#!/usr/bin/env python3
"""Build compact LLM decision packets from Twenty and FullEnrich Lookup results."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import load_json,make_envelope,write_json_atomic
def main():
 ap=argparse.ArgumentParser();ap.add_argument('companies',type=Path);ap.add_argument('lookups',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();companies=load_json(a.companies);lookups=load_json(a.lookups);by_person={x.get('twenty_person_id'):x for x in lookups.get('results',[])};packets=[]
 for c in companies.get('companies',[]):
  people=[]
  for p in c.get('linked_people',[]):
   lr=by_person.get(p.get('twenty_person_id'))
   people.append({'twenty_person':p,'lookup_result':lr,'evidence_refs':[f"lookup:{lr.get('request_id')}" if lr else 'twenty_snapshot']})
  packets.append({'company':{k:c.get(k) for k in ['twenty_company_id','name','segment','domain','professional_network_url','location']},'linked_people':people,'decision_required':['identity_status','company_match_status','role_priority','role_status','retain_as_target','secondary_fallback_eligible','people_search_required']})
 out=make_envelope('a2-lookup-decision-packet',companies.get('run_id','unknown'),{'packets':packets});write_json_atomic(a.output,out);print(json.dumps({'status':'valid','packets':len(packets),'output':str(a.output)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
