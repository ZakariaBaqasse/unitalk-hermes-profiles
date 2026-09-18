#!/usr/bin/env python3
"""Build the Step 3G preliminary A2-to-HubSpot mapping."""
from __future__ import annotations
import csv,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; C=R/'foundations/contracts/business/a2-business-field-catalogue-0.1.0-draft.1.json'; H=Path('/opt/data/profiles/equinet/attachments/Property_Definitions (1).csv'); O=R/'foundations/contracts/mappings'; J=O/'a2-hubspot-preliminary-mapping-0.1.0-draft.1.json'; V=O/'a2-hubspot-preliminary-mapping-0.1.0-draft.1.csv'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 c=json.loads(C.read_text()); rows=list(csv.DictReader(H.open(encoding='utf-8-sig',newline=''))); idx={(x['Object'].lower(),x['Internal name']):x for x in rows}; mappings=[]
 for f in c['fields']:
  dest=[]
  for m in f['mapping_candidates']:
   x=idx.get((m['object'].lower(),m['property']))
   dest.append({'object':m['object'].title(),'property':m['property'],'metadata_found':bool(x),'hubspot_type':x['Type'] if x else None,'read_only':x['Read only']=='True' if x else None,'unique_lookup':x['Unique lookup property']=='True' if x else None,'enum_options':x['Options (label [value])'] if x else None})
  status='proposed_unverified' if dest else 'canonical_only_no_hubspot_mapping'
  if f['field_key']=='person.personal_email_candidate': status='review_only_no_hubspot_mapping'
  if 'do_not_collect' in f['priority_by_segment'].values(): status='prohibited'
  if f['field_key']=='organisation.horse_count_band': status='mapping_blocked_taxonomy_conflict'
  if f['field_key']=='organisation.stable_type': status='mapping_blocked_enum_mismatch'
  if f['field_key']=='person.professional_credential': dest=[]; status='canonical_only_compatibility_field'
  if f['field_key']=='organisation.disciplines': status='proposed_segment_specific'
  conversion='direct_string'
  if f['field_key']=='person.full_name': conversion='split_first_last_requires_human_review'
  elif f['value_type']=='structured': conversion='multi_property_mapping_required'
  elif f['value_type']=='string_array': conversion='enum_or_multivalue_conversion_pending'
  elif f['value_type']=='enum': conversion='explicit_enum_mapping_required'
  mappings.append({'canonical_field':f['field_key'],'scope':f['scope'],'value_type':f['value_type'],'allowed_segments':f['allowed_segments'],'mapping_status':status,'direction':'read_and_propose_only' if dest else 'canonical_only','hubspot_destinations':dest,'conversion':conversion,'baseline_authority':'hubspot_when_connected_else_validated_input','populated_manual_value':'preserve_and_hold_on_difference','workflow_dependency_status':'unverified' if dest else 'not_applicable','write_authorized':False})
 out={'mapping_id':'equinet-a2-hubspot-preliminary-mapping','version':'0.1.0-draft.1','status':'approved_by_unitalk_as_working_baseline_live_verification_pending','profile':'equinet-a2-enrichment','unitalk_approval':{'approver':'Séverine, Unitalk Operations','approved_at':'2026-08-27T09:09:39Z','scope':'decisions_3G_1_through_3G_10'},'dependencies':[{'path':str(C.relative_to(R)),'sha256':h(C)},{'path':str(H),'sha256':h(H)}],'hubspot_connection':'not_connected','metadata_snapshot_only':True,'global_write_authorized':False,'object_routing':{'person':'Contact','organisation':'Company unless an existing Equinet Contact property is the only confirmed candidate','relationship':'association or reviewed Contact field; exact mapping pending','network':'no mapping'},'known_mapping_blocks':['horse_count_range options overlap','stable_type catalogue includes other but supplied HubSpot options do not','person.full_name split requires human review','farrier_certifications has two possible canonical representations','workflow and list dependencies are not verified','live values, associations and permissions are not verified'],'mappings':mappings,'protected_control_reads':'Use Step 3E protected-field register; read-only visibility does not authorise writes.','approval_gate':{'equinet_confirmation':'pending','live_read_verification':'pending','workflow_dependency_review':'pending','global_write_authorized':False,'next_gate':'Step 4 — Final Specialist SOUL after remaining foundation alignment'}}
 O.mkdir(parents=True,exist_ok=True);J.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 cols=['canonical_field','scope','value_type','allowed_segments','mapping_status','direction','hubspot_destinations','conversion','baseline_authority','populated_manual_value','workflow_dependency_status','write_authorized']
 with V.open('w',encoding='utf-8',newline='') as fh:
  w=csv.DictWriter(fh,fieldnames=cols);w.writeheader()
  for x in mappings:
   y=dict(x);y['allowed_segments']=json.dumps(y['allowed_segments'],separators=(',',':'));y['hubspot_destinations']=json.dumps(y['hubspot_destinations'],separators=(',',':'));w.writerow(y)
 print(json.dumps({'mapping':str(J),'csv':str(V),'fields':len(mappings),'mapped':sum(bool(x['hubspot_destinations']) for x in mappings),'blocked':sum(x['mapping_status'].startswith('mapping_blocked') or x['mapping_status']=='prohibited' for x in mappings)},indent=2))
if __name__=='__main__':main()
