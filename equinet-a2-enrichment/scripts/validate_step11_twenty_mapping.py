#!/usr/bin/env python3
"""Validate Twenty Company contact/social fields required by website-first A2."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import http_json,load_json,twenty_env,write_json_atomic
ROOT=Path(__file__).resolve().parents[1];MAPPING=ROOT/'foundations/contracts/twenty/a2-twenty-operational-mapping-0.1.2.json'
EXPECTED={'domainName':'LINKS','email':'EMAILS','phone':'PHONES','linkedinLink':'LINKS','facebook':'LINKS','instagram':'LINKS','youtube':'LINKS','tiktok':'LINKS','xTwitter':'LINKS'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--fixture',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();mapping=load_json(MAPPING)
 if a.fixture:payload=load_json(a.fixture);calls=0
 else:base,key=twenty_env();payload,_=http_json('GET',base+'/rest/metadata/objects',token=key,retries=1);calls=1
 company=next((x for x in payload.get('data',[]) if x.get('nameSingular')=='company'),None);errors=[];observed={}
 if not company:errors.append('Company metadata missing')
 else:
  fields={x.get('name'):x for x in company.get('fields',[])}
  for name,typ in EXPECTED.items():
   f=fields.get(name)
   if not f:errors.append(f'missing Company field {name}')
   elif f.get('type')!=typ:errors.append(f'Company.{name} expected {typ}, got {f.get("type")}')
   else:observed[name]={'id':f.get('id'),'type':f.get('type'),'isUnique':f.get('isUnique')}
 configured=(mapping.get('objects') or {}).get('company',{}).get('business_fields') or {}
 for key,name in configured.items():
  if name not in EXPECTED:errors.append(f'mapping {key} references unsupported field {name}')
 out={'status':'valid' if not errors else 'invalid','mapping_version':mapping.get('version'),'company_object_id':company.get('id') if company else None,'observed':observed,'external_calls':calls,'external_writes':0,'errors':errors};write_json_atomic(a.output,out);print(json.dumps(out,indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
