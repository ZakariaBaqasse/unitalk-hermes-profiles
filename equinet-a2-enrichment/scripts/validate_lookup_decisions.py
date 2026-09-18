#!/usr/bin/env python3
"""Validate LLM Lookup decisions and deferred linked-secondary fallbacks."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import load_json,write_json_atomic
from classify_a2_target_role_v2 import classify
IDENTITY={'VERIFIED','AMBIGUOUS','CONFLICT','NOT_FOUND'};MATCH={'CONFIRMED','PROBABLE','AMBIGUOUS','MISMATCH'};PRIORITY={'PRIMARY','SECONDARY','REVIEW_ONLY','EXCLUDED','UNKNOWN'};ROLE={'CURRENT_AT_COMPANY','NOT_CURRENT_AT_COMPANY','UNVERIFIED'}
SECOND_CONTACT_REASONS={'large_organisation','shared_purchasing_or_operational_responsibility'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('packet',type=Path);ap.add_argument('decisions',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();packet=load_json(a.packet);dec=load_json(a.decisions);companies={x['company']['twenty_company_id']:x for x in packet.get('packets',[])};errors=[];rows=dec.get('decisions',[]);ids=[x.get('company_id') for x in rows]
 if len(ids)!=len(set(ids)):errors.append('decision company IDs must be unique')
 if set(ids)!=set(companies):errors.append('decisions must cover every and only packet Company')
 validated=[]
 for d in rows:
  cid=d.get('company_id');source=companies.get(cid)
  if not source:errors.append(f'unknown company_id: {cid}');continue
  known={x['twenty_person'].get('twenty_person_id'):x for x in source.get('linked_people',[])};person_rows=d.get('person_decisions',[]);person_ids=[x.get('twenty_person_id') for x in person_rows]
  if len(person_ids)!=len(set(person_ids)):errors.append(f'{cid}: person decisions must be unique')
  if set(person_ids)!=set(known):errors.append(f'{cid}: person decisions must cover every linked Person')
  usable_primary=0;fallback_count=0
  for pd in person_rows:
   pid=pd.get('twenty_person_id');item=known.get(pid)
   if not item:errors.append(f'{cid}: unknown twenty_person_id {pid}');continue
   for key,allowed in [('identity_status',IDENTITY),('company_match_status',MATCH),('role_priority',PRIORITY),('role_status',ROLE)]:
    if pd.get(key) not in allowed:errors.append(f'{cid}/{pid}: invalid {key}')
   if not isinstance(pd.get('secondary_fallback_eligible'),bool):errors.append(f'{cid}/{pid}: secondary_fallback_eligible must be boolean')
   lookup=item.get('lookup_result') or {};person=lookup.get('person') or {};title=person.get('exact_current_role')
   if title and pd.get('role_priority')!='UNKNOWN':
    classified=classify({'segment':str(source['company'].get('segment','')).casefold(),'source_role_title':title,'evidence_flags':pd.get('evidence_flags') or []})
    if classified.get('status')=='classified' and classified.get('priority','').upper()!=pd.get('role_priority'):errors.append(f'{cid}/{pid}: role priority disagrees with active classifier')
   if pd.get('role_status')=='CURRENT_AT_COMPANY' and pd.get('company_match_status')!='CONFIRMED':errors.append(f'{cid}/{pid}: CURRENT_AT_COMPANY requires CONFIRMED company match')
   if pd.get('role_status')=='NOT_CURRENT_AT_COMPANY' and pd.get('company_match_status')!='MISMATCH':errors.append(f'{cid}/{pid}: NOT_CURRENT_AT_COMPANY requires MISMATCH company match')
   if pd.get('retain_as_target'):
    if not (pd.get('identity_status')=='VERIFIED' and pd.get('company_match_status')=='CONFIRMED' and pd.get('role_priority')=='PRIMARY' and pd.get('role_status')=='CURRENT_AT_COMPANY'):errors.append(f'{cid}/{pid}: retained target must be verified confirmed current primary')
    else:usable_primary+=1
   if pd.get('secondary_fallback_eligible'):
    if pd.get('retain_as_target'):errors.append(f'{cid}/{pid}: primary retention and secondary fallback are mutually exclusive')
    if not (pd.get('identity_status')=='VERIFIED' and pd.get('company_match_status')=='CONFIRMED' and pd.get('role_priority')=='SECONDARY' and pd.get('role_status')=='CURRENT_AT_COMPANY' and person.get('provider_person_id')):errors.append(f'{cid}/{pid}: linked secondary fallback must be provider-resolved, verified, Company-confirmed, current and SECONDARY')
    else:fallback_count+=1
  if usable_primary>2:errors.append(f'{cid}: at most two primary contacts may be retained')
  if fallback_count>2:errors.append(f'{cid}: at most two linked secondary fallbacks may be eligible')
  if fallback_count>1 and d.get('secondary_fallback_second_contact_reason') not in SECOND_CONTACT_REASONS:errors.append(f'{cid}: a second linked secondary fallback requires an approved reason')
  if bool(d.get('people_search_required'))==(usable_primary>0):errors.append(f'{cid}: people_search_required inconsistent with usable primary contacts')
  validated.append({**d,'linked_secondary_fallback_count':fallback_count})
 status='valid' if not errors else 'invalid';out={'status':status,'validated_decisions':validated if not errors else [],'errors':errors};write_json_atomic(a.output,out);print(json.dumps({'status':status,'errors':len(errors),'output':str(a.output)},indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
