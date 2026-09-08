from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "route_and_overlay.py"
spec = importlib.util.spec_from_file_location("route_and_overlay", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class RouteAndOverlayTests(unittest.TestCase):
    def discovery(self):
        return {
            "contract_version": "a1.discovery-result.v1",
            "run_id": "RUN-1",
            "status": "discovery_complete",
            "summary": {"returned": 3},
            "leads": [
                {"lead_fingerprint": "phone:1", "business_name": "No Site"},
                {"lead_fingerprint": "domain:example.com", "business_name": "Website", "website": "https://example.com"},
                {"lead_fingerprint": "name:invalid", "business_name": "Invalid", "website": "://bad"},
            ],
        }

    def test_route_is_complete_and_emits_no_site_overlays(self):
        with tempfile.TemporaryDirectory() as root:
            result = module.route_discovery(self.discovery(), Path(root))
            self.assertEqual(result["counts"], {"no_website": 2, "website_candidate": 1})
            no_site = json.loads((Path(root) / "no-website-overlays.json").read_text())
            overlay = no_site["overlays"][0]
            self.assertEqual(overlay["icp_score_status"], "NOT_SCORED")
            self.assertIsNone(overlay["icp_score"])
            invalid_overlay = next(item for item in no_site["overlays"] if item["lead_fingerprint"] == "name:invalid")
            self.assertEqual(invalid_overlay["notes"]["fallback_reason"], "invalid_website_candidate")
            self.assertEqual(result["routes"][2]["candidate_status"], "invalid")

    def test_overlay_validation_keeps_zero_as_real_score(self):
        overlay = {
            "schema_version": module.OVERLAY_SCHEMA,
            "lead_fingerprint": "domain:example.com",
            "website_status": "verified",
            "enrichment_status": "completed",
            "official_website_url": "https://example.com",
            "qualification_status": "ELIGIBLE",
            "icp_score_status": "SCORED",
            "icp_score": 0,
            "icp_band": "UNQUALIFIED",
            "icp_outcome": "unqualified_farrier",
            "evidence_confidence_score": 80,
            "evidence_confidence_level": "HIGH",
            "notes": {},
        }
        module.validate_overlay(overlay)
        overlay["icp_score_status"] = "NOT_SCORED"
        overlay["qualification_status"] = "NOT_CHECKED"
        overlay["website_status"] = "none_found"
        overlay["enrichment_status"] = "failed"
        overlay["official_website_url"] = None
        with self.assertRaisesRegex(ValueError, "null score"):
            module.validate_overlay(overlay)

    def test_build_scored_overlay_from_real_wrapper_shapes(self):
        discovery = {
            "contract_version": "a1.discovery-result.v1",
            "run_id": "RUN-2",
            "leads": [{"lead_fingerprint": "domain:example.com", "business_name": "Example", "website": "https://example.com"}],
        }
        with tempfile.TemporaryDirectory() as root:
            root_path = Path(root)
            qualification = root_path / "qualification.json"
            confidence = root_path / "confidence.json"
            scoring = root_path / "scoring.json"
            qualification.write_text(json.dumps({"qualification": {"exclusion_status": "eligible", "icp_config_version": "1.1.0"}}))
            confidence.write_text(json.dumps({"confidence": {"score": 84, "level": "high", "method_version": "1.1.0", "limitations": []}}))
            scoring.write_text(json.dumps({"scoring": {"status": "scored", "score": 72, "band": "medium", "model_version": "1.0.0", "block_reason": None}, "audit": {"outcome": "qualified_farrier"}}))
            state = {
                "schema_version": "a1.website-enrichment-state.v1",
                "run": {"run_id": "RUN-2"},
                "leads": {
                    "domain:example.com": {
                        "status": "scored",
                        "enrichment": {"website_status": "verified", "official_website_url": "https://example.com", "missing_information": []},
                        "artifacts": {
                            "qualification_package": str(qualification),
                            "confidence_package": str(confidence),
                            "scoring_package": str(scoring),
                        },
                    }
                },
            }
            result = module.build_website_overlays(discovery, state)
            overlay = result["overlays"][0]
            self.assertEqual(overlay["icp_score"], 72)
            self.assertEqual(overlay["icp_band"], "MEDIUM")
            self.assertEqual(overlay["evidence_confidence_level"], "HIGH")
            self.assertEqual(overlay["qualification_status"], "ELIGIBLE")

    def test_build_verified_unscored_overlay_preserves_official_domain(self):
        discovery = {
            "contract_version": "a1.discovery-result.v1",
            "run_id": "RUN-VERIFIED-UNSCORED",
            "leads": [{
                "lead_fingerprint": "place:verified",
                "business_name": "Verified Association",
                "website": "http://candidate.example/",
            }],
        }
        state = {
            "schema_version": "a1.website-enrichment-state.v1",
            "run": {"run_id": "RUN-VERIFIED-UNSCORED"},
            "leads": {
                "place:verified": {
                    "status": "completed",
                    "enrichment": {
                        "website_status": "verified",
                        "official_website_url": "https://official.example/",
                        "missing_information": ["classification_not_completed"],
                        "conflicts": [],
                    },
                    "pipeline_inputs": {},
                    "artifacts": {},
                }
            },
        }

        result = module.build_website_overlays(discovery, state)

        overlay = result["overlays"][0]
        self.assertEqual(overlay["website_status"], "verified")
        self.assertEqual(overlay["enrichment_status"], "completed")
        self.assertEqual(overlay["official_website_url"], "https://official.example/")
        self.assertEqual(overlay["qualification_status"], "NOT_CHECKED")
        self.assertEqual(overlay["icp_score_status"], "NOT_SCORED")
        self.assertIsNone(overlay["icp_score"])
        self.assertEqual(overlay["notes"]["fallback_reason"], "verified_site_unscored_missing_pipeline_inputs")
        module.validate_overlay(overlay)

    def test_merge_indexes_requires_exact_coverage(self):
        discovery = self.discovery()
        first = {
            "schema_version": module.STAGING_INDEX_SCHEMA,
            "run_id": "RUN-1",
            "complete": True,
            "total": 2,
            "counts": {"company_staged_no_person_required": 2},
            "dispositions": [
                {"lead_fingerprint": "phone:1", "status": "company_staged_no_person_required", "company_id": "company-1", "person_required": False, "person_disposition": "not_required", "relation_status": "not_required", "company_reconciliation_artifact": "/tmp/reconciliation-1.json", "reason": "verified", "artifact_reference": "/tmp/disposition-1.json"},
                {"lead_fingerprint": "name:invalid", "status": "company_staged_no_person_required", "company_id": "company-3", "person_required": False, "person_disposition": "not_required", "relation_status": "not_required", "company_reconciliation_artifact": "/tmp/reconciliation-3.json", "reason": "verified", "artifact_reference": "/tmp/disposition-3.json"},
            ],
        }
        second = {
            "schema_version": module.STAGING_INDEX_SCHEMA,
            "run_id": "RUN-1",
            "complete": True,
            "total": 1,
            "counts": {"company_staged_no_person_required": 1},
            "dispositions": [
                {"lead_fingerprint": "domain:example.com", "status": "company_staged_no_person_required", "company_id": "company-2", "person_required": False, "person_disposition": "not_required", "relation_status": "not_required", "company_reconciliation_artifact": "/tmp/reconciliation-2.json", "reason": "verified", "artifact_reference": "/tmp/disposition-2.json"},
            ],
        }
        merged = module.merge_indexes(discovery, first, second)
        self.assertTrue(merged["complete"])
        self.assertEqual(merged["total"], 3)
        with self.assertRaisesRegex(ValueError, "Missing website_candidate staging index"):
            module.merge_indexes(discovery, first, None)

    def test_merge_indexes_requires_person_terminal_state_and_relation(self):
        discovery = {
            "contract_version": "a1.discovery-result.v1", "run_id": "RUN-PERSON",
            "leads": [{"lead_fingerprint": "fp-person", "business_name": "Alpha", "name": "Jane Doe"}],
        }
        index = {
            "schema_version": module.STAGING_INDEX_SCHEMA, "run_id": "RUN-PERSON",
            "complete": True, "total": 1, "counts": {"company_staged_person_staged": 1},
            "dispositions": [{
                "lead_fingerprint": "fp-person", "status": "company_staged_person_staged",
                "company_id": "company-1", "person_required": True, "person_id": "person-1",
                "person_disposition": "staged", "relation_status": "verified", "reason": "verified",
                "company_reconciliation_artifact": "/tmp/company.json",
                "person_reconciliation_artifact": "/tmp/person.json",
                "relation_reconciliation_artifact": "/tmp/person.json",
                "artifact_reference": "/tmp/disposition.json",
            }],
        }
        merged = module.merge_indexes(discovery, index, None)
        self.assertEqual(merged["person_coverage"], {"expected": 1, "terminal": 1, "verified_relations": 1})
        broken = json.loads(json.dumps(index))
        broken["dispositions"][0]["relation_status"] = "unverified"
        with self.assertRaisesRegex(ValueError, "relation"):
            module.merge_indexes(discovery, broken, None)

    def test_processing_next_action_is_artifact_driven(self):
        discovery = self.discovery()
        with tempfile.TemporaryDirectory() as root:
            work = Path(root)
            self.assertEqual(module.processing_next_action(discovery, work)["next_action"], "route_result")
            module.route_discovery(discovery, work)
            self.assertEqual(module.processing_next_action(discovery, work)["next_action"], "stage_no_website")
            staging = work / "staging-no-website"
            staging.mkdir()
            (staging / "staging-index.json").write_text(json.dumps({
                "schema_version": module.STAGING_INDEX_SCHEMA,
                "run_id": "RUN-1",
                "complete": True,
                "total": 1,
                "counts": {"company_staged_no_person_required": 1},
                "dispositions": [{"lead_fingerprint": "phone:1", "status": "company_staged_no_person_required", "person_required": False}],
            }))
            self.assertEqual(module.processing_next_action(discovery, work)["next_action"], "init_enrichment")

    def test_processing_next_action_builds_overlay_for_verified_unscored_state(self):
        discovery = {
            "contract_version": "a1.discovery-result.v1",
            "run_id": "RUN-VERIFIED-NEXT",
            "leads": [{
                "lead_fingerprint": "place:verified",
                "business_name": "Verified Association",
                "website": "https://candidate.example/",
            }],
        }
        with tempfile.TemporaryDirectory() as root:
            work = Path(root)
            module.route_discovery(discovery, work)
            state = {
                "schema_version": "a1.website-enrichment-state.v1",
                "run": {"run_id": "RUN-VERIFIED-NEXT"},
                "leads": {
                    "place:verified": {
                        "status": "completed",
                        "enrichment": {
                            "website_status": "verified",
                            "official_website_url": "https://official.example/",
                        },
                        "pipeline_inputs": {},
                        "artifacts": {},
                    }
                },
            }
            (work / "enrichment-state.json").write_text(json.dumps(state))

            action = module.processing_next_action(discovery, work)

            self.assertEqual(action["next_action"], "build_website_overlays")


if __name__ == "__main__":
    unittest.main()
