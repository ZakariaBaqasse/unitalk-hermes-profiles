#!/usr/bin/env python3
"""Build compact FullEnrich staged-Search candidate packets for LLM selection."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import load_json,make_envelope,normalise_text,write_json_atomic

def main():
 ap=argparse.ArgumentParser();ap.add_argument('companies',type=Path);ap.add_argument('search_results',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();companies=load_json(a.companies);results=load_json(a.search_results);by_company={x.get('company_id'):x for x in results.get('results',[])};packets=[];envelope_stage=results.get('search_stage') or 'primary'
 for c in companies.get('companies',[]):
  sr=by_company.get(c.get('twenty_company_id'))
  if not sr:continue
  existing=[]
  for p in c.get('linked_people',[]):existing.append({'twenty_person_id':p.get('twenty_person_id'),'fullenrich_person_id':p.get('fullenrich_person_id'),'professional_network_url':p.get('professional_network_url'),'normalised_name':normalise_text(p.get('full_name'))})
  stage=sr.get('search_stage') or envelope_stage
  packets.append({'company':{k:c.get(k) for k in ['twenty_company_id','name','segment','domain','professional_network_url','location']},'search_stage':stage,'target_priority':sr.get('target_priority') or ('SECONDARY' if stage=='secondary' else 'PRIMARY'),'target_titles':sr.get('target_titles') or [],'existing_people':existing,'search_terminal_status':sr.get('terminal_status'),'candidates':sr.get('candidates',[]),'evidence_ref':f"search:{sr.get('request_id')}"})
 out=make_envelope('a2-search-candidate-packet',companies.get('run_id','unknown'),{'search_stage':envelope_stage,'packets':packets});write_json_atomic(a.output,out);print(json.dumps({'status':'valid','search_stage':envelope_stage,'packets':len(packets),'output':str(a.output)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
