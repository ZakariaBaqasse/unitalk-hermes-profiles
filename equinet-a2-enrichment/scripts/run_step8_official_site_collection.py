#!/usr/bin/env python3
"""Collect the five approved Step 8 official pages through Firecrawl without model processing."""
from __future__ import annotations
import hashlib,json,urllib.error,urllib.parse,urllib.request,urllib.robotparser
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];ENV=Path('/opt/data/.env');E=ROOT/'evaluations/step8/collection';OUT=E/'collection-manifest.json'
TARGETS={
 'A1-DARLEY-JONABELL-001':['https://www.darleyamerica.com/about-us/kentucky-thoroughbred-horse-farm-tours','https://www.darleyamerica.com/contact-us/united-states/jonabell-farm'],
 'A1-RR-PODIATRY-001':['https://roodandriddle.com/lexington-podiatry-team','https://roodandriddle.com/lexington/','https://www.roodandriddle.com/contact']}
ALLOW={'darleyamerica.com','www.darleyamerica.com','roodandriddle.com','www.roodandriddle.com'}
def sha(b):return hashlib.sha256(b).hexdigest()
def keys():
 vals={k:[] for k in ['EXA_API_KEY','FIRECRAWL_API_KEY']}
 for line in ENV.read_text(encoding='utf-8').splitlines():
  s=line.strip()
  if not s or s.startswith('#') or '=' not in s:continue
  k,v=s.split('=',1);k=k.removeprefix('export ').strip();v=v.strip().strip('"').strip("'")
  if k in vals:vals[k].append(v)
 for k,v in vals.items():
  if not v or len(set(v))!=1 or not v[-1]:raise RuntimeError(f'{k} missing or inconsistent')
 return {k:v[-1] for k,v in vals.items()}
def get(url):
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Unitalk-A2-BoundedPilot/1.0'})
  with urllib.request.urlopen(req,timeout=30) as r:return r.status,r.read(262144).decode('utf-8','replace'),None
 except urllib.error.HTTPError as e:return e.code,e.read(262144).decode('utf-8','replace'),str(e)
 except Exception as e:return None,'',f'{type(e).__name__}: {e}'
def post(url,payload,headers):
 req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json',**headers},method='POST')
 try:
  with urllib.request.urlopen(req,timeout=60) as r:return r.status,r.read(2097152),None
 except urllib.error.HTTPError as e:return e.code,e.read(2097152),str(e)
 except Exception as e:return None,b'',f'{type(e).__name__}: {e}'
def main():
 E.mkdir(parents=True,exist_ok=True);k=keys();robots={};direct_calls=0
 for host in sorted({urllib.parse.urlsplit(u).hostname for urls in TARGETS.values() for u in urls}):
  status,text,error=get(f'https://{host}/robots.txt');direct_calls+=1;rp=urllib.robotparser.RobotFileParser();rp.set_url(f'https://{host}/robots.txt')
  if status==200:rp.parse(text.splitlines());mode='parsed'
  elif status==404:mode='absent_allow_standard'
  else:mode='unavailable_hold_domain'
  robots[host]={'url':f'https://{host}/robots.txt','http_status':status,'mode':mode,'error':error,'content_sha256':sha(text.encode()) if text else None,'parser':rp if status==200 else None}
 records=[];fire_calls=0;exa_calls=0
 for cid,urls in TARGETS.items():
  cdir=E/cid;cdir.mkdir(parents=True,exist_ok=True)
  for index,url in enumerate(urls,1):
   host=urllib.parse.urlsplit(url).hostname;rob=robots[host];allowed=rob['mode']=='absent_allow_standard' or (rob['mode']=='parsed' and rob['parser'].can_fetch('Unitalk-A2-BoundedPilot/1.0',url))
   if not allowed:
    records.append({'candidate_id':cid,'url':url,'robots_allowed':False,'status':'blocked_robots_or_preflight','firecrawl_calls':0,'exa_calls':0});continue
   attempts=[];success=False;data={}
   for attempt in [1,2]:
    if fire_calls>=10:break
    code,body,error=post('https://api.firecrawl.dev/v1/scrape',{'url':url,'formats':['markdown'],'onlyMainContent':True},{'Authorization':'Bearer '+k['FIRECRAWL_API_KEY']});fire_calls+=1
    try:payload=json.loads(body)
    except Exception:payload={}
    data=payload.get('data') or {};success=bool(code and 200<=code<300 and payload.get('success') is True);attempts.append({'attempt':attempt,'http_status':code,'success':success,'error':error or payload.get('error')})
    if success:break
   if not success and exa_calls<2:
    query=f'site:{host} "{cid}" official';code,body,error=post('https://api.exa.ai/search',{'query':query,'numResults':3,'useAutoprompt':False},{'x-api-key':k['EXA_API_KEY']});exa_calls+=1
    try:payload=json.loads(body)
    except Exception:payload={}
    discovery=[{'title':x.get('title'),'url':x.get('url')} for x in (payload.get('results') or [])];discovery_ref={'http_status':code,'success':bool(code and 200<=code<300),'results':discovery,'error':error}
   else:discovery_ref=None
   markdown=data.get('markdown') or '';meta=data.get('metadata') or {};mp=cdir/f'page-{index:02d}.md';meta_path=cdir/f'page-{index:02d}.json'
   if success:mp.write_text(markdown,encoding='utf-8')
   item={'candidate_id':cid,'url':url,'host':host,'robots_allowed':allowed,'status':'collected' if success else 'collection_failed','attempts':attempts,'firecrawl_calls':len(attempts),'exa_calls':1 if discovery_ref else 0,'resolved_url':meta.get('sourceURL') or meta.get('url'),'title':meta.get('title'),'markdown_path':str(mp.relative_to(ROOT)) if success else None,'markdown_bytes':len(markdown.encode()),'markdown_sha256':sha(markdown.encode()) if markdown else None,'discovery_fallback':discovery_ref};meta_path.write_text(json.dumps(item,indent=2,ensure_ascii=False)+'\n');records.append(item)
 result={'record_type':'step8_bounded_official_site_collection','executed_at':datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),'scope':'two_authorised_real_public_business_prospects','candidate_ids':list(TARGETS),'robots_preflight':{h:{k:v for k,v in x.items() if k!='parser'} for h,x in robots.items()},'records':records,'summary':{'targets':5,'collected':sum(x['status']=='collected' for x in records),'blocked':sum(x['status'].startswith('blocked') for x in records),'failed':sum(x['status']=='collection_failed' for x in records),'robots_calls':direct_calls,'firecrawl_calls':fire_calls,'exa_calls':exa_calls},'model_processing':False,'hubspot_calls':0,'twenty_calls':0,'apify_calls':0,'outreach_actions':0,'external_calls':direct_calls+fire_calls+exa_calls,'external_actions':0,'secrets_logged':False,'pass':all(x['status']=='collected' for x in records) and fire_calls<=10 and exa_calls<=2};OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'pass':result['pass'],'summary':result['summary'],'model_processing':False,'external_actions':0,'output':str(OUT)},indent=2));return 0 if result['pass'] else 1
if __name__=='__main__':raise SystemExit(main())
