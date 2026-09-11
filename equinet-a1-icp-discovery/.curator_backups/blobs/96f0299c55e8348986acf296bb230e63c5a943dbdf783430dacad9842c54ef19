#!/usr/bin/env python3
import copy, importlib.util, sys, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("migrate",HERE/"migrate_state_v1_to_v2.py"); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
import manage_enrichment as m

class MigrationTests(unittest.TestCase):
    def test_v1_mapping_preserves_hash_and_evidence(self):
        handoff={"contract_version":"a1.discovery-result.v1","run_id":"r","leads":[{"lead_fingerprint":"a"},{"lead_fingerprint":"b"},{"lead_fingerprint":"c"}]}
        old={"schema_version":mod.V1,"source_contract_version":"a1.discovery-result.v1","source_sha256":m.canonical_sha256(handoff),"run":{"run_id":"r"},"discovery_result":{"contract_version":"a1.discovery-result.v1","run_id":"r"},"max_retries":1,"leads":{
          "a":{"lead":handoff["leads"][0],"status":"completed","attempts":1,"failure_history":[],"enrichment":{"website_status":"verified","official_website_url":"https://a.test","evidence":[{"evidence_id":"EV-AAA"}]},"pipeline_inputs":{},"artifacts":{}},
          "b":{"lead":handoff["leads"][1],"status":"completed","attempts":1,"failure_history":[],"enrichment":{"website_status":"none_found","official_website_url":None,"evidence":[]},"pipeline_inputs":{},"artifacts":{}},
          "c":{"lead":handoff["leads"][2],"status":"completed","attempts":1,"failure_history":[],"enrichment":{"website_status":"verified","official_website_url":"https://c.test","evidence":[{"evidence_id":"EV-CCC"}]},"pipeline_inputs":{"classification_decision":{},"qualification_assessment":{},"confidence_assessment":{}},"artifacts":{}}}}
        new=mod.migrate(copy.deepcopy(old),"2026-09-10T00:00:00Z")
        self.assertEqual(new["source_sha256"],old["source_sha256"]); self.assertEqual(new["leads"]["a"]["state"],"assessment_pending"); self.assertEqual(new["leads"]["b"]["state"],"terminal_none_found"); self.assertEqual(new["leads"]["c"]["state"],"ready_to_score"); self.assertEqual(new["leads"]["a"]["enrichment"],old["leads"]["a"]["enrichment"])

if __name__=="__main__": unittest.main(verbosity=2)
