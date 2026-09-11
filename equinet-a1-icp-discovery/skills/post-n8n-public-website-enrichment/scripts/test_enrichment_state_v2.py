#!/usr/bin/env python3
"""Offline unit coverage for enrichment state v2 hardening."""
import copy, importlib.util, sys, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import manage_enrichment as m
import route_and_overlay as r

HANDOFF={"contract_version":"a1.discovery-result.v1","run_id":"run-test","leads":[{"lead_fingerprint":"lead-1","business_name":"Safe Test","website":"https://example.test"}]}
EVIDENCE={"evidence_id":"EV-TEST1","source_url":"https://example.test/about","source_name":"Official","source_type":"official_business_website","retrieved_at":"2026-09-10T00:00:00Z","retrieval_tool":"web_extract","evidence_excerpt":"Professional farrier services.","claim":"Professional farrier services are offered.","fact_or_inference":"direct_fact"}
RESEARCH={"schema_version":m.RESULTS_SCHEMA,"results":[{"lead_id":"lead-1","research_method":"hermes_approved_web_tools","website_status":"verified","official_website_url":"https://example.test","evidence":[EVIDENCE],"missing_information":[],"conflicts":[]}]}

def researched():
    state=m.initialize_state(copy.deepcopy(HANDOFF),max_retries=1); m._validate_state(state)
    state,claim=m.claim_lead(state,"lead-1","tester",60,0,"2026-09-10T00:00:00Z")
    return m.apply_results(state,copy.deepcopy(RESEARCH),"tester",claim["lease_id"],claim["revision"],"2026-09-10T00:00:01Z")

class StateV2Tests(unittest.TestCase):
    def test_verified_without_assessment_is_nonterminal(self):
        state=researched(); self.assertEqual(state["leads"]["lead-1"]["state"],"assessment_pending"); self.assertFalse(m.state_summary(state)["terminal"])
    def test_separate_assessment_preserves_evidence(self):
        state=researched(); before=copy.deepcopy(state["leads"]["lead-1"]["enrichment"])
        rev=state["leads"]["lead-1"]["revision"]; state,claim=m.claim_lead(state,"lead-1","assessor",60,rev,"2026-09-10T00:01:00Z")
        sub={"schema_version":m.ASSESSMENTS_SCHEMA,"submissions":[{"lead_id":"lead-1",
          "classification_decision":{"schema_version":"1.0.0","seed_id":"lead-1","segment":"farrier","prospect_type":"farrier_business","identity_type":"organisation","classification_status":"confirmed","evidence_references":["EV-TEST1"],"rationale":"Official-site evidence identifies a professional farrier business.","unresolved_questions":[]},
          "qualification_assessment":{"schema_version":"1.0.0","segment":"farrier","criterion_assessments":{},"missing_minimum_fields":[]},
          "confidence_assessment":{"schema_version":"1.0.0","method_version":"evidence-confidence-1.0.0","candidate_reference":{"run_id":"run-test","seed_id":"lead-1"},"available_evidence_ids":["EV-TEST1"],
            "dimensions":{name:{"level":"test_level","evidence_ids":["EV-TEST1"],"rationale":"Test evidence."} for name in ("identity_certainty","source_quality","evidence_directness","corroboration","freshness","completeness")},
            "gates":{name:{"value":False,"evidence_ids":[],"rationale":"No gate."} for name in ("mandatory_claim_inference_only","unresolved_identity_conflict","critical_evidence_conflict","minimum_data_failed","blocked_source_used","no_evidence","fabricated_or_untraceable_evidence")},
            "confidence_stage_missing_fields":[]}
        }]}
        state=m.submit_assessment(state,sub,"assessor",claim["lease_id"],claim["revision"],"2026-09-10T00:01:01Z")
        self.assertEqual(state["leads"]["lead-1"]["state"],"ready_to_score"); self.assertEqual(before,state["leads"]["lead-1"]["enrichment"])
    def test_claim_contention_expiry_and_revision_conflict(self):
        state=m.initialize_state(copy.deepcopy(HANDOFF)); m._validate_state(state)
        state,claim=m.claim_lead(state,"lead-1","one",1,0,"2026-09-10T00:00:00Z")
        with self.assertRaisesRegex(ValueError,"revision_conflict"): m.claim_lead(state,"lead-1","two",1,0,"2026-09-10T00:00:00Z")
        with self.assertRaisesRegex(ValueError,"claim_contention"): m.claim_lead(state,"lead-1","two",1,claim["revision"],"2026-09-10T00:00:00Z")
        batch=m.next_batch(state,1,now="2026-09-10T00:00:02Z",phase="research")
        self.assertEqual(batch["items"][0]["revision"],claim["revision"]+1)
        state,new_claim=m.claim_lead(state,"lead-1","two",1,batch["items"][0]["revision"],"2026-09-10T00:00:02Z"); self.assertEqual(new_claim["owner"],"two")
    def test_explicit_exhausted_fallback_and_overlay(self):
        state=researched(); record=state["leads"]["lead-1"]
        record["assessment_attempts"]=2
        record["failure_history"]=[
          {"stage":"assessment","failure_code":"assessment_schema_failure","message":"first failure","attempted_at":"2026-09-10T00:01:00Z","retryable":True},
          {"stage":"assessment","failure_code":"assessment_schema_failure","message":"second failure","attempted_at":"2026-09-10T00:02:00Z","retryable":True},
        ]
        rev=record["revision"]
        fallback={"schema_version":m.FALLBACK_SCHEMA,"lead_id":"lead-1","failure_code":"assessment_schema_failure","attempted_at":"2026-09-10T00:02:00Z","attempts":2,"retries_exhausted":True}
        state=m.explicit_fallback(state,fallback,rev); overlay=r.build_website_overlays(HANDOFF,state)["overlays"][0]
        self.assertEqual(overlay["notes"]["outcome_provenance"]["outcome"],"assessment_failed")
    def test_overlay_rejects_pending(self):
        with self.assertRaisesRegex(ValueError,"not terminal"): r.build_website_overlays(HANDOFF,researched())
    def test_out_of_scope_terminal_requires_evidence(self):
        state=researched(); rev=state["leads"]["lead-1"]["revision"]; state,claim=m.claim_lead(state,"lead-1","a",60,rev,"2026-09-10T00:03:00Z")
        sub={"schema_version":m.ASSESSMENTS_SCHEMA,"submissions":[{"lead_id":"lead-1","classification_decision":{"schema_version":"1.0.0","seed_id":"lead-1","segment":None,"prospect_type":None,"identity_type":"organisation","classification_status":"out_of_scope","evidence_references":["EV-TEST1"],"rationale":"Official evidence places the organisation outside both approved prospect segments.","unresolved_questions":[]},"qualification_assessment":None,"confidence_assessment":None}]}
        state=m.submit_assessment(state,sub,"a",claim["lease_id"],claim["revision"],"2026-09-10T00:03:01Z")
        self.assertEqual(state["leads"]["lead-1"]["state"],"terminal_out_of_scope"); self.assertEqual(r.build_website_overlays(HANDOFF,state)["overlays"][0]["icp_outcome"],"out_of_scope")
    def test_source_coverage_tamper_rejected(self):
        state=m.initialize_state(copy.deepcopy(HANDOFF)); state["leads"]["lead-1"]["lead"]["business_name"]="Tampered"
        with self.assertRaisesRegex(ValueError,"source_sha256"): m._validate_state(state)

if __name__=="__main__": unittest.main(verbosity=2)
