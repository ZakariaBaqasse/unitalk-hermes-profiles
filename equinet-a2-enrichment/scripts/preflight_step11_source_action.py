#!/usr/bin/env python3
"""Preflight Step 11 official-site and Facebook source actions."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import env_value,load_json,make_envelope,write_json_atomic
ROOT=Path(__file__).resolve().parents[1];REGISTER=ROOT/'foundations/contracts/sources/a2-source-register-0.3.2.json'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('request',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();r=load_json(a.request);source=r.get('source_id');mode=r.get('execution_mode','preflight_only');errors=[];blocks=[];warnings=[]
 sources={x['source_id']:x for x in load_json(REGISTER)['sources']}
 if source not in sources:errors.append('unknown source_id')
 if not r.get('company_id') or not r.get('run_id'):errors.append('company_id and run_id required')
 if mode not in {'preflight_only','local_fixture_simulation','live'}:errors.append('unsupported execution_mode')
 if source=='prospect_official_website':
  if not isinstance(r.get('official_url'),str) or not r['official_url'].startswith(('http://','https://')):blocks.append('official_url_required')
  if int(r.get('maximum_pages',5))!=5:blocks.append('maximum_pages_must_equal_five')
  if r.get('agent_web_extract') is True:blocks.append('agent_web_extract_runtime_prohibited')
  if mode=='live' and not env_value('FIRECRAWL_API_KEY'):blocks.append('FIRECRAWL_API_KEY_missing')
  if mode=='live' and r.get('integration_validation_approved') is not True:blocks.append('candidate_specific_integration_validation_approval_required')
 elif source=='apify_facebook_page_contact_information':
  if r.get('official_facebook_link_evidence') is not True:blocks.append('official_website_facebook_link_required')
  if not set(r.get('missing_channels') or []).intersection({'email','phone'}):blocks.append('missing_company_channel_required')
  if int(r.get('actor_calls_per_company',1))!=1:blocks.append('one_actor_call_per_company')
  if int(r.get('automatic_retries',0))!=0:blocks.append('automatic_retry_prohibited')
  if mode=='live':
   if r.get('integration_validation_approved') is not True:blocks.append('candidate_specific_integration_validation_approval_required')
   for key in ['APIFY_API_KEY','APIFY_FACEBOOK_BUILD_ID','APIFY_FACEBOOK_RIGHTS_APPROVED','APIFY_FACEBOOK_LIVE_ENABLED']:
    if not env_value(key):blocks.append(f'{key}_missing')
 else:
  if source in sources:blocks.append('source_not_supported_by_step11_preflight')
 status='invalid' if errors else 'blocked' if blocks else 'allowed_fixture' if mode=='local_fixture_simulation' else 'allowed_live' if mode=='live' else 'preflight_passed';out=make_envelope('a2-step11-source-preflight',r.get('run_id','unknown'),{'source_id':source,'execution_mode':mode,'preflight_status':status,'errors':errors,'blocks':blocks,'warnings':warnings,'external_actions':0},company_id=r.get('company_id'));out['status']=status;write_json_atomic(a.output,out);print(json.dumps({'status':status,'errors':errors,'blocks':blocks,'output':str(a.output)},indent=2));return 1 if errors or blocks else 0
if __name__=='__main__':raise SystemExit(main())
