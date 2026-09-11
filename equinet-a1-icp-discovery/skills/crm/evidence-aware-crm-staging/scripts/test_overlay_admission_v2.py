#!/usr/bin/env python3
from pathlib import Path
import sys
import unittest

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import stage_twenty_rest as rest
import stage_twenty_company as helper

class OverlayAdmissionTests(unittest.TestCase):
    def test_rejects_unexplained_verified_unscored(self):
        value={"overlays":[{"website_status":"verified","enrichment_status":"completed","icp_score_status":"NOT_SCORED","notes":{}}]}
        with self.assertRaisesRegex(ValueError,"explicit exhausted"): rest.reject_unexplained_verified_unscored(value)
    def test_accepts_explicit_exhausted_failure(self):
        value={"overlays":[{"website_status":"verified","enrichment_status":"failed","icp_score_status":"NOT_SCORED","notes":{"outcome_provenance":{"outcome":"assessment_failed","failure_code":"assessment_schema_failure","retries_exhausted":True}}}]}
        rest.reject_unexplained_verified_unscored(value)
    def test_helper_accepts_explicit_exhausted_verified_fallback(self):
        overlay={"schema_version":helper.OVERLAY_SCHEMA,"lead_fingerprint":"fp-1","website_status":"verified","enrichment_status":"failed","official_website_url":"https://example.test","qualification_status":"NOT_CHECKED","icp_score_status":"NOT_SCORED","icp_score":None,"icp_band":None,"icp_outcome":None,"evidence_confidence_score":None,"evidence_confidence_level":None,"notes":{"outcome_provenance":{"outcome":"assessment_failed","failure_code":"assessment_schema_failure","retries_exhausted":True}}}
        helper.validate_overlay(overlay,"fp-1")

    def test_no_site_unchanged(self):
        rest.reject_unexplained_verified_unscored({"overlays":[{"website_status":"unverified","enrichment_status":"not_required_no_website","icp_score_status":"NOT_SCORED","notes":{"fallback_reason":"website_candidate_not_provided"}}]})

if __name__=="__main__": unittest.main(verbosity=2)
