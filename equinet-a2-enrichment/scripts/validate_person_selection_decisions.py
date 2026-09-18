#!/usr/bin/env python3
"""Validate LLM staged-Search selections, fallback progression and deduplication."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import load_json,normalise_text,write_json_atomic
from classify_a2_target_role_v2 import classify,norm
MATCH={'CONFIRMED','PROBABLE','AMBIGUOUS','MISMATCH'};PRIORITY={'PRIMARY','SECONDARY','REVIEW_ONLY','EXCLUDED','UNKNOWN'}
NEXT={'primary':'owner','owner':'linked_secondary','linked_secondary':'secondary','secondary':'completed_no_target'}
EXPECTED_PRIORITY={'primary':'PRIMARY','owner':'PRIMARY','linked_secondary':'SECONDARY','secondary':'SECONDARY'}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('packet',type=Path);ap.add_argument('decisions',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();packet=load_json(a.packet);dec=load_json(a.decisions);packets={x['company']['twenty_company_id']:x for x in packet.get('packets',[])};errors=[];rows=dec.get('decisions',[]);dec_ids=[x.get('company_id') for x in rows]
 if len(dec_ids)!=len(set(dec_ids)):errors.append('decision company IDs must be unique')
 if set(dec_ids)!=set(packets):errors.append('decisions must cover every and only packet Company')
 validated=[]
 for d in rows:
  cid=d.get('company_id');p=packets.get(cid)
  if not p:errors.append(f'unknown company_id: {cid}');continue
  stage=p.get('search_stage') or packet.get('search_stage') or 'primary';expected=EXPECTED_PRIORITY.get(stage)
  if not expected:errors.append(f'{cid}: invalid search_stage {stage}');continue
  if p.get('search_terminal_status') not in {'succeeded','not_found'}:errors.append(f'{cid}: failed or indeterminate Search cannot progress automatically')
  candidates={x.get('provider_person_id'):x for x in p.get('candidates',[])};selected=d.get('selected_provider_person_ids') or []
  if len(selected)>2 or len(selected)!=len(set(selected)):errors.append(f'{cid}: selected IDs must be unique and at most two')
  existing_ids={x.get('fullenrich_person_id') for x in p.get('existing_people',[]) if x.get('fullenrich_person_id')};existing_urls={x.get('professional_network_url') for x in p.get('existing_people',[]) if x.get('professional_network_url')};existing_names={x.get('normalised_name') for x in p.get('existing_people',[]) if x.get('normalised_name')}
  for cd in d.get('candidate_decisions',[]):
   pid=cd.get('provider_person_id');candidate=candidates.get(pid)
   if not candidate:errors.append(f'{cid}: unknown candidate {pid}');continue
   if cd.get('company_match_status') not in MATCH or cd.get('role_priority') not in PRIORITY:errors.append(f'{cid}/{pid}: invalid status')
   title=candidate.get('exact_current_role');classified=classify({'segment':str(p['company'].get('segment','')).casefold(),'source_role_title':title,'evidence_flags':cd.get('evidence_flags') or []}) if title else {'status':'needs_review'}
   if cd.get('retain'):
    if pid not in selected:errors.append(f'{cid}/{pid}: retained candidate missing from selected IDs')
    if cd.get('company_match_status')!='CONFIRMED' or cd.get('role_priority')!=expected:errors.append(f'{cid}/{pid}: {stage} selection must be confirmed {expected.lower()}')
    if classified.get('status')!='classified' or classified.get('priority')!=expected.casefold():errors.append(f'{cid}/{pid}: active classifier does not classify candidate {expected.lower()}')
    if stage=='owner' and norm(title or '')!='owner':errors.append(f'{cid}/{pid}: owner fallback accepts exact Owner title only')
    if stage=='linked_secondary':
     if not candidate.get('deferred_from_lookup'):errors.append(f'{cid}/{pid}: linked-secondary candidate must originate in validated Lookup')
     if cd.get('duplicate_of_twenty_person_id')!=candidate.get('linked_twenty_person_id'):errors.append(f'{cid}/{pid}: linked-secondary selection must target its exact existing Twenty Person')
    duplicate=pid in existing_ids or candidate.get('professional_network_url') in existing_urls or normalise_text(candidate.get('full_name')) in existing_names
    if duplicate and not cd.get('duplicate_of_twenty_person_id'):errors.append(f'{cid}/{pid}: duplicate requires existing Twenty Person reference')
  if set(selected)!={x.get('provider_person_id') for x in d.get('candidate_decisions',[]) if x.get('retain')}:errors.append(f'{cid}: selected IDs disagree with retain decisions')
  validated.append({**d,'search_stage':stage,'selected_target_priority':expected if selected else None,'next_search_stage':'contact_enrichment' if selected else NEXT[stage]})
 status='valid' if not errors else 'invalid';out={'status':status,'validated_decisions':validated if not errors else [],'search_stage':packet.get('search_stage'),'errors':errors};write_json_atomic(a.output,out);print(json.dumps({'status':status,'errors':len(errors),'output':str(a.output)},indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
