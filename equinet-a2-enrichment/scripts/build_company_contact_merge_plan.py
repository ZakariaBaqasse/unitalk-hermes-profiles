#!/usr/bin/env python3
"""Build a deterministic multi-value Twenty Company contact/social merge plan."""
from __future__ import annotations
import argparse,json,re
from copy import deepcopy
from pathlib import Path
from a2_twenty_fullenrich_common import canonical_url,clean,email_values,link_values,load_json,make_envelope,normalise_phone_key,phone_values,sha256_json,write_json_atomic
FIELDS=('email','phone','linkedinLink','facebook','instagram','youtube','tiktok','xTwitter')
SOCIAL_ALIASES={'linkedin':'linkedinLink','facebook':'facebook','instagram':'instagram','youtube':'youtube','tiktok':'tiktok','x':'xTwitter','twitter':'xTwitter','xTwitter':'xTwitter','linkedinLink':'linkedinLink'}
def empty(field):
 if field=='email':return {'primaryEmail':'','additionalEmails':[]}
 if field=='phone':return {'primaryPhoneNumber':'','primaryPhoneCountryCode':'','primaryPhoneCallingCode':'','additionalPhones':[]}
 return {'primaryLinkUrl':'','primaryLinkLabel':'','secondaryLinks':[]}
def merge_email(base,value):
 out=deepcopy(base) if isinstance(base,dict) else empty('email');value=value.casefold();current=email_values(out)
 if value.casefold() in {x.casefold() for x in current}:return out,'no_change'
 if not clean(out.get('primaryEmail')):out['primaryEmail']=value;out.setdefault('additionalEmails',[]);return out,'set_primary'
 out.setdefault('additionalEmails',[]).append(value);return out,'append_additional'
def merge_phone(base,obs):
 out=deepcopy(base) if isinstance(base,dict) else empty('phone');value=clean(obs.get('value'));current=phone_values(out)
 if normalise_phone_key(value) in {normalise_phone_key(x['number']) for x in current}:return out,'no_change'
 country=clean(obs.get('country_code')) or '';calling=clean(obs.get('calling_code')) or ''
 if not clean(out.get('primaryPhoneNumber')):out.update({'primaryPhoneNumber':value,'primaryPhoneCountryCode':country,'primaryPhoneCallingCode':calling});out.setdefault('additionalPhones',[]);return out,'set_primary'
 out.setdefault('additionalPhones',[]).append({'number':value,'countryCode':country,'callingCode':calling});return out,'append_additional'
def merge_link(base,obs,field):
 out=deepcopy(base) if isinstance(base,dict) else empty(field);value=canonical_url(obs.get('value'));current=link_values(out)
 if value in {canonical_url(x['url']) for x in current}:return out,'no_change'
 label=clean(obs.get('label')) or field
 if not clean(out.get('primaryLinkUrl')):out.update({'primaryLinkUrl':value,'primaryLinkLabel':label});out.setdefault('secondaryLinks',[]);return out,'set_primary'
 out.setdefault('secondaryLinks',[]).append({'url':value,'label':label});return out,'append_additional'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('request',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();req=load_json(a.request);baseline=req.get('baseline') or {};merged={f:deepcopy(baseline.get(f) or empty(f)) for f in FIELDS};decisions=[];errors=[]
 for i,obs in enumerate(req.get('observations') or []):
  if not isinstance(obs,dict) or obs.get('accepted') is not True:continue
  raw_field=obs.get('field');field=SOCIAL_ALIASES.get(raw_field,raw_field);value=clean(obs.get('value'));refs=obs.get('evidence_refs') or []
  if field not in FIELDS:errors.append(f'observation[{i}] unsupported field {raw_field}');continue
  if not value or not refs:errors.append(f'observation[{i}] requires value and evidence_refs');continue
  if field=='email':
   if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value):errors.append(f'observation[{i}] invalid email');continue
   merged[field],action=merge_email(merged[field],value)
  elif field=='phone':
   if len(re.sub(r'\D','',value))<7:errors.append(f'observation[{i}] invalid phone');continue
   merged[field],action=merge_phone(merged[field],obs)
  else:
   if not canonical_url(value).startswith(('http://','https://')):errors.append(f'observation[{i}] invalid URL');continue
   merged[field],action=merge_link(merged[field],obs,field)
  decisions.append({'field':field,'source':obs.get('source'),'source_url':obs.get('source_url'),'canonical_value':value.casefold() if field=='email' else canonical_url(value) if field not in {'phone'} else value,'action':action,'evidence_refs':refs})
 changed={f:v for f,v in merged.items() if sha256_json(v)!=sha256_json(baseline.get(f) or empty(f))}
 status='valid' if not errors else 'invalid';out=make_envelope('a2-company-contact-merge-plan',req.get('run_id','unknown'),{'company_id':req.get('company_id'),'baseline_sha256':sha256_json(baseline),'company_field_updates':changed if not errors else {},'merged_fields':merged if not errors else {},'decisions':decisions if not errors else [],'provenance':req.get('provenance') or [],'external_actions':0,'errors':errors});out['status']=status;write_json_atomic(a.output,out);print(json.dumps({'status':status,'updated_fields':sorted(changed) if not errors else [],'errors':errors,'output':str(a.output)},indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
