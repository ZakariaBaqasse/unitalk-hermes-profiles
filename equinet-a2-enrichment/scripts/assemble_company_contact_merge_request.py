#!/usr/bin/env python3
"""Assemble one Company merge request from Twenty baseline and validated website/Facebook evidence."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import load_json,write_json_atomic
PLATFORM={'linkedin':'linkedinLink','facebook':'facebook','instagram':'instagram','youtube':'youtube','tiktok':'tiktok','x':'xTwitter'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('companies',type=Path);ap.add_argument('website_validation',type=Path);ap.add_argument('--apify-results',type=Path);ap.add_argument('--company-id',required=True);ap.add_argument('--run-id',required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();companies=load_json(a.companies);web=load_json(a.website_validation);errors=[]
 company=next((x for x in companies.get('companies',[]) if x.get('twenty_company_id')==a.company_id),None)
 if not company:errors.append('Company not found in baseline')
 if web.get('status')!='valid' or web.get('company_id')!=a.company_id:errors.append('valid matching website decisions required')
 observations=[]
 for x in web.get('retained_contacts',[]):
  if (x.get('attribution') or {}).get('entity_type')!='Company':continue
  ev=x.get('page_evidence') or [];observations.append({'field':x.get('contact_type'),'value':x.get('value'),'accepted':True,'source':'prospect_official_website','source_url':ev[0].get('page_url') if ev else None,'evidence_refs':[x.get('observation_id')]})
 for x in web.get('retained_social_links',[]):
  ev=x.get('page_evidence') or [];field=PLATFORM.get(x.get('platform'))
  if field:observations.append({'field':field,'value':x.get('url'),'label':x.get('platform','').title(),'accepted':True,'source':'prospect_official_website','source_url':ev[0].get('page_url') if ev else None,'evidence_refs':[x.get('observation_id')]})
 if a.apify_results:
  apify=load_json(a.apify_results)
  if apify.get('status')!='valid':errors.append('Apify results are not valid')
  for x in apify.get('append_candidates',[]):
   if x.get('company_id')!=a.company_id:continue
   field='email' if x.get('field_key')=='company.company_email' else 'phone' if x.get('field_key')=='company.company_phone' else None
   if field:observations.append({'field':field,'value':x.get('value'),'accepted':True,'source':'apify_facebook_page_contact_information','source_url':x.get('source_url'),'evidence_refs':[x.get('candidate_id')]})
 baseline=(company or {}).get('company_contact_composites') or {};out={'run_id':a.run_id,'company_id':a.company_id,'baseline':baseline,'observations':observations,'errors':errors}
 write_json_atomic(a.output,out);print(json.dumps({'status':'valid' if not errors else 'invalid','observations':len(observations),'errors':errors,'output':str(a.output)},indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
