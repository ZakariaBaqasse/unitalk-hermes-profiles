#!/usr/bin/env python3
"""Build a safe explicit Twenty write plan from validated resolved People."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import load_json,make_envelope,split_name,utc_now,write_json_atomic
BUSINESS_ACTIONS={'add','update_a2_owned','no_change','preserve_manual','hold_conflict','privacy_review','reject_invalid'}
ROLE_RELATIONSHIPS={'CURRENT_AT_COMPANY','NOT_CURRENT_AT_COMPANY','UNVERIFIED'}
WEBSITE_PRIORITIES={'PRIMARY','SECONDARY','REVIEW_ONLY','UNKNOWN'}
COMPANY_BUSINESS_FIELDS={'email','phone','linkedinLink','facebook','instagram','youtube','tiktok','xTwitter'}
def composite_email(value):return {'primaryEmail':value,'additionalEmails':[]}
def composite_emails(values):
 out=[]
 for x in values or []:
  v=x.get('value') if isinstance(x,dict) else x
  if isinstance(v,str) and v.strip() and v.strip().casefold() not in {y.casefold() for y in out}:out.append(v.strip().casefold())
 return {'primaryEmail':out[0] if out else '','additionalEmails':out[1:]}
def composite_phone(value,region=None):return {'primaryPhoneNumber':value,'primaryPhoneCountryCode':region or '', 'primaryPhoneCallingCode':'','additionalPhones':[]}
def composite_phones(values):
 out=[]
 for x in values or []:
  if isinstance(x,dict):v=x.get('value') or x.get('number');country=x.get('region') or x.get('countryCode') or '';calling=x.get('callingCode') or ''
  else:v=x;country='';calling=''
  key=''.join(ch for ch in str(v or '') if ch.isdigit() or ch=='+')
  if v and key not in {''.join(ch for ch in y['number'] if ch.isdigit() or ch=='+') for y in out}:out.append({'number':str(v),'countryCode':country,'callingCode':calling})
 if not out:return {'primaryPhoneNumber':'','primaryPhoneCountryCode':'','primaryPhoneCallingCode':'','additionalPhones':[]}
 first=out[0];return {'primaryPhoneNumber':first['number'],'primaryPhoneCountryCode':first['countryCode'],'primaryPhoneCallingCode':first['callingCode'],'additionalPhones':out[1:]}

def composite_link(value):return {'primaryLinkUrl':value,'primaryLinkLabel':'LinkedIn','secondaryLinks':[]}
def allowed_value(person,key):
 value=person.get(key)
 if isinstance(value,dict):return value.get('value')
 return value
def provider_work_email(person):
 value=person.get('work_email')
 if isinstance(value,dict) and value.get('value'):
  return value
 for item in person.get('merged_work_emails') or []:
  if isinstance(item,dict) and item.get('value') and (item.get('source')=='fullenrich_contact_enrichment' or item.get('provider_status') is not None):return item
 return None
def provider_email_status(person):
 email=provider_work_email(person)
 candidates=[person.get('fullenrich_email_status'),person.get('work_email_status'),person.get('business_email_status')]
 if isinstance(email,dict):candidates.extend([email.get('provider_status'),email.get('status')])
 for value in candidates:
  if isinstance(value,str) and value.strip():
   status=value.strip()
   if len(status)>100 or any(ch in status for ch in '\r\n\x00'):raise ValueError('FullEnrich email status must be bounded plain text')
   return status
 return 'unknown' if email else None
def main():
 ap=argparse.ArgumentParser();ap.add_argument('proposal',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();req=load_json(a.proposal);errors=[];ops=[];expected_people=[];cid=req.get('company_id');run_id=req.get('run_id');expected_company={}
 merge=req.get('company_merge') or {}
 updates=merge.get('company_field_updates') or {}
 if updates:
  bad=set(updates)-COMPANY_BUSINESS_FIELDS
  if bad:errors.append(f'unsupported Company business fields: {sorted(bad)}')
  elif not merge.get('baseline_sha256') or not isinstance(merge.get('baseline'),dict):errors.append('Company merge requires baseline and baseline_sha256')
  else:
   ops.append({'operation_id':'update-company-business-fields','operation_type':'update_company_fields','twenty_company_id':cid,'baseline_sha256':merge.get('baseline_sha256'),'baseline_fields':merge.get('baseline'),'fields':updates})
   expected_company.update(updates)
 for index,p in enumerate(req.get('resolved_people') or []):
  decisions=p.get('field_decisions') or {}
  if any(x not in BUSINESS_ACTIONS for x in decisions.values()):errors.append(f'person[{index}] has invalid field decision');continue
  if p.get('personal_email_candidate') and decisions.get('personal_email_candidate') in {'add','update_a2_owned'}:errors.append(f'person[{index}] cannot auto-write personal email')
  statuses=p.get('statuses') or {}
  try:provider_email=provider_work_email(p);email_status=provider_email_status(p)
  except ValueError as exc:errors.append(f'person[{index}] {exc}');continue
  if provider_email and not email_status:errors.append(f'person[{index}] FullEnrich work email requires its provider-returned status');continue
  if statuses.get('role') not in ROLE_RELATIONSHIPS:errors.append(f'person[{index}] has invalid role relationship status');continue
  if statuses.get('role')=='CURRENT_AT_COMPANY' and statuses.get('company_match')!='CONFIRMED':errors.append(f'person[{index}] CURRENT_AT_COMPANY requires CONFIRMED company match');continue
  if statuses.get('role')=='NOT_CURRENT_AT_COMPANY' and statuses.get('company_match')!='MISMATCH':errors.append(f'person[{index}] NOT_CURRENT_AT_COMPANY requires MISMATCH company match');continue
  if p.get('selection_stage')=='linked_secondary' and not (p.get('source_kind')=='existing' and statuses.get('priority')=='SECONDARY' and statuses.get('identity')=='VERIFIED' and statuses.get('role')=='CURRENT_AT_COMPANY' and statuses.get('company_match')=='CONFIRMED'):
   errors.append(f'person[{index}] linked-secondary fallback must update the verified existing SECONDARY Person');continue
  fields={'a2IdentityStatus':statuses.get('identity'),'a2RoleStatus':statuses.get('role'),'a2RolePriority':statuses.get('priority'),'a2CompanyMatchStatus':statuses.get('company_match'),'a2EnrichmentStatus':statuses.get('enrichment'),'a2FullenrichPersonid':p.get('provider_person_id'),'a2LastVerifiedAt':p.get('verified_at') or utc_now(),'a2LastEnrichedAt':p.get('enriched_at') or utc_now(),'a2EnrichmentRunId':run_id}
  fields={k:v for k,v in fields.items() if v is not None}
  if p.get('source_kind')=='new':
   selection_stage=p.get('selection_stage')
   allowed_selection=(statuses.get('priority')=='PRIMARY' and selection_stage in {'primary','owner'}) or (statuses.get('priority')=='SECONDARY' and selection_stage=='secondary') or (selection_stage=='website' and statuses.get('priority') in WEBSITE_PRIORITIES)
   if not (statuses.get('identity')=='VERIFIED' and statuses.get('role')=='CURRENT_AT_COMPANY' and statuses.get('company_match')=='CONFIRMED' and allowed_selection):errors.append(f'person[{index}] new Person must be verified, current at Company, Company-confirmed, and have a stage-consistent Search or website selection');continue
   first,last=p.get('first_name'),p.get('last_name')
   if not first:first,last=split_name(p.get('full_name'))
   if not first:errors.append(f'person[{index}] requires name');continue
   fields['name']={'firstName':first,'lastName':last or ''}
   if allowed_value(p,'exact_current_role'):fields['jobTitle']=allowed_value(p,'exact_current_role')
   if p.get('merged_work_emails'):fields['emails']=composite_emails(p.get('merged_work_emails'))
   elif allowed_value(p,'work_email'):fields['emails']=composite_email(allowed_value(p,'work_email'))
   if provider_email and email_status:fields['emailStatus']=email_status
   if p.get('merged_phones'):fields['phones']=composite_phones(p.get('merged_phones'))
   elif allowed_value(p,'mobile_phone'):fields['phones']=composite_phone(allowed_value(p,'mobile_phone'),(p.get('mobile_phone') or {}).get('region') if isinstance(p.get('mobile_phone'),dict) else None)
   if allowed_value(p,'professional_network_url'):fields['linkedinLink']=composite_link(allowed_value(p,'professional_network_url'))
   source_person_id=p.get('provider_person_id') or p.get('website_person_id') or f'website-{index}'
   temp=f"new-{index}-{source_person_id}";ops.append({'operation_id':f'create-person-{index}','operation_type':'create_person','temporary_person_key':temp,'source_provider_person_id':p.get('provider_person_id'),'source_website_person_id':p.get('website_person_id'),'fields':fields});ops.append({'operation_id':f'associate-person-{index}','operation_type':'associate_person_company','temporary_person_key':temp,'twenty_company_id':cid,'fields':{}});expected_people.append({'temporary_person_key':temp,'fields':fields})
  else:
   pid=p.get('twenty_person_id')
   if not pid:errors.append(f'person[{index}] existing Person requires twenty_person_id');continue
   if p.get('merged_work_emails'):fields['emails']=composite_emails(p.get('merged_work_emails'))
   if p.get('merged_phones'):fields['phones']=composite_phones(p.get('merged_phones'))
   mapping={'exact_current_role':('jobTitle',lambda v:v),'work_email':('emails',composite_email),'mobile_phone':('phones',lambda v:composite_phone(v,(p.get('mobile_phone') or {}).get('region') if isinstance(p.get('mobile_phone'),dict) else None)),'professional_network_url':('linkedinLink',composite_link)}
   for key,(target,convert) in mapping.items():
    if key=='work_email' and p.get('merged_work_emails'):continue
    if key=='mobile_phone' and p.get('merged_phones'):continue
    if decisions.get(key) in {'add','update_a2_owned'} and allowed_value(p,key):fields[target]=convert(allowed_value(p,key))
   if provider_email:
    if 'emails' not in fields:errors.append(f'person[{index}] FullEnrich work email must be retained in Twenty');continue
    fields['emailStatus']=email_status
   ops.append({'operation_id':f'update-person-{index}','operation_type':'update_person','twenty_person_id':pid,'fields':fields});expected_people.append({'twenty_person_id':pid,'fields':fields})
 final=req.get('company_final_status')
 if final not in {'ENRICHED','PARTIALLY_ENRICHED','COMPLETED_NO_TARGET','RETRYABLE_ERROR','BLOCKED'}:errors.append('invalid company_final_status')
 company_fields={'a2EnrichmentStatus':final,'a2EnrichmentVersion':req.get('enrichment_version','0.1.0'),'a2EnrichmentRunId':run_id,'a2LastAttemptedAt':utc_now(),'a2EnrichmentErrorCode':req.get('error_code')}
 if final=='ENRICHED':company_fields['a2LastEnrichedAt']=utc_now();company_fields['a2NextRetryAt']=None
 ops.append({'operation_id':'final-company-status','operation_type':'update_company_status','twenty_company_id':cid,'fields':company_fields})
 status='valid' if not errors else 'invalid';expected_company.update(company_fields);plan=make_envelope('a2-twenty-write-plan',run_id,{'company_id':cid,'operations':ops if not errors else [],'expected_read_back':{'company_fields':expected_company,'people':expected_people},'errors':errors});plan['status']=status;write_json_atomic(a.output,plan);print(json.dumps({'status':status,'operations':len(plan['operations']),'errors':errors,'output':str(a.output)},indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
