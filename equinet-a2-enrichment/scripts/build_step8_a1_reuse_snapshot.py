#!/usr/bin/env python3
"""Project approved A1 facts into a conservative Step 8 A2 gap-planning snapshot."""
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def project(record:dict)->dict:
 h=record['source_handoff']['handoff_snapshot'];c=h['candidate_snapshot'];segment=c['segment'];identity=c['identity'];person=identity.get('person');org=identity.get('organisation');states={};values={};evidence_ids={x['evidence_id'] for x in c.get('source_evidence',[])}
 def add(key,value,state='verified',evidence=None):
  if value in (None,'',[]):return
  states[key]={'state':state,'freshness_status':'current'};values[key]={'value':value,'evidence_ids':sorted(evidence or evidence_ids),'origin':'a1_handoff'}
 if org:
  add('organisation.business_name',org.get('name'));add('organisation.website',org.get('website'));add('organisation.website_domain',org.get('domain'))
 location=c.get('location') or {}
 if any(location.get(k) for k in ['country_code','state_region','city','postal_code','public_address']):add('organisation.public_business_location',{k:location.get(k) for k in ['country_code','state_region','city','postal_code','public_address']})
 if person:
  add('person.full_name',person.get('full_name'));add('person.role_title',person.get('role_title'))
 for contact in c.get('public_contacts',[]):
  label=(contact.get('label') or '').casefold();typ=contact.get('contact_type');key=None
  if 'primary named contact' in label and typ=='email':key='person.business_email'
  elif 'primary named contact' in label and typ=='phone':
   # A1 may label a mobile as a named phone; A2 does not operationalise it without explicit business-phone classification.
   continue
  elif 'organisation general contact' in label and typ=='email':key='organisation.business_email'
  elif 'organisation general contact' in label and typ=='phone':key='organisation.business_phone'
  if key:add(key,contact.get('value'),evidence=contact.get('evidence_ids',[]))
 if segment=='horse_owner' and c.get('prospect_type')=='breeding_farm':add('organisation.stable_type','breeding',state='present_unverified')
 if person:
  title=(person.get('role_title') or '').casefold()
  if segment=='farrier' and ('founder' in title or 'owner' in title or 'lead farrier' in title):add('relationship.target_role_priority','primary')
  elif segment=='horse_owner' and ('operating manager' in title or 'operations manager' in title):add('relationship.target_role_priority','secondary',state='present_unverified')
 package=f'{segment}_review_ready';required={'farrier':['person.professional_status','organisation.business_name','organisation.public_business_location','organisation.service_area','organisation.disciplines','person.full_name','person.role_title','relationship.target_role_priority'],'horse_owner':['organisation.business_name','organisation.public_business_location','organisation.stable_type','person.full_name','person.role_title','relationship.target_role_priority']}[segment]
 for key in required:
  states.setdefault(key,{'state':'unknown','freshness_status':'not_assessed'})
 contact_fields=['person.business_email','person.business_phone']
 for key in contact_fields:states.setdefault(key,{'state':'unknown','freshness_status':'not_assessed'})
 result={'projection_version':'0.1.0-draft.1','candidate_id':c['candidate_id'],'segment':segment,'operating_scope':'manual_no_integration_pilot','a2_eligibility_status':'eligible','enrichment_mode':'default_minimum_package','contact_path':'named_target','target_role_not_found':False,'research_exhausted':False,'field_states':states,'reused_a1_values':values,'relationship_state':'proposal_only_requires_evidence_review','package':package,'automatic_rejection':False,'automatic_a1_score_change':False,'external_actions':0}
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('record',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=project(load(a.record));a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'candidate_id':r['candidate_id'],'segment':r['segment'],'reused_fields':len(r['reused_a1_values']),'unknown_fields':sum(v['state']=='unknown' for v in r['field_states'].values()),'external_actions':0,'output':str(a.output)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
