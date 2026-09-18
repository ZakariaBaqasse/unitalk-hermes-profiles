#!/usr/bin/env python3
"""Regression acceptance for prose People extraction on Quillin About content."""
from __future__ import annotations
import json
from pathlib import Path
from build_official_site_plan import load_json,write_json_atomic
from extract_official_site_observations import extract_observations
from build_website_decision_packet import build_packet
from validate_website_person_observation_proposals import validate_proposals
ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'evaluations/step11/fixtures/firecrawl/quillin-about-fetch.json'
OUT=ROOT/'evaluations/step11/quillin-person-extraction-acceptance.json'
EXPECTED={'Ralph Quillin','Donna Quillin','Rob Windels','Vince Grupposo'}
def main():
 observations=extract_observations(load_json(FIXTURE));preliminary=build_packet(observations)
 block=next(row for row in preliminary['person_evidence_blocks'] if 'Ralph and Donna Quillin' in row['text'] and 'Rob Windels & Vince Grupposo' in row['text'])
 rows=[]
 for pid,name,mention,derivation in [('ralph','Ralph Quillin','Ralph and Donna Quillin','shared_surname_split'),('donna','Donna Quillin','Ralph and Donna Quillin','shared_surname_split'),('rob','Rob Windels','Rob Windels & Vince Grupposo','multiple_full_names'),('vince','Vince Grupposo','Rob Windels & Vince Grupposo','multiple_full_names')]:
  rows.append({'proposal_id':pid,'block_id':block['block_id'],'person_name':name,'source_mention':mention,'derivation':derivation,'role_text':None,'relationship_to_company':'current','company_relationship_evidence':block['text']})
 proposal={'run_id':preliminary['run_id'],'company_id':preliminary['company_id'],'reviewed_block_ids':[row['block_id'] for row in preliminary['person_evidence_blocks']],'proposals':rows}
 augmented=validate_proposals(preliminary,proposal);names={row['observed_name'] for row in augmented.get('candidate_people',[])};false_positive_names=sorted(name for name in names if name not in EXPECTED);checks={'exact_people':names==EXPECTED,'no_product_false_positives':not false_positive_names,'coverage_complete':(augmented.get('person_extraction_coverage') or {}).get('status')=='complete','all_blocks_reviewed':(augmented.get('person_extraction_coverage') or {}).get('reviewed_block_count')==len(preliminary['person_evidence_blocks'])}
 result={'suite':'quillin_person_extraction_acceptance','status':'pass' if all(checks.values()) else 'fail','fixture':str(FIXTURE.relative_to(ROOT)),'checks':checks,'deterministic_candidate_names':sorted({row['observed_name'] for row in observations['candidate_people']}),'validated_candidate_names':sorted(names),'false_positive_names':false_positive_names,'semantic_block_count':len(preliminary['person_evidence_blocks']),'external_calls':0,'external_writes':0}
 write_json_atomic(OUT,result);print(json.dumps(result,indent=2));return 0 if result['status']=='pass' else 1
if __name__=='__main__':raise SystemExit(main())
