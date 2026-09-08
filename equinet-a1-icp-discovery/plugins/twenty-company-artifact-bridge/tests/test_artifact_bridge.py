from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

PLUGIN_PATH = Path(__file__).resolve().parents[1] / "__init__.py"
SPEC = importlib.util.spec_from_file_location("twenty_company_artifact_bridge", PLUGIN_PATH)
assert SPEC and SPEC.loader
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)

COMPANY_ID = "123e4567-e89b-42d3-a456-426614174000"
OTHER_COMPANY_ID = "223e4567-e89b-42d3-a456-426614174000"
PHONE = "+14055553078"


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _fixture(base: Path, *, phone: str | None = PHONE) -> tuple[Path, str]:
    item = base / "runtime/n8n-poll-tickets/ticket-1/staging/item-00"
    payload = {
        "name": "Example Farrier",
        "position": "first",
        "discoveryStatus": "DISCOVERED",
        "discoveryFingerprint": "phone:14055553078",
        "segment": "FARRIER",
        "country": "US",
        "city": "LEXINGTON",
        "state": "KENTUCKY",
    }
    if phone is not None:
        payload["phone"] = {
            "primaryPhoneNumber": phone,
            "additionalPhones": [],
        }
    plan = {
        "schema_version": bridge.PLAN_SCHEMA,
        "company_payload": payload,
        "lookup_plan": {
            "fingerprint": {"mcp_tool": "find_many_companies", "arguments": {}},
            "domain": None,
            "possible_name_location": {
                "mcp_tool": "find_many_companies",
                "arguments": {},
            },
        },
    }
    decision = {
        "schema_version": bridge.DECISION_SCHEMA,
        "action": "create",
        "reason": "no_existing_company_match",
        "company_id": None,
        "mcp_tool": "create_many_companies",
        "mcp_arguments": {"records": [payload]},
    }
    _write_json(item / "plan.json", plan)
    _write_json(item / "decision.json", decision)
    _write_json(
        item / "matches.json",
        {"fingerprint_matches": [], "domain_matches": [], "possible_matches": []},
    )
    raw_empty = {
        "success": True,
        "result": {"records": [], "count": "0", "hasNextPage": False},
    }
    normalized_empty = {
        "schema_version": bridge.MATCH_SCHEMA,
        "records": [],
    }
    _write_json(item / "raw-fingerprint.json", raw_empty)
    _write_json(item / "fingerprint-normalized.json", normalized_empty)
    _write_json(item / "raw-possible_name_location.json", raw_empty)
    _write_json(item / "possible-normalized.json", normalized_empty)
    raw = (item / "decision.json").read_bytes()
    return item / "decision.json", hashlib.sha256(raw).hexdigest()


def _decoded(result: str) -> dict:
    return json.loads(result)


class ArtifactBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.base = Path(self._temp.name)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def test_plugin_registration_has_no_mcp_startup_race_check(self) -> None:
        class Context:
            def __init__(self) -> None:
                self.registration = None

            def register_tool(self, **kwargs: object) -> None:
                self.registration = kwargs

        context = Context()
        bridge.register(context)
        self.assertEqual(context.registration["name"], bridge.TOOL_NAME)
        self.assertNotIn("check_fn", context.registration)

    def test_forwards_unredacted_phone_and_persists_responses(self) -> None:
        decision_path, digest = _fixture(self.base)
        calls: list[tuple[str, dict]] = []

        def dispatch(tool_name: str, arguments: dict, **_: object) -> str:
            calls.append((tool_name, arguments))
            if arguments["toolName"] == "create_many_companies":
                self.assertEqual(
                    arguments["arguments"]["records"][0]["phone"]["primaryPhoneNumber"],
                    PHONE,
                )
                return json.dumps(
                    {
                        "result": json.dumps(
                            {"success": True, "result": [{"id": COMPANY_ID}]}
                        )
                    }
                )
            self.assertEqual(
                arguments,
                {
                    "toolName": "find_one_company",
                    "arguments": {"id": COMPANY_ID, "select": ["*"]},
                },
            )
            return json.dumps(
                {
                    "result": json.dumps(
                        {"success": True, "result": {"id": COMPANY_ID}}
                    )
                }
            )

        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path),
                digest,
                base_dir=self.base,
                dispatch_fn=dispatch,
            )
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["company_id"], COMPANY_ID)
        self.assertNotIn(PHONE, json.dumps(result))
        self.assertEqual(
            [call[1]["toolName"] for call in calls],
            ["create_many_companies", "find_one_company"],
        )
        item = decision_path.parent
        self.assertTrue((item / "raw-create.json").is_file())
        self.assertTrue((item / "raw-readback.json").is_file())
        marker = json.loads(
            (item / "write-attempt.json").read_text(encoding="utf-8")
        )
        self.assertEqual(marker["status"], "readback_persisted")
        self.assertEqual(marker["company_id"], COMPANY_ID)

    def test_dry_run_validates_without_writing_or_dispatching(self) -> None:
        decision_path, digest = _fixture(self.base)

        def fail_dispatch(*_: object, **__: object) -> str:
            self.fail("dry run must not dispatch")

        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path),
                digest,
                dry_run=True,
                base_dir=self.base,
                dispatch_fn=fail_dispatch,
            )
        )
        self.assertTrue(result["validated"])
        self.assertFalse(result["write_attempted"])
        self.assertFalse((decision_path.parent / "write-attempt.json").exists())

    def test_rejects_hash_mismatch_before_dispatch(self) -> None:
        decision_path, _ = _fixture(self.base)
        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path),
                "0" * 64,
                base_dir=self.base,
                dispatch_fn=lambda *_args, **_kwargs: self.fail("must not dispatch"),
            )
        )
        self.assertEqual(result["error_type"], "artifact_validation")
        self.assertIn("SHA-256", result["error"])
        self.assertFalse(result["write_attempted"])

    def test_rejects_masked_phone_in_raw_artifact(self) -> None:
        decision_path, digest = _fixture(self.base, phone="+140****3078")
        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path),
                digest,
                base_dir=self.base,
                dispatch_fn=lambda *_args, **_kwargs: self.fail("must not dispatch"),
            )
        )
        self.assertEqual(result["error_type"], "artifact_validation")
        self.assertIn("unmasked E.164", result["error"])

    def test_rejects_create_when_duplicate_matches_exist(self) -> None:
        decision_path, _ = _fixture(self.base)
        _write_json(
            decision_path.parent / "matches.json",
            {
                "fingerprint_matches": [{"id": COMPANY_ID}],
                "domain_matches": [],
                "possible_matches": [],
            },
        )
        _write_json(
            decision_path.parent / "raw-fingerprint.json",
            {"success": True, "result": {"records": [{"id": COMPANY_ID}]}},
        )
        _write_json(
            decision_path.parent / "fingerprint-normalized.json",
            {
                "schema_version": bridge.MATCH_SCHEMA,
                "records": [{"id": COMPANY_ID}],
            },
        )
        digest = hashlib.sha256(decision_path.read_bytes()).hexdigest()
        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path), digest, base_dir=self.base, dry_run=True
            )
        )
        self.assertEqual(result["error_type"], "artifact_validation")
        self.assertIn("conflicts with non-empty duplicate matches", result["error"])

    def test_rejects_normalized_preflight_that_differs_from_raw(self) -> None:
        decision_path, digest = _fixture(self.base)
        _write_json(
            decision_path.parent / "fingerprint-normalized.json",
            {
                "schema_version": bridge.MATCH_SCHEMA,
                "records": [{"id": COMPANY_ID}],
            },
        )
        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path), digest, base_dir=self.base, dry_run=True
            )
        )
        self.assertEqual(result["error_type"], "artifact_validation")
        self.assertIn("records do not match", result["error"])

    def test_rejects_symlinked_sibling_artifact(self) -> None:
        decision_path, digest = _fixture(self.base)
        plan_path = decision_path.parent / "plan.json"
        external = self.base / "external-plan.json"
        external.write_bytes(plan_path.read_bytes())
        plan_path.unlink()
        plan_path.symlink_to(external)
        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path), digest, base_dir=self.base, dry_run=True
            )
        )
        self.assertEqual(result["error_type"], "artifact_validation")
        self.assertIn("symbolic link", result["error"])

    def test_rejects_symlinked_decision_artifact(self) -> None:
        decision_path, _ = _fixture(self.base)
        real_decision = decision_path.with_name("real-decision.json")
        decision_path.replace(real_decision)
        decision_path.symlink_to(real_decision)
        digest = hashlib.sha256(real_decision.read_bytes()).hexdigest()
        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path), digest, base_dir=self.base, dry_run=True
            )
        )
        self.assertEqual(result["error_type"], "artifact_validation")
        self.assertIn("symbolic link", result["error"])

    def test_rejects_path_outside_runtime_scope(self) -> None:
        decision_path = self.base / "decision.json"
        _write_json(decision_path, {})
        digest = hashlib.sha256(decision_path.read_bytes()).hexdigest()
        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path), digest, base_dir=self.base, dry_run=True
            )
        )
        self.assertEqual(result["error_type"], "artifact_validation")
        self.assertIn("runtime/n8n-poll-tickets", result["error"])

    def test_refuses_retry_after_write_marker(self) -> None:
        decision_path, digest = _fixture(self.base)
        _write_json(decision_path.parent / "write-attempt.json", {"status": "started"})
        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path), digest, base_dir=self.base, dry_run=True
            )
        )
        self.assertEqual(result["error_type"], "artifact_validation")
        self.assertIn("possible duplicate write", result["error"])

    def test_phone_less_company_is_not_batch_blocked(self) -> None:
        decision_path, digest = _fixture(self.base, phone=None)
        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path), digest, base_dir=self.base, dry_run=True
            )
        )
        self.assertTrue(result["success"])
        self.assertTrue(result["validated"])

    def test_missing_write_id_is_uncertain_and_not_retryable(self) -> None:
        decision_path, digest = _fixture(self.base)

        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path),
                digest,
                base_dir=self.base,
                dispatch_fn=lambda *_args, **_kwargs: json.dumps(
                    {"result": json.dumps({"success": True, "result": []})}
                ),
            )
        )

        self.assertEqual(result["error_type"], "twenty_postwrite_validation")
        self.assertTrue(result["write_attempted"])
        self.assertFalse(result["retry_safe"])
        marker = json.loads(
            (decision_path.parent / "write-attempt.json").read_text(encoding="utf-8")
        )
        self.assertEqual(marker["status"], "write_response_persisted")

    def test_transport_exception_is_non_retryable_and_does_not_echo_phone(self) -> None:
        decision_path, digest = _fixture(self.base)

        def dispatch(*_args: object, **_kwargs: object) -> str:
            raise RuntimeError(f"transport failed for {PHONE}")

        result_text = bridge.execute_twenty_company_artifact(
            str(decision_path),
            digest,
            base_dir=self.base,
            dispatch_fn=dispatch,
        )
        result = _decoded(result_text)

        self.assertEqual(result["error_type"], "twenty_artifact_execution")
        self.assertTrue(result["write_attempted"])
        self.assertFalse(result["retry_safe"])
        self.assertNotIn(PHONE, result_text)
        marker = json.loads(
            (decision_path.parent / "write-attempt.json").read_text(encoding="utf-8")
        )
        self.assertEqual(marker["status"], "started")

    def test_update_uses_exact_match_and_preserves_reviewer_status(self) -> None:
        decision_path, _ = _fixture(self.base)
        plan = json.loads(
            (decision_path.parent / "plan.json").read_text(encoding="utf-8")
        )
        update_fields = {
            key: value
            for key, value in plan["company_payload"].items()
            if key not in {"position", "discoveryStatus"}
        }
        decision = {
            "schema_version": bridge.DECISION_SCHEMA,
            "action": "update",
            "reason": "exact_existing_company_match",
            "company_id": COMPANY_ID,
            "mcp_tool": "update_one_company",
            "mcp_arguments": {"id": COMPANY_ID, **update_fields},
        }
        _write_json(decision_path, decision)
        _write_json(
            decision_path.parent / "matches.json",
            {
                "fingerprint_matches": [{"id": COMPANY_ID}],
                "domain_matches": [],
                "possible_matches": [],
            },
        )
        _write_json(
            decision_path.parent / "raw-fingerprint.json",
            {
                "success": True,
                "result": {
                    "records": [{"id": COMPANY_ID}],
                    "count": "1",
                    "hasNextPage": False,
                },
            },
        )
        _write_json(
            decision_path.parent / "fingerprint-normalized.json",
            {
                "schema_version": bridge.MATCH_SCHEMA,
                "records": [{"id": COMPANY_ID}],
            },
        )
        digest = hashlib.sha256(decision_path.read_bytes()).hexdigest()
        calls: list[dict] = []

        def dispatch(_tool_name: str, arguments: dict, **_: object) -> str:
            calls.append(arguments)
            return json.dumps(
                {
                    "result": json.dumps(
                        {"success": True, "result": {"id": COMPANY_ID}}
                    )
                }
            )

        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path),
                digest,
                base_dir=self.base,
                dispatch_fn=dispatch,
            )
        )

        self.assertTrue(result["success"])
        self.assertEqual(calls[0]["toolName"], "update_one_company")
        self.assertNotIn("discoveryStatus", calls[0]["arguments"])
        self.assertNotIn("position", calls[0]["arguments"])

    def test_default_mcp_dispatch_makes_exactly_one_transport_call(self) -> None:
        from tools import mcp_tool

        class AsyncLock:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args: object) -> None:
                return None

        class Session:
            def __init__(self) -> None:
                self.calls = 0

            async def call_tool(self, name: str, arguments: dict):
                self.calls += 1
                self.last_call = (name, arguments)
                return SimpleNamespace(
                    content=[SimpleNamespace(text=json.dumps({"success": True}))],
                    isError=False,
                    structuredContent=None,
                )

        session = Session()
        server = SimpleNamespace(
            session=session,
            _rpc_lock=AsyncLock(),
            tool_timeout=10,
            _tools=[SimpleNamespace(name="execute_tool")],
        )

        def run_once(factory, timeout: float):
            self.assertEqual(timeout, 10)
            return asyncio.run(factory())

        with (
            mock.patch.object(
                bridge.registry,
                "get_entry",
                return_value=SimpleNamespace(toolset="mcp-twenty"),
            ),
            mock.patch.object(
                mcp_tool, "_get_connected_server_for_call", return_value=server
            ),
            mock.patch.object(mcp_tool, "_mark_server_call_started"),
            mock.patch.object(mcp_tool, "_run_on_mcp_loop", side_effect=run_once),
            mock.patch.dict(
                mcp_tool._mcp_tool_server_names,
                {bridge.TWENTY_EXECUTE_TOOL: "twenty"},
            ),
        ):
            result = _decoded(
                bridge._default_dispatch(
                    bridge.TWENTY_EXECUTE_TOOL,
                    {"toolName": "create_many_companies", "arguments": {"records": []}},
                )
            )

        self.assertEqual(session.calls, 1)
        self.assertEqual(session.last_call[0], "execute_tool")
        self.assertFalse(result["isError"])

    def test_rejects_plan_payload_id_override(self) -> None:
        decision_path, _ = _fixture(self.base)
        plan_path = decision_path.parent / "plan.json"
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        plan["company_payload"]["id"] = OTHER_COMPANY_ID
        _write_json(plan_path, plan)
        update_fields = {
            key: value
            for key, value in plan["company_payload"].items()
            if key not in {"position", "discoveryStatus"}
        }
        _write_json(
            decision_path,
            {
                "schema_version": bridge.DECISION_SCHEMA,
                "action": "update",
                "reason": "exact_existing_company_match",
                "company_id": COMPANY_ID,
                "mcp_tool": "update_one_company",
                "mcp_arguments": update_fields,
            },
        )
        _write_json(
            decision_path.parent / "matches.json",
            {
                "fingerprint_matches": [{"id": COMPANY_ID}],
                "domain_matches": [],
                "possible_matches": [],
            },
        )
        _write_json(
            decision_path.parent / "raw-fingerprint.json",
            {"success": True, "result": {"records": [{"id": COMPANY_ID}]}},
        )
        _write_json(
            decision_path.parent / "fingerprint-normalized.json",
            {
                "schema_version": bridge.MATCH_SCHEMA,
                "records": [{"id": COMPANY_ID}],
            },
        )
        digest = hashlib.sha256(decision_path.read_bytes()).hexdigest()
        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path), digest, base_dir=self.base, dry_run=True
            )
        )
        self.assertEqual(result["error_type"], "artifact_validation")
        self.assertIn("must not contain a Company id", result["error"])

    def test_postwrite_output_collision_reports_uncertain_write(self) -> None:
        decision_path, digest = _fixture(self.base)

        def dispatch(*_args: object, **_kwargs: object) -> str:
            _write_json(decision_path.parent / "raw-create.json", {"raced": True})
            return json.dumps(
                {"result": json.dumps({"success": True, "result": [{"id": COMPANY_ID}]})}
            )

        result = _decoded(
            bridge.execute_twenty_company_artifact(
                str(decision_path),
                digest,
                base_dir=self.base,
                dispatch_fn=dispatch,
            )
        )
        self.assertEqual(result["error_type"], "twenty_postwrite_artifact_collision")
        self.assertTrue(result["write_attempted"])
        self.assertFalse(result["retry_safe"])

    def test_company_id_uses_documented_result_location(self) -> None:
        nested = {
            "result": json.dumps(
                {
                    "success": True,
                    "result": {
                        "id": COMPANY_ID,
                        "accountOwner": {"id": OTHER_COMPANY_ID},
                    },
                }
            )
        }
        self.assertEqual(bridge._extract_single_company_id(nested), COMPANY_ID)


if __name__ == "__main__":
    unittest.main()
