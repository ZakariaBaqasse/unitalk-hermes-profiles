#!/usr/bin/env python3
"""Run exactly one Exa and one Firecrawl synthetic connectivity call, then restore A2 config."""
from __future__ import annotations
import hashlib,json,os,shutil,urllib.error,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];GLOBAL_ENV=Path('/opt/data/.env');ACTIVE_CONFIG=ROOT/'config.yaml';PROPOSED=ROOT/'evaluations/step8/readiness/config.proposed-bounded-web.yaml';E=ROOT/'evaluations/step8/readiness';BACKUP=E/'config.before-web-smoke.yaml';OUT=E/'web-connectivity-smoke.json'
def sha_bytes(b):return hashlib.sha256(b).hexdigest()
def load_keys():
 vals={k:[] for k in ['EXA_API_KEY','FIRECRAWL_API_KEY']}
 for line in GLOBAL_ENV.read_text(encoding='utf-8').splitlines():
  s=line.strip()
  if not s or s.startswith('#') or '=' not in s:continue
  k,v=s.split('=',1);k=k.removeprefix('export ').strip();v=v.strip().strip('"').strip("'")
  if k in vals:vals[k].append(v)
 for k,v in vals.items():
  if not v or not all(v) or len(set(v))!=1:raise RuntimeError(f'{k} is missing or inconsistent')
 return {k:v[-1] for k,v in vals.items()}, {k:{'occurrences':len(v),'all_identical':len(set(v))==1,'configured':bool(v[-1])} for k,v in vals.items()}
def call(url,payload,headers):
 data=json.dumps(payload).encode();req=urllib.request.Request(url,data=data,headers={'Content-Type':'application/json',**headers},method='POST')
 try:
  with urllib.request.urlopen(req,timeout=30) as resp:return {'http_status':resp.status,'headers':dict(resp.headers),'body':resp.read(1048576)}
 except urllib.error.HTTPError as e:return {'http_status':e.code,'headers':dict(e.headers),'body':e.read(1048576),'error':str(e)}
 except Exception as e:return {'http_status':None,'headers':{},'body':b'','error':f'{type(e).__name__}: {e}'}
def main():
 E.mkdir(parents=True,exist_ok=True);original=ACTIVE_CONFIG.read_bytes();proposed=PROPOSED.read_bytes();BACKUP.write_bytes(original);keys,key_state=load_keys();exa_result=fire_result=None
 try:
  ACTIVE_CONFIG.write_bytes(proposed)
  exa=call('https://api.exa.ai/search',{'query':'site:example.com "Example Domain"','numResults':1,'useAutoprompt':False},{'x-api-key':keys['EXA_API_KEY']})
  try:ej=json.loads(exa['body'])
  except Exception:ej={}
  results=ej.get('results') or []
  exa_result={'request_count':1,'http_status':exa['http_status'],'success':exa['http_status'] is not None and 200<=exa['http_status']<300,'result_count':len(results),'first_result':{'title':results[0].get('title'),'url':results[0].get('url')} if results else None,'cost':ej.get('costDollars','unavailable'),'error':exa.get('error')}
  fire=call('https://api.firecrawl.dev/v1/scrape',{'url':'https://example.com/','formats':['markdown'],'onlyMainContent':True},{'Authorization':'Bearer '+keys['FIRECRAWL_API_KEY']})
  try:fj=json.loads(fire['body'])
  except Exception:fj={}
  data=fj.get('data') or {};markdown=data.get('markdown') or '';meta=data.get('metadata') or {}
  fire_result={'request_count':1,'http_status':fire['http_status'],'success':fire['http_status'] is not None and 200<=fire['http_status']<300 and fj.get('success') is True,'source_url':'https://example.com/','resolved_url':meta.get('sourceURL') or meta.get('url'),'title':meta.get('title'),'markdown_bytes':len(markdown.encode()),'markdown_sha256':sha_bytes(markdown.encode()) if markdown else None,'cost':'unavailable','error':fire.get('error') or fj.get('error')}
 finally:
  ACTIVE_CONFIG.write_bytes(original)
 restored=ACTIVE_CONFIG.read_bytes()==original
 result={'record_type':'step8_synthetic_web_connectivity_smoke','profile':'equinet-a2-enrichment','executed_at':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'scope':'synthetic_connectivity_only','test_target':'example.com','config_activation':{'before_sha256':sha_bytes(original),'proposed_sha256':sha_bytes(proposed),'temporarily_applied':True,'restored':restored,'after_sha256':sha_bytes(ACTIVE_CONFIG.read_bytes())},'credential_checks':key_state,'exa':exa_result,'firecrawl':fire_result,'external_calls':2,'external_actions':0,'real_mustad_or_equinet_data_used':False,'secrets_logged':False,'pass':bool(restored and exa_result and exa_result['success'] and fire_result and fire_result['success']),'next_state':'web_connectivity_validated_not_activated' if restored and exa_result and exa_result['success'] and fire_result and fire_result['success'] else 'connectivity_validation_failed'};OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result,indent=2,ensure_ascii=False));return 0 if result['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
