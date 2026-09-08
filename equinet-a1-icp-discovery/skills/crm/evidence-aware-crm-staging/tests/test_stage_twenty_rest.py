from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "stage_twenty_rest.py"
FIXTURE = Path(
    "/opt/data/profiles/equinet-a1-icp-discovery/runtime/"
    "n8n-discovery-results/equinet-1151-20260901T195623Z/discovery-result.json"
)
PEOPLE_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "discovery-with-persons.json"


def load_module():
    spec = importlib.util.spec_from_file_location("stage_twenty_rest", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def nested_value(record, parts):
    value = record
    for part in parts:
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def matches_filter(record, expression):
    if not expression:
        return True
    if "and" in expression:
        return all(matches_filter(record, item) for item in expression["and"])
    if "or" in expression:
        return any(matches_filter(record, item) for item in expression["or"])
    for key, condition in expression.items():
        if isinstance(condition, dict) and "eq" in condition:
            if nested_value(record, [key]) != condition["eq"]:
                return False
        elif isinstance(condition, dict) and "is" in condition:
            actual = nested_value(record, [key])
            if condition["is"] == "NOT_NULL" and actual is None:
                return False
            if condition["is"] == "NULL" and actual is not None:
                return False
        elif isinstance(condition, dict):
            for child, child_condition in condition.items():
                if not isinstance(child_condition, dict) or "eq" not in child_condition:
                    return False
                if nested_value(record, [key, child]) != child_condition["eq"]:
                    return False
        else:
            return False
    return True


def parse_rest_filter(value):
    left, separator, expected = value.partition(":")
    if not separator:
        raise ValueError("missing REST filter separator")
    match = re.fullmatch(r"(.+)\[([a-zA-Z]+)\]", left)
    if not match or match.group(2) not in {"eq", "is"}:
        raise ValueError("unsupported REST filter")
    try:
        expected = json.loads(expected)
    except json.JSONDecodeError:
        pass
    condition = {match.group(2): expected}
    for part in reversed(match.group(1).split(".")):
        condition = {part: condition}
    return condition


class MockTwenty:
    def __init__(self):
        self.records = {}
        self.people = {}
        self.next_id = 1
        self.next_person_id = 1
        self.create_calls = 0
        self.update_calls = 0
        self.person_create_calls = 0
        self.person_update_calls = 0
        self.fail_person_create = False
        self.paths = []
        self.auth_headers = []

    def handler(self):
        state = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                return

            def send_json(self, status, value):
                payload = json.dumps(value).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def body(self):
                length = int(self.headers.get("Content-Length", "0"))
                return json.loads(self.rfile.read(length) or b"{}")

            def record_request(self):
                state.paths.append(self.path)
                state.auth_headers.append(self.headers.get("Authorization"))

            def do_GET(self):
                self.record_request()
                parsed = urllib.parse.urlsplit(self.path)
                if parsed.path == "/rest/companies":
                    query = urllib.parse.parse_qs(parsed.query)
                    filter_value = parse_rest_filter(query.get("filter", [""])[0])
                    limit = int(query.get("limit", ["10"])[0])
                    rows = [record for record in state.records.values() if matches_filter(record, filter_value)]
                    self.send_json(200, {"data": rows[:limit]})
                    return
                if parsed.path == "/rest/people":
                    query = urllib.parse.parse_qs(parsed.query)
                    raw_filter = query.get("filter", [""])[0]
                    parts = [parse_rest_filter(part) for part in raw_filter.split(",") if part]
                    rows = [
                        record for record in state.people.values()
                        if all(matches_filter(record, part) for part in parts)
                    ]
                    self.send_json(200, {"data": rows})
                    return
                company_prefix = "/rest/companies/"
                if parsed.path.startswith(company_prefix):
                    company_id = urllib.parse.unquote(parsed.path[len(company_prefix):])
                    record = state.records.get(company_id)
                    if record is None:
                        self.send_json(404, {"message": "not found"})
                    else:
                        self.send_json(200, {"data": record})
                    return
                people_prefix = "/rest/people/"
                if parsed.path.startswith(people_prefix):
                    person_id = urllib.parse.unquote(parsed.path[len(people_prefix):])
                    record = state.people.get(person_id)
                    if record is None:
                        self.send_json(404, {"message": "not found"})
                    else:
                        self.send_json(200, {"data": record})
                    return
                self.send_json(404, {"message": "unknown path"})

            def do_POST(self):
                self.record_request()
                request_path = urllib.parse.urlsplit(self.path).path
                if request_path == "/rest/people":
                    if state.fail_person_create:
                        self.send_json(503, {"message": "simulated Person failure"})
                        return
                    payload = self.body()
                    person_id = f"person-{state.next_person_id}"
                    state.next_person_id += 1
                    state.person_create_calls += 1
                    state.people[person_id] = {"id": person_id, **payload}
                    self.send_json(201, {"data": {"id": person_id}})
                    return
                if request_path != "/rest/companies":
                    self.send_json(404, {"message": "unknown path"})
                    return
                payload = self.body()
                if "position" in payload:
                    self.send_json(400, {"message": "position is not a Company field"})
                    return
                company_id = f"company-{state.next_id}"
                state.next_id += 1
                state.create_calls += 1
                state.records[company_id] = {"id": company_id, **payload}
                self.send_json(201, {"data": {"id": company_id}})

            def do_PATCH(self):
                self.record_request()
                company_prefix = "/rest/companies/"
                people_prefix = "/rest/people/"
                parsed = urllib.parse.urlsplit(self.path)
                if parsed.path.startswith(people_prefix):
                    person_id = urllib.parse.unquote(parsed.path[len(people_prefix):])
                    if person_id not in state.people:
                        self.send_json(404, {"message": "not found"})
                        return
                    state.people[person_id].update(self.body())
                    state.person_update_calls += 1
                    self.send_json(200, {"data": {"id": person_id}})
                    return
                if not parsed.path.startswith(company_prefix):
                    self.send_json(404, {"message": "unknown path"})
                    return
                company_id = urllib.parse.unquote(parsed.path[len(company_prefix):])
                if company_id not in state.records:
                    self.send_json(404, {"message": "not found"})
                    return
                payload = self.body()
                state.update_calls += 1
                original_status = state.records[company_id].get("discoveryStatus")
                state.records[company_id].update(payload)
                if "discoveryStatus" not in payload and original_status is not None:
                    state.records[company_id]["discoveryStatus"] = original_status
                self.send_json(200, {"data": {"id": company_id}})

        return Handler


class StageTwentyRestTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        source = json.loads(FIXTURE.read_text())
        source["leads"] = source["leads"][:2]
        source["summary"]["returned"] = 2
        self.source = source
        self.mock = MockTwenty()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.mock.handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def run_once(self, root, name, overlays=None):
        input_path = Path(root) / f"{name}-input.json"
        output_dir = Path(root) / f"{name}-output"
        input_path.write_text(json.dumps(self.source))
        overlays_path = None
        if overlays is not None:
            overlays_path = Path(root) / f"{name}-overlays.json"
            overlays_path.write_text(json.dumps(overlays))
        args = SimpleNamespace(
            input=input_path,
            overlays=overlays_path,
            field_manifest=self.module.DEFAULT_FIELD_MANIFEST,
            output_dir=output_dir,
            base_url=f"http://127.0.0.1:{self.server.server_port}",
            api_key="test-key",
            timeout=5.0,
            request_delay=0.0,
            max_records=200,
        )
        return self.module.run(args), output_dir

    def test_scored_overlay_is_written_and_reconciled(self):
        self.source["leads"] = self.source["leads"][:1]
        self.source["summary"]["returned"] = 1
        self.source["leads"][0]["email"] = "contact@example.com"
        fingerprint = self.source["leads"][0]["lead_fingerprint"]
        overlays = {
            "schema_version": self.module.helper.OVERLAYS_SCHEMA,
            "run_id": self.source["run_id"],
            "source_sha256": self.module.helper.sha256_json(self.source),
            "overlays": [{
                "schema_version": self.module.helper.OVERLAY_SCHEMA,
                "lead_fingerprint": fingerprint,
                "website_status": "verified",
                "enrichment_status": "completed",
                "official_website_url": "https://official.example",
                "qualification_status": "ELIGIBLE",
                "icp_score_status": "SCORED",
                "icp_score": 75,
                "icp_band": "HIGH",
                "icp_outcome": "high_priority_farrier",
                "evidence_confidence_score": 82,
                "evidence_confidence_level": "HIGH",
                "notes": {"scoring_model_version": "1.0.0"},
            }],
        }
        with tempfile.TemporaryDirectory() as root:
            summary, output_dir = self.run_once(root, "scored", overlays)
            self.assertEqual(summary["counts"], {"company_staged_no_person_required": 1})
            record = next(iter(self.mock.records.values()))
            self.assertEqual(record["qualificationStatus"], "ELIGIBLE")
            self.assertEqual(record["icpScoreStatus"], "SCORED")
            self.assertEqual(record["icpScore"], 75)
            self.assertEqual(record["icpBand"], "HIGH")
            self.assertEqual(record["icpOutcome"], "high_priority_farrier")
            self.assertEqual(record["evidenceConfidenceScore"], 82)
            self.assertEqual(record["evidenceConfidenceLevel"], "HIGH")
            self.assertEqual(record["domainName"]["primaryLinkUrl"], "https://official.example")
            self.assertEqual(record["email"], {"primaryEmail": "contact@example.com", "additionalEmails": []})
            self.assertTrue((output_dir / "staging-index.json").exists())

    def test_real_fixture_creates_then_updates_without_duplicates(self):
        with tempfile.TemporaryDirectory() as root:
            first, first_dir = self.run_once(root, "first")
            self.assertTrue(first["complete"])
            self.assertEqual(first["total"], 2)
            self.assertEqual(first["counts"], {"company_staged_no_person_required": 2})
            self.assertFalse(first["lead_rows_emitted"])
            self.assertEqual(self.mock.create_calls, 2)
            self.assertEqual(self.mock.update_calls, 0)
            self.assertEqual(len(self.mock.records), 2)

            second, second_dir = self.run_once(root, "second")
            self.assertEqual(second["counts"], {"company_staged_no_person_required": 2})
            self.assertEqual(self.mock.create_calls, 2)
            self.assertEqual(self.mock.update_calls, 2)
            self.assertEqual(len(self.mock.records), 2)

            first_index = json.loads((first_dir / "staging-index.json").read_text())
            second_index = json.loads((second_dir / "staging-index.json").read_text())
            self.assertTrue(first_index["complete"])
            self.assertTrue(second_index["complete"])
            self.assertTrue(all(item["write_attempted"] for item in first_index["dispositions"]))
            self.assertTrue(all(item["operation"] == "update" for item in second_index["dispositions"]))

        self.assertTrue(all(value == "Bearer test-key" for value in self.mock.auth_headers))
        self.assertTrue(all("/people" not in path for path in self.mock.paths))
        self.assertTrue(all("/opportunities" not in path for path in self.mock.paths))

    def test_suffix_bearing_name_filter_is_quoted(self):
        rendered = self.module.rest_filter_expression({"name": {"eq": "J. T. Holub, APF"}})
        self.assertEqual(rendered, 'name[eq]:"J. T. Holub, APF"')

    def test_manifest_drift_fails_before_any_http_request(self):
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            input_path = root_path / "input.json"
            input_path.write_text(json.dumps(self.source))
            manifest = json.loads(self.module.DEFAULT_FIELD_MANIFEST.read_text())
            manifest["fields"]["icpScore"]["decimals"] = 2
            manifest_path = root_path / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))
            args = SimpleNamespace(
                input=input_path, overlays=None, field_manifest=manifest_path,
                output_dir=root_path / "output",
                base_url=f"http://127.0.0.1:{self.server.server_port}",
                api_key="test-key", timeout=5.0, request_delay=0.0, max_records=200,
            )
            with self.assertRaisesRegex(ValueError, "precision mismatch"):
                self.module.run(args)
            self.assertEqual(self.mock.paths, [])

    def test_soft_deleted_exact_match_is_held_without_write(self):
        self.source["leads"] = self.source["leads"][:1]
        self.source["summary"]["returned"] = 1
        with tempfile.TemporaryDirectory() as root:
            first, _ = self.run_once(root, "create")
            self.assertEqual(first["counts"], {"company_staged_no_person_required": 1})
            company_id = next(iter(self.mock.records))
            self.mock.records[company_id]["deletedAt"] = "2026-09-01T00:00:00.000Z"

            second, second_dir = self.run_once(root, "soft-deleted")
            self.assertEqual(second["counts"], {"company_possible_match": 1})
            self.assertEqual(self.mock.create_calls, 1)
            self.assertEqual(self.mock.update_calls, 0)
            index = json.loads((second_dir / "staging-index.json").read_text())
            item = index["dispositions"][0]
            self.assertEqual(item["reason"], "soft_deleted_exact_match")
            self.assertFalse(item["write_attempted"])
            self.assertEqual(item["company_id"], company_id)

    def test_connection_probe_uses_valid_non_nil_company_uuid(self):
        environment = os.environ.copy()
        environment.update({
            "TWENTY_API_KEY": "test-key",
            "TWENTY_BASE_URL": f"http://127.0.0.1:{self.server.server_port}",
            "TWENTY_REQUEST_DELAY": "0",
        })
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--check-connection"],
            capture_output=True,
            check=False,
            env=environment,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        summary = json.loads(completed.stdout)
        self.assertTrue(summary["api_contract_usable"])
        people_paths = [path for path in self.mock.paths if path.startswith("/rest/people?")]
        self.assertEqual(len(people_paths), 1)
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(people_paths[0]).query)
        self.assertEqual(
            query["filter"],
            ['companyId[eq]:"11111111-1111-4111-8111-111111111111"'],
        )

    def test_cli_uses_environment_auth_and_emits_summary_only(self):
        source = json.loads(json.dumps(self.source))
        source["leads"] = source["leads"][:1]
        source["summary"]["returned"] = 1
        hidden_values = {
            str(source["leads"][0].get("business_name") or ""),
            str(source["leads"][0].get("phone") or ""),
        } - {""}

        with tempfile.TemporaryDirectory() as root:
            input_path = Path(root) / "input.json"
            output_dir = Path(root) / "output"
            input_path.write_text(json.dumps(source))
            environment = os.environ.copy()
            environment.update({
                "TWENTY_API_KEY": "test-key",
                "TWENTY_BASE_URL": f"http://127.0.0.1:{self.server.server_port}",
                "TWENTY_REQUEST_DELAY": "0",
            })
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input",
                    str(input_path),
                    "--output-dir",
                    str(output_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
                timeout=30,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            self.assertEqual(summary["counts"], {"company_staged_no_person_required": 1})
            self.assertFalse(summary["lead_rows_emitted"])
            self.assertTrue(all(value not in completed.stdout for value in hidden_values))
            self.assertTrue((output_dir / "staging-index.json").exists())
    def test_company_first_person_second_relation_and_idempotency(self):
        self.source = {
            "contract_version": "a1.discovery-result.v1", "run_id": "RUN-PEOPLE",
            "summary": {"returned": 1},
            "leads": [{
                "lead_fingerprint": "fp-person", "business_name": "Alpha Forge",
                "name": "Jane Doe", "country": "US", "phone": "859-555-0100",
                "email": "jane@example.com", "segment_hint": "farrier",
            }],
        }
        with tempfile.TemporaryDirectory() as root:
            first, first_dir = self.run_once(root, "person-first")
            self.assertEqual(first["counts"], {"company_staged_person_staged": 1})
            self.assertEqual(self.mock.create_calls, 1)
            self.assertEqual(self.mock.person_create_calls, 1)
            company_post = self.mock.paths.index("/rest/companies")
            person_post = self.mock.paths.index("/rest/people")
            self.assertLess(company_post, person_post)
            company_id, company = next(iter(self.mock.records.items()))
            person_id, person = next(iter(self.mock.people.items()))
            self.assertNotIn("phone", company)
            self.assertNotIn("email", company)
            self.assertEqual(person["name"], {"firstName": "Jane Doe", "lastName": ""})
            self.assertEqual(person["companyId"], company_id)
            self.assertIn("phones", person)
            self.assertIn("emails", person)
            index = json.loads((first_dir / "staging-index.json").read_text())
            disposition = index["dispositions"][0]
            self.assertEqual(disposition["person_id"], person_id)
            self.assertEqual(disposition["relation_status"], "verified")
            self.assertTrue(Path(disposition["company_reconciliation_artifact"]).is_file())
            self.assertTrue(Path(disposition["person_reconciliation_artifact"]).is_file())

            second, _ = self.run_once(root, "person-second")
            self.assertEqual(second["counts"], {"company_staged_person_staged": 1})
            self.assertEqual(self.mock.create_calls, 1)
            self.assertEqual(self.mock.person_create_calls, 1)
            self.assertEqual(self.mock.person_update_calls, 1)

    def test_immutable_people_fixture_covers_all_name_combinations(self):
        self.source = json.loads(PEOPLE_FIXTURE.read_text())
        with tempfile.TemporaryDirectory() as root:
            summary, output_dir = self.run_once(root, "people-fixture")
            self.assertEqual(summary["total"], 4)
            self.assertEqual(summary["counts"], {
                "blocked_missing_company_name": 1,
                "company_staged_no_person_required": 1,
                "company_staged_person_staged": 2,
            })
            self.assertEqual(len(self.mock.records), 3)
            self.assertEqual(len(self.mock.people), 2)
            index = json.loads((output_dir / "staging-index.json").read_text())
            self.assertTrue(index["complete"])

    def test_company_success_person_failure_is_terminal_and_not_retried(self):
        self.source = {
            "contract_version": "a1.discovery-result.v1", "run_id": "RUN-PERSON-FAIL",
            "summary": {"returned": 1},
            "leads": [{"lead_fingerprint": "fp-fail", "business_name": "Alpha", "name": "Jane Doe", "country": "US"}],
        }
        self.mock.fail_person_create = True
        with tempfile.TemporaryDirectory() as root:
            summary, output_dir = self.run_once(root, "person-fail")
            self.assertEqual(summary["counts"], {"company_staged_person_sync_failed": 1})
            index = json.loads((output_dir / "staging-index.json").read_text())
            item = index["dispositions"][0]
            self.assertIsNotNone(item["company_id"])
            self.assertIsNone(item["person_id"])
            self.assertTrue(item["write_outcome_uncertain"])
            self.assertEqual(sum(path.startswith("/rest/people") for path in self.mock.paths if "people" in path and "?" not in path), 1)

    def test_soft_deleted_person_is_held(self):
        self.source = {
            "contract_version": "a1.discovery-result.v1", "run_id": "RUN-SOFT-PERSON",
            "summary": {"returned": 1},
            "leads": [{"lead_fingerprint": "fp-soft", "business_name": "Alpha", "name": "Jane Doe", "country": "US", "email": "jane@example.com"}],
        }
        with tempfile.TemporaryDirectory() as root:
            first, _ = self.run_once(root, "soft-person-first")
            self.assertEqual(first["counts"], {"company_staged_person_staged": 1})
            person_id = next(iter(self.mock.people))
            self.mock.people[person_id]["deletedAt"] = "2026-09-04T00:00:00Z"
            second, _ = self.run_once(root, "soft-person-second")
            self.assertEqual(second["counts"], {"company_staged_person_possible_match": 1})
            self.assertEqual(self.mock.person_create_calls, 1)

    def test_existing_company_contacts_migrate_after_person_reconciliation(self):
        business_only = {
            "contract_version": "a1.discovery-result.v1", "run_id": "RUN-MIGRATE",
            "summary": {"returned": 1},
            "leads": [{"lead_fingerprint": "fp-migrate", "business_name": "Alpha", "country": "US", "phone": "859-555-0100", "email": "jane@example.com"}],
        }
        self.source = business_only
        with tempfile.TemporaryDirectory() as root:
            first, _ = self.run_once(root, "migration-company")
            self.assertEqual(first["counts"], {"company_staged_no_person_required": 1})
            company_id = next(iter(self.mock.records))
            self.assertIn("phone", self.mock.records[company_id])
            self.source["leads"][0]["name"] = "Jane Doe"
            second, second_dir = self.run_once(root, "migration-person")
            self.assertEqual(second["counts"], {"company_staged_person_staged": 1})
            self.assertIsNone(self.mock.records[company_id]["phone"])
            self.assertIsNone(self.mock.records[company_id]["email"])
            item_dir = next((second_dir / "items").iterdir())
            self.assertTrue((item_dir / "company-contact-migration.json").is_file())


if __name__ == "__main__":
    unittest.main()
