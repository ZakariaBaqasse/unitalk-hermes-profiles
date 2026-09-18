#!/usr/bin/env python3
"""Validate the active Twenty workspace against the A2 operational mapping."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import TWENTY_MAPPING,http_json,load_json,sha256_json,twenty_env,write_json_atomic
EXPECTED_TYPES={'a2EnrichmentStatus':'SELECT','a2EnrichmentVersion':'TEXT','a2EnrichmentRunId':'TEXT','a2ProcessingStartedAt':'DATE_TIME','a2LastAttemptedAt':'DATE_TIME','a2LastEnrichedAt':'DATE_TIME','a2NextRetryAt':'DATE_TIME','a2EnrichmentErrorCode':'TEXT','a2IdentityStatus':'SELECT','a2RoleStatus':'SELECT','a2RolePriority':'SELECT','a2CompanyMatchStatus':'SELECT','a2FullenrichPersonid':'TEXT','a2LastVerifiedAt':'DATE_TIME'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--fixture',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();mapping=load_json(TWENTY_MAPPING)
 if a.fixture:payload=load_json(a.fixture);external_calls=0
 else:base,key=twenty_env();payload,_=http_json('GET',base+'/rest/metadata/objects',token=key,retries=1);external_calls=1
 objects={x.get('nameSingular'):x for x in payload.get('data',[])};errors=[];observed={}
 for kind in ['company','person']:
  obj=objects.get(kind)
  if not obj:errors.append(f'missing {kind} object');continue
  fields={x.get('name'):x for x in obj.get('fields',[])};required=set(mapping['objects'][kind]['a2_fields'].values())
  for name in required:
   f=fields.get(name)
   if not f:errors.append(f'{kind}: missing field {name}');continue
   if name in EXPECTED_TYPES and f.get('type')!=EXPECTED_TYPES[name]:errors.append(f'{kind}.{name}: expected {EXPECTED_TYPES[name]}, got {f.get("type")}')
  observed[kind]={'object_id':obj.get('id'),'a2_fields':{name:{'type':fields[name].get('type'),'isUnique':fields[name].get('isUnique'),'options':[x.get('value') for x in (fields[name].get('options') or [])]} for name in required if name in fields}}
 person=observed.get('person',{}).get('a2_fields',{}).get('a2FullenrichPersonid')
 if person and person.get('isUnique') is not True:errors.append('person.a2FullenrichPersonid must be unique')
 for field,expected in [('a2EnrichmentStatus',mapping['company_statuses'])]:
  actual=observed.get('company',{}).get('a2_fields',{}).get(field,{}).get('options')
  if actual!=expected:errors.append(f'company.{field} enum mismatch')
 for key,field in [('identity','a2IdentityStatus'),('role','a2RoleStatus'),('priority','a2RolePriority'),('company_match','a2CompanyMatchStatus'),('enrichment','a2EnrichmentStatus')]:
  actual=observed.get('person',{}).get('a2_fields',{}).get(field,{}).get('options');expected=mapping['person_statuses'][key]
  if actual!=expected:errors.append(f'person.{field} enum mismatch')
 result={'status':'valid' if not errors else 'invalid','mapping_version':mapping['version'],'observed':observed,'metadata_sha256':sha256_json(observed),'external_calls':external_calls,'external_writes':0,'errors':errors};write_json_atomic(a.output,result);print(json.dumps({'status':result['status'],'errors':errors,'output':str(a.output)},indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
