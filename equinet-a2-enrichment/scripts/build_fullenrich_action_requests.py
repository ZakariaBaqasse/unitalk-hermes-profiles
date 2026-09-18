#!/usr/bin/env python3
"""Build validated FullEnrich Lookup or staged Search request batches."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import load_json,make_envelope,write_json_atomic
from classify_a2_target_role_v2 import ALIASES

SEARCH_STAGES=('primary','owner','secondary')

def role_titles(segment,stage):
 groups=ALIASES.get(segment.casefold(),{})
 if stage=='owner':return ['Owner']
 priority='primary' if stage=='primary' else 'secondary'
 titles={x for values in groups.get(priority,{}).values() for x in values}
 # Generic Owner is a separately controlled fallback stage. Keep specific
 # owner titles such as Farm Owner and Stable Owner in the primary stage.
 if stage=='primary':titles={x for x in titles if x.casefold()!='owner'}
 return sorted(titles,key=str.casefold)

def lookup(companies):
 reqs=[];blocked=[]
 for c in companies.get('companies',[]):
  for p in c.get('linked_people',[]):
   item={'request_id':f"lookup-{p.get('twenty_person_id')}",'company_id':c.get('twenty_company_id'),'twenty_person_id':p.get('twenty_person_id'),'person_name':p.get('full_name'),'person_professional_network_url':p.get('professional_network_url'),'company_domain':c.get('domain'),'company_professional_network_url':c.get('professional_network_url')}
   supported=item.get('person_professional_network_url') or (item.get('person_name') and (item.get('company_domain') or item.get('company_professional_network_url')))
   (reqs if supported else blocked).append(item if supported else {**item,'reason':'FullEnrich Lookup requires a Person network identifier or name plus Company domain/network identifier'})
 return reqs,blocked

def _eligible_company_ids(decisions,stage):
 rows=decisions.get('validated_decisions',[])
 if stage=='primary':return {x.get('company_id') for x in rows if x.get('people_search_required')}
 return {x.get('company_id') for x in rows if x.get('next_search_stage')==stage}

def search(companies,decisions,stage):
 if stage not in SEARCH_STAGES:raise ValueError(f'unsupported search stage: {stage}')
 eligible=_eligible_company_ids(decisions,stage);reqs=[];blocked=[]
 for c in companies.get('companies',[]):
  cid=c.get('twenty_company_id')
  if cid not in eligible:continue
  titles=role_titles(str(c.get('segment','')),stage)
  if not titles:
   blocked.append({'company_id':cid,'search_stage':stage,'reason':f'No approved {stage} titles exist for segment {c.get("segment")}'})
   continue
  reqs.append({'request_id':f"search-{stage}-{cid}",'company_id':cid,'company_name':c.get('name'),'domain':c.get('domain'),'company_professional_network_url':c.get('professional_network_url'),'location':c.get('location') or {},'segment':c.get('segment'),'search_stage':stage,'target_priority':'SECONDARY' if stage=='secondary' else 'PRIMARY','target_titles':titles,'limit':1})
 return reqs,blocked

def main():
 ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['lookup','search']);ap.add_argument('companies',type=Path);ap.add_argument('--decisions',type=Path);ap.add_argument('--search-stage',choices=SEARCH_STAGES,default='primary');ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();companies=load_json(a.companies)
 if a.mode=='lookup':reqs,blocked=lookup(companies);stage=None
 else:
  if not a.decisions:raise SystemExit('--decisions is required for search')
  stage=a.search_stage;reqs,blocked=search(companies,load_json(a.decisions),stage)
 out=make_envelope(f'a2-fullenrich-{a.mode}-requests',companies.get('run_id','unknown'),{'search_stage':stage,'requests':reqs,'blocked_requests':blocked});write_json_atomic(a.output,out);print(json.dumps({'status':'valid','search_stage':stage,'requests':len(reqs),'blocked':len(blocked),'output':str(a.output)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
