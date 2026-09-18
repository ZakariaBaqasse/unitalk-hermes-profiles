#!/usr/bin/env python3
"""Build selected website People batches for Contact Enrichment or direct Twenty proposal."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from urllib.parse import urlsplit
from a2_twenty_fullenrich_common import clean,load_json,make_envelope,split_name,write_json_atomic
def main():
 ap=argparse.ArgumentParser();ap.add_argument('packet',type=Path);ap.add_argument('validation',type=Path);ap.add_argument('--run-id',required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();packet=load_json(a.packet);validation=load_json(a.validation);errors=[]
 if packet.get('company_id')!=validation.get('company_id') or validation.get('status')!='valid':errors.append('packet and valid website decisions must match')
 people={x.get('observation_id'):x for x in packet.get('candidate_people',[])};contacts=validation.get('retained_contacts') or [];by_person={}
 for c in contacts:
  att=c.get('attribution') or {}
  if att.get('entity_type')=='Person':by_person.setdefault(att.get('entity_id'),{})[c.get('contact_type')]=c.get('value')
 retained=validation.get('retained_people') or []
 if len(retained)>2:errors.append('maximum two website People')
 company=packet.get('company') or {};official=packet.get('official_url') or '';domain=(urlsplit(official).hostname or '').removeprefix('www.') if official else company.get('domain');selected=[];complete=[]
 for row in retained:
  oid=row.get('observation_id');source=people.get(oid)
  if not source:errors.append(f'unknown retained website Person {oid}');continue
  display=clean(row.get('name'));comparison=clean(row.get('provider_comparison_name')) or display;first,last=split_name(comparison);channels=by_person.get(oid,{ });email=clean(channels.get('email'));phone=clean(channels.get('phone'));base={'request_id':f'contact-web-{oid}','company_id':packet.get('company_id'),'twenty_person_id':row.get('duplicate_of_twenty_person_id'),'website_person_id':oid,'provider_person_id':None,'full_name':comparison,'source_full_name':display,'first_name':first,'last_name':last,'professional_network_url':None,'company_name':company.get('name'),'company_domain':domain,'source_kind':'existing' if row.get('duplicate_of_twenty_person_id') else 'new','selection_stage':'website','selected_target_priority':row.get('role_priority') or 'UNKNOWN','identity_status':row.get('identity_status') or 'VERIFIED','company_match_status':row.get('company_match_status') or 'CONFIRMED','role_status':row.get('role_status') or 'CURRENT_AT_COMPANY','exact_current_role':row.get('role'),'website_work_email':email,'website_phone':phone,'evidence_refs':row.get('page_evidence') or []}
  (complete if email and phone else selected).append(base)
 status='valid' if not errors else 'invalid';out=make_envelope('a2-website-selected-contact-batch',a.run_id,{'selected_people':selected if not errors else [],'complete_people':complete if not errors else [],'errors':errors});out['status']=status;write_json_atomic(a.output,out);print(json.dumps({'status':status,'contact_enrichment_required':len(selected),'complete_people':len(complete),'errors':errors,'output':str(a.output)},indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
