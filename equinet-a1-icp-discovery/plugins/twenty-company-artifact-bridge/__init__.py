"""Execute deterministic Twenty Company decisions without exposing raw payloads.

The bridge reads a validated local decision artifact, forwards its exact
``mcp_arguments`` to the configured Twenty MCP server, and persists both the
write response and authoritative read-back before returning a safe summary.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from tools.registry import registry, tool_error

TOOL_NAME = "twenty_company_write_from_artifact"
TOOLSET = "mcp-artifact"
TWENTY_EXECUTE_TOOL = "mcp__twenty__execute_tool"
DECISION_SCHEMA = "a1.twenty-company-staging-decision.v1"
PLAN_SCHEMA = "a1.twenty-company-staging-plan.v1"
MATCH_SCHEMA = "a1.twenty-company-match-set.v1"
_ALLOWED_OPERATIONS = {
    "create": "create_many_companies",
    "update": "update_one_company",
}
_ALLOWED_COMPANY_FIELDS = {
    "id",
    "name",
    "domainName",
    "address",
    "linkedinLink",
    "annualRevenue",
    "position",
    "accountOwnerId",
    "phone",
    "country",
    "city",
    "state",
    "sourceUrl",
    "segment",
    "discoveryStatus",
    "discoverySourceNotes",
    "discoveryFingerprint",
}
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
_MAX_DECISION_BYTES = 256 * 1024


class ArtifactValidationError(ValueError):
    """A fail-closed validation failure before a remote write."""


def _json_error(message: str, **details: Any) -> str:
    return tool_error(message, error_type="artifact_validation", **details)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_json_object(
    path: Path, *, max_bytes: int = _MAX_DECISION_BYTES
) -> tuple[dict[str, Any], bytes]:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ArtifactValidationError(f"Cannot stat artifact: {exc}") from exc
    if size <= 0 or size > max_bytes:
        raise ArtifactValidationError(
            f"Artifact size must be between 1 and {max_bytes} bytes"
        )
    try:
        raw = path.read_bytes()
        value = json.loads(
            raw.decode("utf-8"),
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"Non-finite JSON number {token!r} is not allowed")
            ),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ArtifactValidationError(f"Artifact is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ArtifactValidationError("Artifact must contain one JSON object")
    return value, raw


def _resolve_local_decision_path(
    decision_path: str,
    task_id: str,
    base_dir: Path | None = None,
) -> tuple[Path, Path]:
    if not isinstance(decision_path, str) or not decision_path.strip():
        raise ArtifactValidationError("decision_path must be a non-empty string")
    if "\x00" in decision_path:
        raise ArtifactValidationError("decision_path contains a NUL byte")

    if base_dir is None:
        from tools.file_tools import _resolve_base_dir, _resolve_path_for_task

        resolved_base = _resolve_base_dir(task_id)
        resolved = _resolve_path_for_task(decision_path, task_id)
        if not isinstance(resolved_base, Path) or not isinstance(resolved, Path):
            raise ArtifactValidationError(
                "Artifact execution is supported only for the local filesystem backend"
            )
        base = resolved_base.resolve()
        unresolved = Path(resolved)
    else:
        base = Path(base_dir).expanduser().resolve()
        candidate = Path(decision_path).expanduser()
        unresolved = candidate if candidate.is_absolute() else base / candidate

    if unresolved.is_symlink():
        raise ArtifactValidationError("decision_path must not be a symbolic link")
    path = unresolved.resolve()

    try:
        relative = path.relative_to(base)
    except ValueError as exc:
        raise ArtifactValidationError(
            "decision_path must remain inside the active task working directory"
        ) from exc

    parts = relative.parts
    if (
        len(parts) != 6
        or parts[0:2] != ("runtime", "n8n-poll-tickets")
        or parts[3] != "staging"
        or not parts[2]
        or not parts[4].startswith("item-")
    ):
        raise ArtifactValidationError(
            "decision_path must match runtime/n8n-poll-tickets/<ticket>/staging/item-*/decision.json"
        )
    if path.name != "decision.json":
        raise ArtifactValidationError(
            "decision_path must name a staging item decision.json artifact"
        )
    if not path.is_file():
        raise ArtifactValidationError("decision_path does not identify a regular file")
    return base, path


def _validate_phone(record: dict[str, Any]) -> None:
    phone = record.get("phone")
    if phone is None:
        return
    if not isinstance(phone, dict):
        raise ArtifactValidationError("Company phone must be an object")
    if set(phone) - {
        "primaryPhoneNumber",
        "primaryPhoneCountryCode",
        "primaryPhoneCallingCode",
        "additionalPhones",
    }:
        raise ArtifactValidationError("Company phone contains unsupported fields")
    value = phone.get("primaryPhoneNumber")
    if not isinstance(value, str) or not _E164_RE.fullmatch(value):
        raise ArtifactValidationError("Company phone must contain one unmasked E.164 value")
    if phone.get("additionalPhones", []) != []:
        raise ArtifactValidationError("Company additionalPhones must be an empty array")


def _validate_company_record(record: Any, *, require_name: bool) -> None:
    if not isinstance(record, dict):
        raise ArtifactValidationError("Company write payload must be an object")
    unknown = set(record) - _ALLOWED_COMPANY_FIELDS
    if unknown:
        raise ArtifactValidationError(
            "Company payload contains unsupported fields: " + ", ".join(sorted(unknown))
        )
    if require_name and (
        not isinstance(record.get("name"), str) or not record["name"].strip()
    ):
        raise ArtifactValidationError("Company create payload requires a non-empty name")
    if record.get("discoveryStatus") not in {
        None,
        "DISCOVERED",
        "HELD",
        "ELIGIBLE",
        "REJECTED",
    }:
        raise ArtifactValidationError("Company discoveryStatus is unsupported")
    _validate_phone(record)


def _safe_sibling(item_dir: Path, name: str) -> Path:
    candidate = item_dir / name
    if candidate.is_symlink():
        raise ArtifactValidationError(
            f"Preflight artifact {name} must not be a symbolic link"
        )
    resolved = candidate.resolve()
    if resolved.parent != item_dir.resolve() or not resolved.is_file():
        raise ArtifactValidationError(f"Missing or unsafe preflight artifact: {name}")
    return resolved


def _records_from_raw_response(
    value: dict[str, Any], label: str
) -> list[dict[str, Any]]:
    if _response_error(value):
        raise ArtifactValidationError(f"{label} records an MCP error")
    candidates: list[list[dict[str, Any]]] = []
    for node in _walk_decoded(value):
        if not isinstance(node, dict) or "records" not in node:
            continue
        records = node.get("records")
        if isinstance(records, list) and all(isinstance(item, dict) for item in records):
            candidates.append(records)
    if not candidates:
        raise ArtifactValidationError(f"{label} does not contain a records array")
    canonical = {_canonical_json(records) for records in candidates}
    if len(canonical) != 1:
        raise ArtifactValidationError(f"{label} contains conflicting records arrays")
    return candidates[0]


def _validate_preflight_artifacts(
    item_dir: Path,
    plan: dict[str, Any],
    matches: dict[str, Any],
) -> None:
    lookups = [
        (
            "fingerprint",
            "raw-fingerprint.json",
            "fingerprint-normalized.json",
            "fingerprint_matches",
        ),
        (
            "possible_name_location",
            "raw-possible_name_location.json",
            "possible-normalized.json",
            "possible_matches",
        ),
    ]
    lookup_plan = plan.get("lookup_plan")
    if not isinstance(lookup_plan, dict):
        raise ArtifactValidationError("Sibling plan requires lookup_plan")
    if lookup_plan.get("domain") is not None:
        lookups.append(
            ("domain", "raw-domain.json", "domain-normalized.json", "domain_matches")
        )
    elif matches.get("domain_matches") != []:
        raise ArtifactValidationError(
            "matches.json has domain matches without a domain lookup"
        )

    for lookup_name, raw_name, normalized_name, matches_key in lookups:
        raw, _ = _load_json_object(_safe_sibling(item_dir, raw_name))
        normalized, _ = _load_json_object(
            _safe_sibling(item_dir, normalized_name)
        )
        if normalized.get("schema_version") != MATCH_SCHEMA:
            raise ArtifactValidationError(
                f"{normalized_name} must use schema_version {MATCH_SCHEMA}"
            )
        normalized_records = normalized.get("records")
        if not isinstance(normalized_records, list) or not all(
            isinstance(item, dict) for item in normalized_records
        ):
            raise ArtifactValidationError(
                f"{normalized_name} requires an object records array"
            )
        raw_records = _records_from_raw_response(raw, raw_name)
        if raw_records != normalized_records:
            raise ArtifactValidationError(
                f"{raw_name} and {normalized_name} records do not match"
            )
        if matches.get(matches_key) != normalized_records:
            raise ArtifactValidationError(
                f"matches.json {matches_key} does not match {lookup_name} lookup evidence"
            )


def _validate_decision(
    decision: dict[str, Any],
    plan: dict[str, Any],
    matches: dict[str, Any],
) -> tuple[str, str, dict[str, Any]]:
    if decision.get("schema_version") != DECISION_SCHEMA:
        raise ArtifactValidationError(f"Expected schema_version {DECISION_SCHEMA}")
    if plan.get("schema_version") != PLAN_SCHEMA:
        raise ArtifactValidationError(f"Expected sibling plan schema_version {PLAN_SCHEMA}")

    action = decision.get("action")
    expected_tool = _ALLOWED_OPERATIONS.get(action)
    if expected_tool is None:
        raise ArtifactValidationError("Only deterministic create/update decisions may execute")
    if decision.get("mcp_tool") != expected_tool:
        raise ArtifactValidationError(
            f"Decision action {action!r} must use {expected_tool!r}"
        )
    arguments = decision.get("mcp_arguments")
    if not isinstance(arguments, dict):
        raise ArtifactValidationError("Decision mcp_arguments must be an object")

    payload = plan.get("company_payload")
    if not isinstance(payload, dict):
        raise ArtifactValidationError("Sibling plan requires company_payload")
    if "id" in payload:
        raise ArtifactValidationError("plan.company_payload must not contain a Company id")
    if decision.get("reason") not in {
        "no_existing_company_match",
        "exact_existing_company_match",
    }:
        raise ArtifactValidationError("Decision reason is not a supported deterministic outcome")

    match_sets: dict[str, list[dict[str, Any]]] = {}
    for key in ("fingerprint_matches", "domain_matches", "possible_matches"):
        value = matches.get(key)
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise ArtifactValidationError(f"matches.json requires an object array at {key}")
        match_sets[key] = value

    if action == "create":
        if decision.get("reason") != "no_existing_company_match":
            raise ArtifactValidationError(
                "Create decision reason must be no_existing_company_match"
            )
        records = arguments.get("records")
        if set(arguments) != {"records"} or not isinstance(records, list) or len(records) != 1:
            raise ArtifactValidationError("Company create must contain exactly one records item")
        if records[0] != payload:
            raise ArtifactValidationError("Create arguments do not exactly match plan.company_payload")
        if any(match_sets.values()):
            raise ArtifactValidationError("Create decision conflicts with non-empty duplicate matches")
        _validate_company_record(records[0], require_name=True)
    else:
        if decision.get("reason") != "exact_existing_company_match":
            raise ArtifactValidationError(
                "Update decision reason must be exact_existing_company_match"
            )
        company_id = decision.get("company_id")
        if not isinstance(company_id, str) or not _UUID_RE.fullmatch(company_id):
            raise ArtifactValidationError("Company update decision requires a valid company_id")
        expected = {
            **{
                key: value
                for key, value in payload.items()
                if key not in {"position", "discoveryStatus"}
            },
            "id": company_id,
        }
        if arguments != expected:
            raise ArtifactValidationError(
                "Update arguments do not exactly match the reviewer-status-preserving plan"
            )
        fingerprint_matches = match_sets["fingerprint_matches"]
        domain_matches = match_sets["domain_matches"]
        if len(fingerprint_matches) > 1 or len(domain_matches) > 1:
            raise ArtifactValidationError(
                "Update decision has ambiguous exact duplicate matches"
            )
        expected_match = (
            fingerprint_matches[0]
            if len(fingerprint_matches) == 1
            else domain_matches[0]
            if len(domain_matches) == 1
            else None
        )
        if not isinstance(expected_match, dict) or expected_match.get("id") != company_id:
            raise ArtifactValidationError(
                "Update company_id is not the deterministic exact duplicate match"
            )
        _validate_company_record(arguments, require_name=False)

    return action, expected_tool, arguments


def _decode_json_string(value: Any) -> Any:
    current = value
    for _ in range(4):
        if not isinstance(current, str):
            break
        try:
            current = json.loads(current)
        except json.JSONDecodeError:
            break
    return current


def _walk_decoded(value: Any):
    value = _decode_json_string(value)
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_decoded(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_decoded(child)


def _response_error(value: Any) -> str | None:
    for node in _walk_decoded(value):
        if not isinstance(node, dict):
            continue
        if node.get("success") is False:
            return str(node.get("error") or node.get("message") or "MCP operation failed")
        error = node.get("error")
        if error:
            if isinstance(error, dict):
                return str(error.get("message") or error)
            return str(error)
    return None


def _primary_response_payload(value: Any) -> Any:
    root = _decode_json_string(value)
    if not isinstance(root, dict):
        raise ArtifactValidationError("MCP response envelope must be an object")
    if root.get("structuredContent") is not None:
        payload = _decode_json_string(root["structuredContent"])
    else:
        payload = _decode_json_string(root.get("result"))
    if isinstance(payload, dict) and payload.get("structuredContent") is not None:
        payload = _decode_json_string(payload["structuredContent"])
    if isinstance(payload, dict) and "result" in payload:
        payload = _decode_json_string(payload["result"])
    return payload


def _extract_single_company_id(value: Any) -> str:
    payload = _primary_response_payload(value)
    if isinstance(payload, dict) and isinstance(payload.get("record"), dict):
        payload = payload["record"]
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        payload = payload["records"]
    if isinstance(payload, list):
        if len(payload) != 1 or not isinstance(payload[0], dict):
            raise ArtifactValidationError(
                "MCP response must contain exactly one Company record"
            )
        payload = payload[0]
    company_id = payload.get("id") if isinstance(payload, dict) else None
    if not isinstance(company_id, str) or not _UUID_RE.fullmatch(company_id):
        raise ArtifactValidationError(
            "MCP response does not contain a Company UUID at the documented result location"
        )
    return company_id


def _fsync_parent(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    directory_fd = os.open(path.parent, flags)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def _atomic_create(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        _fsync_parent(path)
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def _atomic_replace_json(path: Path, value: dict[str, Any]) -> None:
    rendered = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    temp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
        _fsync_parent(path)
    except BaseException:
        try:
            temp.unlink()
        except OSError:
            pass
        raise


def _default_dispatch(tool_name: str, arguments: dict[str, Any], **_kwargs: Any) -> Any:
    """Call Twenty MCP exactly once, without the generic MCP retry wrapper.

    The normal MCP handler retries once after selected authentication/session
    failures. That is useful for reads but unsafe for creates: the server may
    have committed a Company before the client lost the response. The artifact
    bridge therefore uses the already-connected MCP session directly and leaves
    its exclusive write-attempt marker behind on every transport exception.
    """
    if tool_name != TWENTY_EXECUTE_TOOL:
        raise ArtifactValidationError("Artifact bridge may call only Twenty execute_tool")

    from tools import mcp_tool

    entry = registry.get_entry(TWENTY_EXECUTE_TOOL)
    if entry is None or entry.toolset != "mcp-twenty":
        raise RuntimeError("Registered Twenty execute tool provenance is unavailable")
    with mcp_tool._lock:
        registered_server = mcp_tool._mcp_tool_server_names.get(TWENTY_EXECUTE_TOOL)
    if registered_server != "twenty":
        raise RuntimeError("Registered Twenty execute tool is not owned by the twenty MCP server")

    server = mcp_tool._get_connected_server_for_call("twenty")
    if server is None or server.session is None:
        raise RuntimeError("Twenty MCP server is not connected")
    if not any(getattr(item, "name", None) == "execute_tool" for item in server._tools):
        raise RuntimeError("Twenty MCP server no longer advertises execute_tool")

    async def _call_once() -> str:
        mcp_tool._mark_server_call_started(server)
        async with server._rpc_lock:
            result = await server.session.call_tool("execute_tool", arguments=arguments)

        parts: list[str] = []
        for block in result.content or []:
            text = getattr(block, "text", None)
            if text:
                parts.append(str(text))
        text_result = "\n".join(parts)
        structured = getattr(result, "structuredContent", None)
        envelope: dict[str, Any] = {
            "result": text_result,
            "isError": bool(getattr(result, "isError", False)),
        }
        if structured is not None:
            envelope["structuredContent"] = structured
        if envelope["isError"]:
            envelope["error"] = text_result or "Twenty MCP tool returned an error"
        return json.dumps(envelope, ensure_ascii=False)

    return mcp_tool._run_on_mcp_loop(_call_once, timeout=server.tool_timeout)


def execute_twenty_company_artifact(
    decision_path: str,
    expected_sha256: str,
    *,
    dry_run: bool = False,
    task_id: str = "default",
    session_id: str | None = None,
    user_task: str | None = None,
    base_dir: Path | None = None,
    dispatch_fn: Callable[..., Any] | None = None,
) -> str:
    """Validate and execute one persisted Twenty Company decision."""
    marker_path: Path | None = None
    write_started = False
    try:
        if not isinstance(expected_sha256, str) or not _SHA256_RE.fullmatch(expected_sha256):
            raise ArtifactValidationError("expected_sha256 must be 64 hexadecimal characters")
        _, path = _resolve_local_decision_path(decision_path, task_id, base_dir)
        decision, decision_raw = _load_json_object(path)
        actual_sha256 = _sha256_bytes(decision_raw)
        if not hmac.compare_digest(actual_sha256.lower(), expected_sha256.lower()):
            raise ArtifactValidationError("Decision artifact SHA-256 does not match expected_sha256")

        plan_path = _safe_sibling(path.parent, "plan.json")
        plan, _ = _load_json_object(plan_path)
        matches_path = _safe_sibling(path.parent, "matches.json")
        matches, _ = _load_json_object(matches_path)
        _validate_preflight_artifacts(path.parent, plan, matches)
        action, target_tool, arguments = _validate_decision(decision, plan, matches)

        marker_path = path.with_name("write-attempt.json")
        raw_write_path = path.with_name("raw-create.json" if action == "create" else "raw-update.json")
        raw_readback_path = path.with_name("raw-readback.json")
        if marker_path.exists() or raw_write_path.exists() or raw_readback_path.exists():
            raise ArtifactValidationError(
                "A write-attempt or response artifact already exists; refusing a possible duplicate write"
            )

        if dry_run:
            return json.dumps(
                {
                    "success": True,
                    "dry_run": True,
                    "validated": True,
                    "operation": action,
                    "target_tool": target_tool,
                    "decision_sha256": actual_sha256,
                    "decision_path": str(path),
                    "write_attempted": False,
                },
                ensure_ascii=False,
            )

        dispatcher = dispatch_fn or _default_dispatch
        if dispatch_fn is None and registry.get_entry(TWENTY_EXECUTE_TOOL) is None:
            raise ArtifactValidationError(
                f"Required Twenty MCP bridge tool {TWENTY_EXECUTE_TOOL!r} is not registered"
            )

        marker = {
            "schema_version": "hermes.twenty-company-write-attempt.v1",
            "status": "started",
            "decision_path": str(path),
            "decision_sha256": actual_sha256,
            "operation": action,
            "target_tool": target_tool,
            "started_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        _atomic_create(
            marker_path,
            (json.dumps(marker, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        )
        write_started = True

        response = dispatcher(
            TWENTY_EXECUTE_TOOL,
            {"toolName": target_tool, "arguments": arguments},
            task_id=task_id,
            session_id=session_id,
            user_task=user_task,
        )
        response_bytes = response.encode("utf-8") if isinstance(response, str) else _canonical_json(response).encode("utf-8")
        _atomic_create(raw_write_path, response_bytes)
        marker.update(
            {
                "status": "write_response_persisted",
                "write_response_path": str(raw_write_path),
                "write_response_sha256": _sha256_bytes(response_bytes),
            }
        )
        _atomic_replace_json(marker_path, marker)

        response_error = _response_error(response)
        if response_error:
            marker["status"] = "write_failed_or_uncertain"
            marker["error"] = response_error
            _atomic_replace_json(marker_path, marker)
            return tool_error(
                "Twenty write returned an error; the response was persisted and automatic retry is blocked",
                error_type="twenty_write_error",
                operation=action,
                decision_path=str(path),
                write_response_path=str(raw_write_path),
                write_attempted=True,
                retry_safe=False,
            )

        company_id = _extract_single_company_id(response)
        readback = dispatcher(
            TWENTY_EXECUTE_TOOL,
            {"toolName": "find_one_company", "arguments": {"id": company_id, "select": ["*"]}},
            task_id=task_id,
            session_id=session_id,
            user_task=user_task,
        )
        readback_bytes = readback.encode("utf-8") if isinstance(readback, str) else _canonical_json(readback).encode("utf-8")
        _atomic_create(raw_readback_path, readback_bytes)
        marker.update(
            {
                "status": "readback_response_persisted",
                "company_id": company_id,
                "readback_response_path": str(raw_readback_path),
                "readback_response_sha256": _sha256_bytes(readback_bytes),
            }
        )
        _atomic_replace_json(marker_path, marker)
        readback_error = _response_error(readback)
        if readback_error:
            marker.update(
                {
                    "status": "readback_failed",
                    "company_id": company_id,
                    "readback_response_path": str(raw_readback_path),
                    "readback_response_sha256": _sha256_bytes(readback_bytes),
                    "error": readback_error,
                }
            )
            _atomic_replace_json(marker_path, marker)
            return tool_error(
                "Twenty write returned a Company ID but read-back failed; automatic retry is blocked",
                error_type="twenty_readback_error",
                operation=action,
                company_id=company_id,
                write_response_path=str(raw_write_path),
                readback_response_path=str(raw_readback_path),
                write_attempted=True,
                retry_safe=False,
            )

        readback_id = _extract_single_company_id(readback)
        if readback_id != company_id:
            raise ArtifactValidationError("Twenty read-back Company ID does not match write response")

        marker.update(
            {
                "status": "readback_persisted",
                "company_id": company_id,
                "readback_response_path": str(raw_readback_path),
                "readback_response_sha256": _sha256_bytes(readback_bytes),
                "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            }
        )
        _atomic_replace_json(marker_path, marker)
        return json.dumps(
            {
                "success": True,
                "operation": action,
                "company_id": company_id,
                "decision_sha256": actual_sha256,
                "write_attempted": True,
                "write_response_path": str(raw_write_path),
                "readback_response_path": str(raw_readback_path),
                "marker_path": str(marker_path),
                "retry_safe": False,
            },
            ensure_ascii=False,
        )
    except ArtifactValidationError as exc:
        if write_started:
            return tool_error(
                f"Twenty write was attempted but post-write validation failed: {exc}",
                error_type="twenty_postwrite_validation",
                decision_path=decision_path,
                write_attempted=True,
                retry_safe=False,
            )
        return _json_error(str(exc), decision_path=decision_path, write_attempted=False)
    except FileExistsError:
        if write_started:
            return tool_error(
                "An output artifact collision occurred after the Twenty write began; automatic retry is blocked",
                error_type="twenty_postwrite_artifact_collision",
                decision_path=decision_path,
                write_attempted=True,
                retry_safe=False,
            )
        return _json_error(
            "A write-attempt artifact appeared concurrently; refusing a possible duplicate write",
            decision_path=decision_path,
            write_attempted=False,
        )
    except Exception as exc:
        return tool_error(
            f"Twenty artifact execution failed with {type(exc).__name__}; inspect the write-attempt marker before any recovery",
            error_type="twenty_artifact_execution",
            decision_path=decision_path,
            write_attempted=write_started,
            retry_safe=False,
        )


TWENTY_COMPANY_ARTIFACT_SCHEMA = {
    "name": TOOL_NAME,
    "description": (
        "Execute one validated Twenty Company create/update decision directly from a local "
        "staging artifact without exposing raw E.164 phone values to model context. The tool "
        "is side-effecting unless dry_run=true, persists write/read-back responses, and refuses "
        "retries when a write-attempt marker exists."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "decision_path": {
                "type": "string",
                "description": (
                    "Path to an immutable decision.json below "
                    "runtime/n8n-poll-tickets/<ticket>/.../staging."
                ),
            },
            "expected_sha256": {
                "type": "string",
                "description": "SHA-256 of the exact decision.json bytes.",
                "pattern": "^[0-9a-fA-F]{64}$",
            },
            "dry_run": {
                "type": "boolean",
                "default": False,
                "description": "Validate only; do not call Twenty or create write-attempt artifacts.",
            },
        },
        "required": ["decision_path", "expected_sha256"],
        "additionalProperties": False,
    },
}


def _handle(args: dict[str, Any], **kwargs: Any) -> str:
    return execute_twenty_company_artifact(
        decision_path=args.get("decision_path", ""),
        expected_sha256=args.get("expected_sha256", ""),
        dry_run=bool(args.get("dry_run", False)),
        task_id=kwargs.get("task_id") or "default",
        session_id=kwargs.get("session_id"),
        user_task=kwargs.get("user_task"),
    )


def register(ctx) -> None:
    """Register the profile-scoped artifact bridge with Hermes."""
    ctx.register_tool(
        name=TOOL_NAME,
        toolset=TOOLSET,
        schema=TWENTY_COMPANY_ARTIFACT_SCHEMA,
        handler=_handle,
        description=TWENTY_COMPANY_ARTIFACT_SCHEMA["description"],
        emoji="🏢",
    )
