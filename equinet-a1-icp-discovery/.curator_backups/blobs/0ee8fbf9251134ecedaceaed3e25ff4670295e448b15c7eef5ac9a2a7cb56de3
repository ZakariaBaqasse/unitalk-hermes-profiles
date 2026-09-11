from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "manage_enrichment.py"
PROFILE = Path(__file__).resolve().parents[3]
FIXTURE = PROFILE / "evaluations" / "step9" / "candidates" / "rood-riddle-podiatry"
PYTHON = PROFILE / ".venv" / "bin" / "python"


def load_module():
    spec = importlib.util.spec_from_file_location("manage_enrichment", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def handoff():
    return {
        "schema_version": "a1.discovery-result.v1",
        "run": {"run_id": "RUN-N8N-001", "completed_at": "2026-08-28T12:00:00Z"},
        "leads": [
            {"lead_id": "LEAD-001", "name": "Alpha Farrier", "website": None},
            {"lead_id": "LEAD-002", "name": "Beta Farm", "website": "https://beta.example"},
        ],
    }


class EnrichmentStateTests(unittest.TestCase):
    def test_default_pipeline_python_is_profile_local_and_has_yaml(self):
        module = load_module()
        expected = PROFILE / ".venv" / "bin" / "python"
        self.assertEqual(module.DEFAULT_PIPELINE_PYTHON, expected)
        result = subprocess.run(
            [str(module.DEFAULT_PIPELINE_PYTHON), "-c", "import yaml"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_summary_exposes_durable_next_action_without_lead_rows(self):
        module = load_module()
        state = module.initialize_state(handoff())
        summary = module.state_summary(state)
        self.assertEqual(summary["next_action"], "research_pending")
        self.assertEqual(summary["pending_count"], 2)
        self.assertFalse(summary["lead_rows_emitted"])

    def test_initialize_preserves_n8n_leads_without_fabricating_enrichment(self):
        module = load_module()

        state = module.initialize_state(handoff(), max_retries=2)

        self.assertEqual(state["schema_version"], "a1.website-enrichment-state.v1")
        self.assertEqual(state["run"], handoff()["run"])
        self.assertEqual(list(state["leads"]), ["LEAD-001", "LEAD-002"])
        self.assertEqual(
            state["leads"]["LEAD-001"],
            {
                "lead": handoff()["leads"][0],
                "status": "pending",
                "attempts": 0,
                "failure_history": [],
                "enrichment": None,
                "pipeline_inputs": {},
                "artifacts": {},
            },
        )
        rendered = json.dumps(state)
        self.assertNotIn("evidence", rendered)
        self.assertNotIn("official_website_url", rendered)

    def test_initialize_accepts_canonical_compact_discovery_result(self):
        module = load_module()
        canonical = {
            "contract_version": "a1.discovery-result.v1",
            "run_id": "RUN-CANONICAL-001",
            "status": "discovery_complete",
            "request": {"requested_count": 2},
            "source_policy": {
                "registry_id": "equinet-a1-approved-source-register",
                "registry_version": "1.4.3",
            },
            "summary": {"returned": 2},
            "leads": [
                {"lead_fingerprint": "fp-alpha", "name": "Alpha Farrier"},
                {"lead_fingerprint": "fp-beta", "name": "Beta Farm"},
            ],
            "sources": [],
            "warnings": [],
            "started_at": "2026-08-28T11:00:00Z",
            "finished_at": "2026-08-28T12:00:00Z",
        }

        state = module.initialize_state(canonical)

        self.assertEqual(state["run"]["run_id"], "RUN-CANONICAL-001")
        self.assertEqual(list(state["leads"]), ["fp-alpha", "fp-beta"])
        self.assertEqual(state["leads"]["fp-alpha"]["lead"], canonical["leads"][0])
        self.assertEqual(state["discovery_result"]["source_policy"]["registry_version"], "1.4.3")

    def test_initialize_rejects_wrong_schema_and_duplicate_ids(self):
        module = load_module()
        wrong = handoff()
        wrong["schema_version"] = "other"
        with self.assertRaisesRegex(ValueError, "a1.discovery-result.v1"):
            module.initialize_state(wrong)

        duplicate = handoff()
        duplicate["leads"].append(dict(duplicate["leads"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate lead"):
            module.initialize_state(duplicate)

    def test_next_batch_is_stable_and_contains_only_pending_leads(self):
        module = load_module()
        state = module.initialize_state(handoff())
        state["leads"]["LEAD-001"]["status"] = "completed"

        batch = module.next_batch(state, batch_size=1)

        self.assertEqual(batch["schema_version"], "a1.website-enrichment-batch.v1")
        self.assertEqual(batch["run_id"], "RUN-N8N-001")
        self.assertEqual(batch["leads"], [handoff()["leads"][1]])
        self.assertEqual(batch["requirements"]["approved_web_tools"], ["web_search", "web_extract"])
        self.assertTrue(batch["requirements"]["official_website_preferred"])
        self.assertTrue(batch["requirements"]["no_site_completion_allowed"])
        self.assertTrue(batch["requirements"]["destination_page_citations_required_when_website_verified"])

    def test_completed_result_requires_hermes_cited_destination_evidence(self):
        module = load_module()
        state = module.initialize_state(handoff())
        result = {
            "lead_id": "LEAD-001",
            "status": "completed",
            "research_method": "hermes_approved_web_tools",
            "website_status": "verified",
            "official_website_url": "https://alpha.example/",
            "evidence": [
                {
                    "evidence_id": "EV-ALPHA-HOME",
                    "source_url": "https://alpha.example/services",
                    "source_name": "Alpha Farrier services",
                    "source_type": "official_business_website",
                    "retrieved_at": "2026-08-28T12:30:00Z",
                    "retrieval_tool": "web_extract",
                    "evidence_excerpt": "Professional hoof-care services in Kentucky.",
                    "claim": "Alpha offers professional hoof-care services in Kentucky.",
                    "fact_or_inference": "direct_fact",
                }
            ],
            "missing_information": ["Public email not found"],
            "conflicts": [],
        }

        updated = module.apply_results(
            state,
            {"schema_version": "a1.website-enrichment-results.v1", "results": [result]},
        )

        record = updated["leads"]["LEAD-001"]
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["attempts"], 1)
        self.assertEqual(record["enrichment"], result)
        self.assertIsNone(state["leads"]["LEAD-001"]["enrichment"])

    def test_no_site_completion_needs_no_url_or_excerpt_and_blocks_pipeline_inputs(self):
        module = load_module()
        state = module.initialize_state(handoff())
        result = {
            "lead_id": "LEAD-001",
            "status": "completed",
            "research_method": "hermes_approved_web_tools",
            "website_status": "none_found",
            "official_website_url": None,
            "evidence": [],
            "missing_information": ["official_business_website_not_found"],
            "conflicts": [],
        }
        updated = module.apply_results(
            state,
            {"schema_version": "a1.website-enrichment-results.v1", "results": [result]},
        )
        self.assertEqual(updated["leads"]["LEAD-001"]["status"], "completed")
        self.assertEqual(updated["leads"]["LEAD-001"]["enrichment"]["website_status"], "none_found")

        invalid = dict(result)
        invalid["qualification_assessment"] = {"criterion_assessments": {}}
        with self.assertRaisesRegex(ValueError, "No-site completion cannot contain"):
            module.apply_results(state, {"schema_version": "a1.website-enrichment-results.v1", "results": [invalid]})

    def test_verified_completion_without_pipeline_inputs_is_terminal_for_unscored_overlay(self):
        module = load_module()
        state = module.initialize_state(handoff())
        result = {
            "lead_id": "LEAD-001",
            "status": "completed",
            "research_method": "hermes_approved_web_tools",
            "website_status": "verified",
            "official_website_url": "https://alpha.example/",
            "evidence": [{
                "evidence_id": "EV-ALPHA-HOME",
                "source_url": "https://alpha.example/",
                "source_name": "Alpha",
                "source_type": "official_business_website",
                "retrieved_at": "2026-08-28T12:30:00Z",
                "retrieval_tool": "web_extract",
                "evidence_excerpt": "Professional hoof care.",
                "claim": "Alpha provides professional hoof care.",
                "fact_or_inference": "direct_fact",
            }],
            "missing_information": ["classification_not_completed"],
            "conflicts": [],
        }
        updated = module.apply_results(
            state, {"schema_version": "a1.website-enrichment-results.v1", "results": [result]}
        )
        updated["leads"]["LEAD-002"]["status"] = "failed"

        summary = module.state_summary(updated)

        self.assertTrue(summary["terminal"])
        self.assertEqual(summary["terminal_count"], 2)
        self.assertEqual(summary["incomplete_count"], 0)
        self.assertEqual(summary["next_action"], "build_overlays")

    def test_completed_result_rejects_missing_or_non_destination_evidence(self):
        module = load_module()
        base = {
            "lead_id": "LEAD-001",
            "status": "completed",
            "research_method": "hermes_approved_web_tools",
            "website_status": "verified",
            "official_website_url": "https://alpha.example/",
            "evidence": [],
            "missing_information": [],
            "conflicts": [],
        }
        state = module.initialize_state(handoff())
        with self.assertRaisesRegex(ValueError, "schema validation failed|Verified-website enrichment requires at least one cited evidence"):
            module.apply_results(state, {"schema_version": "a1.website-enrichment-results.v1", "results": [base]})

        search_only = dict(base)
        search_only["evidence"] = [{
            "evidence_id": "EV-ALPHA-HOME",
            "source_url": "https://alpha.example/",
            "source_name": "Alpha",
            "source_type": "official_business_website",
            "retrieved_at": "2026-08-28T12:30:00Z",
            "retrieval_tool": "web_search",
            "evidence_excerpt": "Search snippet",
            "claim": "Alpha exists.",
            "fact_or_inference": "direct_fact",
        }]
        with self.assertRaisesRegex(ValueError, "'web_extract' was expected|web_extract destination-page citation"):
            module.apply_results(state, {"schema_version": "a1.website-enrichment-results.v1", "results": [search_only]})

        wrong_domain = copy_result = json.loads(json.dumps(search_only))
        copy_result["evidence"][0]["retrieval_tool"] = "web_extract"
        copy_result["evidence"][0]["source_url"] = "https://directory.example/alpha"
        with self.assertRaisesRegex(ValueError, "official website domain"):
            module.apply_results(state, {"schema_version": "a1.website-enrichment-results.v1", "results": [wrong_domain]})

    def test_pipeline_inputs_cannot_reference_uncited_evidence(self):
        module = load_module()
        state = module.initialize_state(handoff())
        result = {
            "lead_id": "LEAD-001",
            "status": "completed",
            "research_method": "hermes_approved_web_tools",
            "website_status": "verified",
            "official_website_url": "https://alpha.example/",
            "evidence": [{
                "evidence_id": "EV-ALPHA-HOME",
                "source_url": "https://alpha.example/",
                "source_name": "Alpha",
                "source_type": "official_business_website",
                "retrieved_at": "2026-08-28T12:30:00Z",
                "retrieval_tool": "web_extract",
                "evidence_excerpt": "Professional hoof care.",
                "claim": "Alpha provides professional hoof care.",
                "fact_or_inference": "direct_fact",
            }],
            "missing_information": [],
            "conflicts": [],
            "qualification_assessment": {
                "schema_version": "1.0.0",
                "segment": "farrier",
                "criterion_assessments": {
                    "farrier.professional_activity": {
                        "status": "confirmed", "evidence_ids": ["EV-NOT-CITED"], "notes": None
                    }
                },
                "missing_minimum_fields": [],
            },
        }
        with self.assertRaisesRegex(ValueError, "qualification_assessment references unknown"):
            module.apply_results(
                state, {"schema_version": "a1.website-enrichment-results.v1", "results": [result]}
            )

    def test_failures_are_checkpointed_and_retry_budget_is_bounded(self):
        module = load_module()
        state = module.initialize_state(handoff(), max_retries=1)

        first = module.record_failure(
            state, "LEAD-001", "HTTP 429", "2026-08-28T12:30:00Z", retryable=True
        )
        self.assertEqual(first["leads"]["LEAD-001"]["status"], "pending")
        self.assertEqual(first["leads"]["LEAD-001"]["attempts"], 1)
        second = module.record_failure(
            first, "LEAD-001", "HTTP 429 again", "2026-08-28T12:35:00Z", retryable=True
        )
        self.assertEqual(second["leads"]["LEAD-001"]["status"], "failed")
        self.assertEqual(len(second["leads"]["LEAD-001"]["failure_history"]), 2)
        self.assertEqual(module.next_batch(second, 10)["leads"], [handoff()["leads"][1]])

    def test_atomic_checkpoint_round_trip(self):
        module = load_module()
        state = module.initialize_state(handoff())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "state.json"
            module.save_state(path, state)
            self.assertEqual(module.load_state(path), state)
            self.assertFalse(path.with_suffix(".json.tmp").exists())

    def test_run_ready_executes_existing_wrappers_without_inventing_inputs(self):
        module = load_module()
        state = module.initialize_state(handoff())
        classification = json.loads((FIXTURE / "classification-decision.json").read_text())
        qualification = json.loads((FIXTURE / "qualification-assessment.json").read_text())
        confidence = json.loads((FIXTURE / "confidence-assessment.json").read_text())
        classification["seed_id"] = "LEAD-001"
        confidence["candidate_reference"] = {"run_id": "RUN-N8N-001", "seed_id": "LEAD-001"}
        evidence = []
        for evidence_id in confidence["available_evidence_ids"]:
            evidence.append({
                "evidence_id": evidence_id,
                "source_url": "https://alpha.example/services",
                "source_name": "Alpha services",
                "source_type": "official_business_website",
                "retrieved_at": "2026-08-28T12:30:00Z",
                "retrieval_tool": "web_extract",
                "evidence_excerpt": "Public professional information from the official site.",
                "claim": "The official site publishes this professional information.",
                "fact_or_inference": "direct_fact",
            })
        result = {
            "lead_id": "LEAD-001",
            "status": "completed",
            "research_method": "hermes_approved_web_tools",
            "website_status": "verified",
            "official_website_url": "https://alpha.example/",
            "evidence": evidence,
            "missing_information": [],
            "conflicts": [],
            "classification_decision": classification,
            "qualification_assessment": qualification,
            "confidence_assessment": confidence,
        }
        state = module.apply_results(
            state, {"schema_version": "a1.website-enrichment-results.v1", "results": [result]}
        )

        with tempfile.TemporaryDirectory() as directory:
            updated, report = module.run_ready(state, Path(directory), PYTHON)

            self.assertEqual(report["scored"], ["LEAD-001"])
            self.assertEqual(report["skipped"]["LEAD-002"], [
                "classification_decision", "qualification_assessment", "confidence_assessment"
            ])
            record = updated["leads"]["LEAD-001"]
            self.assertEqual(record["status"], "scored")
            scoring_path = Path(record["artifacts"]["scoring_package"])
            scoring = json.loads(scoring_path.read_text())
            expected_scoring = json.loads((FIXTURE / "scoring-package.json").read_text())["scoring"]
            expected_scoring["model_version"] = "1.1.0"
            self.assertEqual(scoring["scoring"], expected_scoring)


if __name__ == "__main__":
    unittest.main()
