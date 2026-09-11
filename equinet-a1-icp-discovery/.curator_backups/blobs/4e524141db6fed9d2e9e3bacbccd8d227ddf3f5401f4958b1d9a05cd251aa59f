#!/usr/bin/env python3
"""Tests for the durable n8n polling-ticket state helper."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "poll_ticket.py"
SCHEMA = SKILL_DIR / "references" / "poll-ticket.schema.json"


def load_module():
    spec = importlib.util.spec_from_file_location("poll_ticket", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class PollTicketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()

    def test_new_ticket_has_versioned_ids_and_unset_markers(self) -> None:
        ticket = self.module.new_ticket(
            ticket_id="poll-001",
            workflow_id="wf-main",
            execution_id="exec-42",
            application_run_id="A1-20260828-001",
            deadline_at="2026-08-28T13:00:00Z",
            now="2026-08-28T12:00:00Z",
        )

        self.assertEqual(ticket["schema_version"], "equinet.n8n-poll-ticket.v1")
        self.assertEqual(ticket["final_node"], "Build Final Discovery Result")
        self.assertEqual(ticket["lifecycle_status"], "polling")
        self.assertEqual(ticket["poll_count"], 0)
        self.assertIsNone(ticket["result_claimed_at"])
        self.assertIsNone(ticket["result_retrieved_at"])
        self.assertIsNone(ticket["consumed_at"])
        self.assertIsNone(ticket["delivered_at"])
        self.module.validate_ticket(ticket)

    def test_observe_maps_n8n_status_and_increments_poll_count(self) -> None:
        ticket = self.module.new_ticket(
            ticket_id="poll-002",
            workflow_id="wf-main",
            execution_id="exec-43",
            application_run_id="A1-20260828-002",
            deadline_at="2026-08-28T13:00:00Z",
            now="2026-08-28T12:00:00Z",
        )

        running = self.module.observe(ticket, "running", now="2026-08-28T12:01:00Z")
        succeeded = self.module.observe(running, "success", now="2026-08-28T12:02:00Z")

        self.assertEqual(running["poll_count"], 1)
        self.assertEqual(running["lifecycle_status"], "polling")
        self.assertEqual(succeeded["poll_count"], 2)
        self.assertEqual(succeeded["lifecycle_status"], "succeeded")
        self.assertEqual(succeeded["terminal_at"], "2026-08-28T12:02:00Z")

    def test_success_result_can_be_claimed_only_once(self) -> None:
        ticket = self.module.new_ticket(
            ticket_id="poll-003",
            workflow_id="wf-main",
            execution_id="exec-44",
            application_run_id="A1-20260828-003",
            deadline_at="2026-08-28T13:00:00Z",
            now="2026-08-28T12:00:00Z",
        )
        ticket = self.module.observe(ticket, "success", now="2026-08-28T12:01:00Z")

        claimed, should_fetch = self.module.claim_result(ticket, now="2026-08-28T12:02:00Z")
        claimed_again, should_fetch_again = self.module.claim_result(
            claimed, now="2026-08-28T12:03:00Z"
        )

        self.assertTrue(should_fetch)
        self.assertFalse(should_fetch_again)
        self.assertEqual(claimed_again["result_claimed_at"], "2026-08-28T12:02:00Z")
        self.assertEqual(self.module.next_action(claimed_again), "recover_claim")

    def test_retrieved_result_is_consumed_then_delivered_idempotently(self) -> None:
        ticket = self.module.new_ticket(
            ticket_id="poll-004",
            workflow_id="wf-main",
            execution_id="exec-45",
            application_run_id="A1-20260828-004",
            deadline_at="2026-08-28T13:00:00Z",
            now="2026-08-28T12:00:00Z",
        )
        ticket = self.module.observe(ticket, "success", now="2026-08-28T12:01:00Z")
        ticket, _ = self.module.claim_result(ticket, now="2026-08-28T12:02:00Z")

        with tempfile.TemporaryDirectory() as temp_dir:
            discovery = {
                "contract_version": "a1.discovery-result.v1",
                "run_id": "A1-20260828-004",
                "leads": [{"lead_fingerprint": "fp-1", "business_name": "Alpha"}],
            }
            result_path = Path(temp_dir) / "discovery-result.json"
            result_path.write_text(json.dumps(discovery), encoding="utf-8")
            result_sha = __import__("hashlib").sha256(result_path.read_bytes()).hexdigest()
            ticket = self.module.mark_retrieved(
                ticket,
                result_sha256=result_sha,
                artifact_reference=str(result_path),
                now="2026-08-28T12:03:00Z",
            )
            self.assertEqual(self.module.next_action(ticket), "process_result")

            reconciliation = Path(temp_dir) / "reconciliation.json"
            reconciliation.write_text(json.dumps({
                "verification_status": "verified",
                "twenty_company_id": "company-1",
            }), encoding="utf-8")
            source_sha = __import__("hashlib").sha256(
                json.dumps(discovery, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            staging_index = Path(temp_dir) / "staging-index.json"
            staging_index.write_text(json.dumps({
                "schema_version": "a1.twenty-entity-staging-index.v3",
                "run_id": "A1-20260828-004",
                "source_contract_version": "a1.discovery-result.v1",
                "source_sha256": source_sha,
                "complete": True,
                "total": 1,
                "counts": {"company_staged_no_person_required": 1},
                "company_coverage": {"expected": 1, "terminal": 1, "verified_ids": 1},
                "person_coverage": {"expected": 0, "terminal": 0, "verified_relations": 0},
                "lane_indexes": {"no_website": {"schema_version": "a1.twenty-entity-staging-index.v2", "sha256": "c" * 64, "complete": True, "total": 1, "counts": {"company_staged_no_person_required": 1}}, "website_candidate": None},
                "dispositions": [{
                    "lead_fingerprint": "fp-1",
                    "lane": "no_website",
                    "status": "company_staged_no_person_required",
                    "company_id": "company-1",
                    "person_required": False,
                    "person_id": None,
                    "person_disposition": "not_required",
                    "relation_status": "not_required",
                    "company_reconciliation_artifact": str(reconciliation),
                    "person_reconciliation_artifact": None,
                    "relation_reconciliation_artifact": None,
                    "reason": "no_existing_company_match",
                    "artifact_reference": str(reconciliation),
                }],
            }), encoding="utf-8")
            ticket = self.module.mark_consumed(
                ticket,
                artifact_reference=str(staging_index),
                now="2026-08-28T12:04:00Z",
            )
        self.assertEqual(self.module.next_action(ticket), "deliver_terminal")

        delivered = self.module.mark_delivered(
            ticket,
            delivery_reference="bot-chat:equinet-a1-icp-discovery",
            now="2026-08-28T12:05:00Z",
        )
        delivered_again = self.module.mark_delivered(
            delivered,
            delivery_reference="duplicate",
            now="2026-08-28T12:06:00Z",
        )
        self.assertEqual(self.module.next_action(delivered_again), "stop")
        self.assertEqual(delivered_again["delivered_at"], "2026-08-28T12:05:00Z")
        self.assertEqual(
            delivered_again["delivery_reference"],
            "bot-chat:equinet-a1-icp-discovery",
        )

    def test_consumption_requires_and_accepts_verified_person_relation(self) -> None:
        ticket = self.module.new_ticket(
            ticket_id="poll-person", workflow_id="wf-main", execution_id="exec-person",
            application_run_id="A1-PERSON", deadline_at="2026-09-04T13:00:00Z",
            now="2026-09-04T12:00:00Z",
        )
        ticket = self.module.observe(ticket, "success", now="2026-09-04T12:01:00Z")
        ticket, _ = self.module.claim_result(ticket, now="2026-09-04T12:02:00Z")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            discovery = {
                "contract_version": "a1.discovery-result.v1", "run_id": "A1-PERSON",
                "leads": [{"lead_fingerprint": "fp-person", "business_name": "Alpha", "name": "Jane Doe"}],
            }
            result_path = root / "result.json"
            result_path.write_text(json.dumps(discovery), encoding="utf-8")
            ticket = self.module.mark_retrieved(
                ticket,
                result_sha256=__import__("hashlib").sha256(result_path.read_bytes()).hexdigest(),
                artifact_reference=str(result_path), now="2026-09-04T12:03:00Z",
            )
            company_rec = root / "company-reconciliation.json"
            person_rec = root / "person-reconciliation.json"
            disposition_artifact = root / "disposition.json"
            company_rec.write_text(json.dumps({"verification_status": "verified", "twenty_company_id": "company-1"}))
            person_rec.write_text(json.dumps({
                "verification_status": "verified", "relation_status": "verified",
                "twenty_company_id": "company-1", "twenty_person_id": "person-1",
            }))
            disposition_artifact.write_text("{}")
            source_sha = __import__("hashlib").sha256(
                json.dumps(discovery, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            index = root / "index.json"
            index.write_text(json.dumps({
                "schema_version": "a1.twenty-entity-staging-index.v3", "run_id": "A1-PERSON",
                "source_contract_version": "a1.discovery-result.v1", "source_sha256": source_sha,
                "complete": True, "total": 1, "counts": {"company_staged_person_staged": 1},
                "company_coverage": {"expected": 1, "terminal": 1, "verified_ids": 1},
                "person_coverage": {"expected": 1, "terminal": 1, "verified_relations": 1},
                "lane_indexes": {"no_website": {"schema_version": "a1.twenty-entity-staging-index.v2", "sha256": "d" * 64, "complete": True, "total": 1, "counts": {"company_staged_person_staged": 1}}, "website_candidate": None},
                "dispositions": [{
                    "lead_fingerprint": "fp-person", "lane": "no_website",
                    "status": "company_staged_person_staged", "company_id": "company-1",
                    "person_required": True, "person_id": "person-1", "person_disposition": "staged",
                    "relation_status": "verified", "reason": "verified",
                    "company_reconciliation_artifact": str(company_rec),
                    "person_reconciliation_artifact": str(person_rec),
                    "relation_reconciliation_artifact": str(person_rec),
                    "artifact_reference": str(disposition_artifact),
                }],
            }))
            consumed = self.module.mark_consumed(ticket, artifact_reference=str(index), now="2026-09-04T12:04:00Z")
            self.assertIsNotNone(consumed["consumed_at"])

    def test_consumption_accepts_terminal_person_partial_failure(self) -> None:
        ticket = self.module.new_ticket(
            ticket_id="poll-person-fail", workflow_id="wf-main", execution_id="exec-person-fail",
            application_run_id="A1-PERSON-FAIL", deadline_at="2026-09-04T13:00:00Z",
            now="2026-09-04T12:00:00Z",
        )
        ticket = self.module.observe(ticket, "success", now="2026-09-04T12:01:00Z")
        ticket, _ = self.module.claim_result(ticket, now="2026-09-04T12:02:00Z")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            discovery = {"contract_version": "a1.discovery-result.v1", "run_id": "A1-PERSON-FAIL", "leads": [{"lead_fingerprint": "fp", "name": "Jane Doe"}]}
            result_path = root / "result.json"
            result_path.write_text(json.dumps(discovery))
            ticket = self.module.mark_retrieved(ticket, result_sha256=__import__("hashlib").sha256(result_path.read_bytes()).hexdigest(), artifact_reference=str(result_path), now="2026-09-04T12:03:00Z")
            company_rec = root / "company.json"
            company_rec.write_text(json.dumps({"verification_status": "verified", "twenty_company_id": "company-1"}))
            disposition_artifact = root / "disposition.json"
            disposition_artifact.write_text("{}")
            source_sha = __import__("hashlib").sha256(json.dumps(discovery, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            index = root / "index.json"
            index.write_text(json.dumps({
                "schema_version": "a1.twenty-entity-staging-index.v3", "run_id": "A1-PERSON-FAIL",
                "source_contract_version": "a1.discovery-result.v1", "source_sha256": source_sha,
                "complete": True, "total": 1, "counts": {"company_staged_person_sync_failed": 1},
                "company_coverage": {"expected": 1, "terminal": 1, "verified_ids": 1},
                "person_coverage": {"expected": 1, "terminal": 1, "verified_relations": 0},
                "lane_indexes": {"no_website": {"schema_version": "a1.twenty-entity-staging-index.v2", "sha256": "e" * 64, "complete": True, "total": 1, "counts": {"company_staged_person_sync_failed": 1}}, "website_candidate": None},
                "dispositions": [{"lead_fingerprint": "fp", "lane": "no_website", "status": "company_staged_person_sync_failed", "company_id": "company-1", "person_required": True, "person_id": None, "person_disposition": "sync_failed", "relation_status": "unverified", "reason": "person_write_failed", "company_reconciliation_artifact": str(company_rec), "person_reconciliation_artifact": None, "relation_reconciliation_artifact": None, "artifact_reference": str(disposition_artifact)}],
            }))
            consumed = self.module.mark_consumed(ticket, artifact_reference=str(index), now="2026-09-04T12:04:00Z")
            self.assertIsNotNone(consumed["consumed_at"])

    def test_deadline_expires_polling_ticket(self) -> None:
        ticket = self.module.new_ticket(
            ticket_id="poll-005",
            workflow_id="wf-main",
            execution_id="exec-46",
            application_run_id="A1-20260828-005",
            deadline_at="2026-08-28T12:10:00Z",
            now="2026-08-28T12:00:00Z",
        )

        expired = self.module.expire_if_due(ticket, now="2026-08-28T12:11:00Z")

        self.assertEqual(expired["lifecycle_status"], "timed_out")
        self.assertEqual(self.module.next_action(expired), "deliver_terminal")

    def test_consumption_rejects_non_staging_artifact(self) -> None:
        ticket = self.module.new_ticket(
            ticket_id="poll-stage-gate",
            workflow_id="wf-main",
            execution_id="exec-stage-gate",
            application_run_id="A1-STAGE-GATE",
            deadline_at="2026-08-28T13:00:00Z",
            now="2026-08-28T12:00:00Z",
        )
        ticket = self.module.observe(ticket, "success", now="2026-08-28T12:01:00Z")
        ticket, _ = self.module.claim_result(ticket, now="2026-08-28T12:02:00Z")
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = Path(temp_dir) / "result.json"
            result_path.write_text(json.dumps({
                "contract_version": "a1.discovery-result.v1",
                "run_id": "A1-STAGE-GATE",
                "leads": [{"lead_fingerprint": "fp-1", "business_name": "Alpha"}],
            }), encoding="utf-8")
            digest = __import__("hashlib").sha256(result_path.read_bytes()).hexdigest()
            ticket = self.module.mark_retrieved(ticket, result_sha256=digest, artifact_reference=str(result_path), now="2026-08-28T12:03:00Z")
            artifact = Path(temp_dir) / "review-package.json"
            artifact.write_text(json.dumps({"schema_version": "1.1.0"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "complete combined Twenty entity staging index"):
                self.module.mark_consumed(ticket, artifact_reference=str(artifact), now="2026-08-28T12:04:00Z")

    def test_consumption_rejects_combined_index_with_wrong_source_hash(self) -> None:
        ticket = self.module.new_ticket(
            ticket_id="poll-source-gate", workflow_id="wf-main", execution_id="exec-source",
            application_run_id="A1-SOURCE", deadline_at="2026-08-28T13:00:00Z",
            now="2026-08-28T12:00:00Z",
        )
        ticket = self.module.observe(ticket, "success", now="2026-08-28T12:01:00Z")
        ticket, _ = self.module.claim_result(ticket, now="2026-08-28T12:02:00Z")
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = Path(temp_dir) / "result.json"
            result_path.write_text(json.dumps({
                "contract_version": "a1.discovery-result.v1", "run_id": "A1-SOURCE",
                "leads": [{"lead_fingerprint": "fp-1", "business_name": "Alpha"}],
            }), encoding="utf-8")
            digest = __import__("hashlib").sha256(result_path.read_bytes()).hexdigest()
            ticket = self.module.mark_retrieved(ticket, result_sha256=digest, artifact_reference=str(result_path), now="2026-08-28T12:03:00Z")
            artifact = Path(temp_dir) / "combined.json"
            artifact.write_text(json.dumps({
                "schema_version": "a1.twenty-entity-staging-index.v3", "run_id": "A1-SOURCE",
                "source_contract_version": "a1.discovery-result.v1", "source_sha256": "0" * 64,
                "complete": True, "total": 1,
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source_sha256"):
                self.module.mark_consumed(ticket, artifact_reference=str(artifact), now="2026-08-28T12:04:00Z")

    def test_failed_execution_never_requests_result_data(self) -> None:
        ticket = self.module.new_ticket(
            ticket_id="poll-006",
            workflow_id="wf-main",
            execution_id="exec-47",
            application_run_id="A1-20260828-006",
            deadline_at="2026-08-28T13:00:00Z",
            now="2026-08-28T12:00:00Z",
        )
        failed = self.module.observe(
            ticket,
            "error",
            error="workflow failed",
            now="2026-08-28T12:01:00Z",
        )

        self.assertEqual(failed["lifecycle_status"], "failed")
        self.assertEqual(self.module.next_action(failed), "deliver_terminal")
        with self.assertRaises(ValueError):
            self.module.claim_result(failed, now="2026-08-28T12:02:00Z")

    def test_cli_persists_atomic_state_transitions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "ticket.json"
            init = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "init",
                    "--file",
                    str(path),
                    "--ticket-id",
                    "poll-cli",
                    "--workflow-id",
                    "wf-main",
                    "--execution-id",
                    "exec-cli",
                    "--application-run-id",
                    "A1-CLI",
                    "--deadline-at",
                    "2026-08-28T13:00:00Z",
                    "--now",
                    "2026-08-28T12:00:00Z",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(json.loads(init.stdout)["ticket_id"], "poll-cli")

            observed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "observe",
                    "--file",
                    str(path),
                    "--execution-status",
                    "running",
                    "--now",
                    "2026-08-28T12:01:00Z",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            state = json.loads(observed.stdout)
            self.assertEqual(state["poll_count"], 1)
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["poll_count"], 1)

    def test_cli_creates_missing_ticket_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "runtime" / "n8n-poll-tickets" / "ticket.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "init",
                    "--file",
                    str(path),
                    "--ticket-id",
                    "poll-nested",
                    "--workflow-id",
                    "wf-main",
                    "--execution-id",
                    "exec-nested",
                    "--application-run-id",
                    "A1-NESTED",
                    "--deadline-at",
                    "2026-08-28T13:00:00Z",
                    "--now",
                    "2026-08-28T12:00:00Z",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(path.is_file())

    def test_schema_requires_durable_idempotency_markers(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        required = set(schema["required"])
        self.assertTrue(
            {
                "workflow_id",
                "execution_id",
                "application_run_id",
                "poll_count",
                "result_claimed_at",
                "result_retrieved_at",
                "consumed_at",
                "delivered_at",
            }.issubset(required)
        )
        self.assertEqual(schema["properties"]["final_node"]["const"], "Build Final Discovery Result")
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
