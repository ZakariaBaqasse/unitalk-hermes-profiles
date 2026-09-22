#!/usr/bin/env python3
"""Shared helpers for the Twenty–FullEnrich A2 integration."""
from __future__ import annotations
import hashlib,json,os,re,tempfile,time,urllib.error,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
TWENTY_MAPPING=ROOT/'foundations/contracts/twenty/a2-twenty-operational-mapping-0.1.3.json'
FULLENRICH_CONTRACT=ROOT/'foundations/contracts/integrations/a2-fullenrich-direct-integration-0.1.4.json'
STATE_MODEL=ROOT/'foundations/contracts/runtime/a2-twenty-fullenrich-state-model-0.1.6.json'
FIRECRAWL_CONTRACT=ROOT/'foundations/contracts/integrations/a2-official-website-firecrawl-integration-0.1.0.json'
APIFY_FACEBOOK_CONTRACT=ROOT/'foundations/contracts/integrations/a2-apify-facebook-page-contact-integration-0.1.0.json'
class IntegrationError(RuntimeError):
 def __init__(self,message:str,*,status:int|None=None,code:str|None=None,payload:Any=None):
  super().__init__(message);self.status=status;self.code=code;self.payload=payload

def utc_now()->str:return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def load_json(path:Path)->Any:
 def no_dupes(pairs):
  out={}
  for k,v in pairs:
   if k in out:raise ValueError(f'duplicate JSON key: {k}')
   out[k]=v
  return out
 return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=no_dupes)
def canonical_bytes(value:Any)->bytes:return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def sha256_json(value:Any)->str:return hashlib.sha256(canonical_bytes(value)).hexdigest()
def write_json_atomic(path:Path,value:Any)->None:
 path.parent.mkdir(parents=True,exist_ok=True);text=json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
 with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as h:h.write(text);tmp=Path(h.name)
 tmp.replace(path)
def clean(value:Any)->str|None:
 if not isinstance(value,str):return None
 value=value.strip();return value or None
def env_value(name:str)->str|None:
 value=clean(os.getenv(name))
 if value:return value
 env_path=ROOT/'.env'
 if not env_path.is_file():return None
 for raw in env_path.read_text(encoding='utf-8').splitlines():
  line=raw.strip()
  if not line or line.startswith('#') or '=' not in line:continue
  key,candidate=line.split('=',1)
  if key.strip()!=name:continue
  candidate=candidate.strip()
  if len(candidate)>=2 and candidate[0]==candidate[-1] and candidate[0] in {'"',"'"}:candidate=candidate[1:-1]
  return clean(candidate)
 return None
def nested(value:Any,*keys:str)->Any:
 cur=value
 for key in keys:
  if not isinstance(cur,dict):return None
  cur=cur.get(key)
 return cur
def link_url(value:Any)->str|None:return clean(nested(value,'primaryLinkUrl'))
def domain_name(value:Any)->str|None:
 value=clean(value)
 if not value:return None
 parsed=urllib.parse.urlparse(value if '://' in value else '//'+value)
 host=(parsed.hostname or value.split('/')[0]).casefold().strip('.')
 return host[4:] if host.startswith('www.') else host
def primary_email(value:Any)->str|None:
 v=clean(nested(value,'primaryEmail'));return v.casefold() if v else None
def primary_phone(value:Any)->str|None:return clean(nested(value,'primaryPhoneNumber'))
def email_values(value:Any)->list[str]:
 if not isinstance(value,dict):return []
 out=[]
 for item in [value.get('primaryEmail'),*(value.get('additionalEmails') or [])]:
  candidate=clean(item.get('email')) if isinstance(item,dict) else clean(item)
  if candidate and candidate.casefold() not in {x.casefold() for x in out}:out.append(candidate.casefold())
 return out
def phone_values(value:Any)->list[dict[str,Any]]:
 if not isinstance(value,dict):return []
 out=[];primary=clean(value.get('primaryPhoneNumber'))
 if primary:out.append({'number':primary,'countryCode':clean(value.get('primaryPhoneCountryCode')) or '', 'callingCode':clean(value.get('primaryPhoneCallingCode')) or ''})
 for item in value.get('additionalPhones') or []:
  if isinstance(item,dict):number=clean(item.get('number'));row={'number':number,'countryCode':clean(item.get('countryCode')) or '','callingCode':clean(item.get('callingCode')) or ''}
  else:number=clean(item);row={'number':number,'countryCode':'','callingCode':''}
  if number and normalise_phone_key(number) not in {normalise_phone_key(x['number']) for x in out}:out.append(row)
 return out
def link_values(value:Any)->list[dict[str,str]]:
 if not isinstance(value,dict):return []
 out=[];url=clean(value.get('primaryLinkUrl'))
 if url:out.append({'url':url,'label':clean(value.get('primaryLinkLabel')) or ''})
 for item in value.get('secondaryLinks') or []:
  if not isinstance(item,dict):continue
  url=clean(item.get('url'))
  if url and canonical_url(url) not in {canonical_url(x['url']) for x in out}:out.append({'url':url,'label':clean(item.get('label')) or ''})
 return out
def normalise_phone_key(value:Any)->str:return re.sub(r'[^0-9+]','',clean(value) or '').lstrip('00')
def canonical_url(value:Any)->str:
 value=clean(value)
 if not value:return ''
 try:
  parsed=urllib.parse.urlsplit(value if '://' in value else 'https://'+value);host=(parsed.hostname or '').casefold().strip('.');host=host[4:] if host.startswith('www.') else host
  query=urllib.parse.parse_qsl(parsed.query,keep_blank_values=True);query=[(k,v) for k,v in query if not k.casefold().startswith('utm_') and k.casefold() not in {'fbclid','gclid'}]
  path=re.sub(r'/+','/',parsed.path or '/');path='' if path=='/' else path.rstrip('/')
  return urllib.parse.urlunsplit(((parsed.scheme or 'https').casefold(),host,path,urllib.parse.urlencode(query),''))
 except Exception:return value
def full_name(value:Any)->str|None:
 if isinstance(value,str):return clean(value)
 if not isinstance(value,dict):return None
 first,last=clean(value.get('firstName')),clean(value.get('lastName'))
 return f'{first} {last}' if first and last else first or last
def split_name(value:str|None)->tuple[str|None,str|None]:
 value=clean(value)
 if not value:return None,None
 parts=value.split();return (parts[0],None) if len(parts)==1 else (' '.join(parts[:-1]),parts[-1])
def normalise_text(value:Any)->str:return re.sub(r'[^a-z0-9]+',' ',(clean(value) or '').casefold()).strip()
def filter_item(value:str,*,exact:bool=True)->dict[str,Any]:return {'value':value,'exact_match':exact,'exclude':False}
def make_envelope(schema_id:str,run_id:str,payload:dict[str,Any],*,company_id:str|None=None)->dict[str,Any]:
 result={'schema_id':schema_id,'schema_version':'0.1.0','run_id':run_id,'company_id':company_id,'created_at':utc_now(),'status':'valid','errors':[],'warnings':[],**payload}
 result['artifact_sha256']=sha256_json({k:v for k,v in result.items() if k!='artifact_sha256'});return result

def http_json(method:str,url:str,*,token:str,body:Any=None,timeout:int=30,retries:int=0)->tuple[Any,dict[str,Any]]:
 headers={'Authorization':f'Bearer {token}','Accept':'application/json'};data=None
 if body is not None:data=canonical_bytes(body);headers['Content-Type']='application/json'
 for attempt in range(1,retries+2):
  req=urllib.request.Request(url,data=data,method=method.upper(),headers=headers)
  try:
   with urllib.request.urlopen(req,timeout=timeout) as resp:
    raw=resp.read();payload=json.loads(raw.decode()) if raw else {}
    return payload,{'http_status':resp.status,'attempt':attempt,'received_at':utc_now()}
  except urllib.error.HTTPError as exc:
   raw=exc.read()
   try:payload=json.loads(raw.decode()) if raw else {}
   except Exception:payload={'message':raw[:500].decode('utf-8','replace')}
   code=payload.get('code') if isinstance(payload,dict) else None;transient=exc.code in {408,429,500,502,503,504}
   if transient and attempt<retries+1:time.sleep(min(2**(attempt-1),8));continue
   raise IntegrationError(str(payload.get('message') if isinstance(payload,dict) else exc),status=exc.code,code=code,payload=payload) from exc
  except (TimeoutError,urllib.error.URLError) as exc:
   if attempt<retries+1:time.sleep(min(2**(attempt-1),8));continue
   raise IntegrationError(str(exc),code='transport_error') from exc
 raise IntegrationError('request failed')
def twenty_env()->tuple[str,str]:
 base,key=env_value('TWENTY_BASE_URL'),env_value('TWENTY_API_KEY')
 if not base or not key:raise IntegrationError('TWENTY_BASE_URL and TWENTY_API_KEY are required',code='missing_credentials')
 return base.rstrip('/'),key
def firecrawl_env()->tuple[str,str]:
 contract=load_json(FIRECRAWL_CONTRACT);base=env_value('FIRECRAWL_API_URL') or contract['base_url'];key=env_value(contract['credential']['environment_variable'])
 if not key:raise IntegrationError('FIRECRAWL_API_KEY is required',code='missing_credentials')
 return base.rstrip('/'),key
def apify_env()->tuple[str,str]:
 contract=load_json(APIFY_FACEBOOK_CONTRACT);base=env_value('APIFY_API_URL') or contract['api_base'];key=env_value(contract['credential']['environment_variable']) or env_value('APIFY_TOKEN')
 if not key:raise IntegrationError('APIFY_API_KEY is required',code='missing_credentials')
 return base.rstrip('/'),key

def fullenrich_env()->tuple[str,str]:
 contract=load_json(FULLENRICH_CONTRACT);base=env_value('FULLENRICH_BASE_URL') or contract['base_url'];key=env_value(contract['authentication']['environment_variable'])
 if not key:raise IntegrationError('FULLENRICH_API_KEY is required',code='missing_credentials')
 return base.rstrip('/'),key

def normalise_twenty_person(r:dict[str,Any])->dict[str,Any]:
 return {'twenty_person_id':r.get('id'),'company_id':r.get('companyId'),'full_name':full_name(r.get('name')),'raw_name':r.get('name'),'job_title':clean(r.get('jobTitle')),'work_email':primary_email(r.get('emails')),'email_status':clean(r.get('emailStatus')),'phone':primary_phone(r.get('phones')),'professional_network_url':link_url(r.get('linkedinLink')),'a2_identity_status':r.get('a2IdentityStatus'),'a2_role_status':r.get('a2RoleStatus'),'a2_role_priority':r.get('a2RolePriority'),'a2_company_match_status':r.get('a2CompanyMatchStatus'),'a2_enrichment_status':r.get('a2EnrichmentStatus'),'fullenrich_person_id':r.get('a2FullenrichPersonid'),'last_verified_at':r.get('a2LastVerifiedAt'),'last_enriched_at':r.get('a2LastEnrichedAt'),'updated_at':r.get('updatedAt')}
def normalise_twenty_company(r:dict[str,Any])->dict[str,Any]:
 a=r.get('address') if isinstance(r.get('address'),dict) else {}
 return {'twenty_company_id':r.get('id'),'name':clean(r.get('name')),'segment':r.get('segment'),'website_url':link_url(r.get('domainName')),'domain':domain_name(link_url(r.get('domainName'))),'professional_network_url':link_url(r.get('linkedinLink')),'company_emails':email_values(r.get('email')),'company_phones':phone_values(r.get('phone')),'social_links':{'linkedin':link_values(r.get('linkedinLink')),'facebook':link_values(r.get('facebook')),'instagram':link_values(r.get('instagram')),'youtube':link_values(r.get('youtube')),'tiktok':link_values(r.get('tiktok')),'x':link_values(r.get('xTwitter'))},'company_contact_composites':{'email':r.get('email') or {'primaryEmail':'','additionalEmails':[]},'phone':r.get('phone') or {'primaryPhoneNumber':'','primaryPhoneCountryCode':'','primaryPhoneCallingCode':'','additionalPhones':[]},'linkedinLink':r.get('linkedinLink') or {'primaryLinkUrl':'','primaryLinkLabel':'','secondaryLinks':[]},'facebook':r.get('facebook') or {'primaryLinkUrl':'','primaryLinkLabel':'','secondaryLinks':[]},'instagram':r.get('instagram') or {'primaryLinkUrl':'','primaryLinkLabel':'','secondaryLinks':[]},'youtube':r.get('youtube') or {'primaryLinkUrl':'','primaryLinkLabel':'','secondaryLinks':[]},'tiktok':r.get('tiktok') or {'primaryLinkUrl':'','primaryLinkLabel':'','secondaryLinks':[]},'xTwitter':r.get('xTwitter') or {'primaryLinkUrl':'','primaryLinkLabel':'','secondaryLinks':[]}},'location':{'street':clean(a.get('addressStreet1')),'city':clean(a.get('addressCity')) or clean(r.get('city')),'region':clean(a.get('addressState')) or clean(r.get('state')),'country':clean(a.get('addressCountry')) or clean(r.get('country')),'postal_code':clean(a.get('addressPostcode'))},'a2_enrichment_status':r.get('a2EnrichmentStatus'),'a2_enrichment_version':r.get('a2EnrichmentVersion'),'a2_enrichment_run_id':r.get('a2EnrichmentRunId'),'a2_processing_started_at':r.get('a2ProcessingStartedAt'),'linked_people':[normalise_twenty_person(x) for x in (r.get('people') or []) if isinstance(x,dict)],'snapshot_updated_at':r.get('updatedAt')}
def response_records(payload:Any,plural:str)->list[dict[str,Any]]:
 data=payload.get('data') if isinstance(payload,dict) else None
 if isinstance(data,dict) and isinstance(data.get(plural),list):return [x for x in data[plural] if isinstance(x,dict)]
 if isinstance(data,list):return [x for x in data if isinstance(x,dict)]
 return []


def normalise_fullenrich_person(profile:dict[str,Any])->dict[str,Any]:
 employment=nested(profile,'employment','current') if isinstance(nested(profile,'employment','current'),dict) else {}
 company=employment.get('company') if isinstance(employment.get('company'),dict) else {}
 location=profile.get('location') if isinstance(profile.get('location'),dict) else {}
 social=nested(profile,'social_profiles','professional_network')
 return {'provider_person_id':clean(profile.get('id')),'full_name':clean(profile.get('full_name')),'first_name':clean(profile.get('first_name')),'last_name':clean(profile.get('last_name')),'exact_current_role':clean(employment.get('title')),'current_role_description':clean(employment.get('description')),'current_employment_is_current':employment.get('is_current'),'organisation':{'provider_company_id':clean(company.get('id')),'name':clean(company.get('name')),'domain':clean(company.get('domain')),'professional_network_url':clean(nested(company,'social_profiles','professional_network','url'))},'location':{k:clean(location.get(k)) for k in ('city','region','country','country_code') if clean(location.get(k))},'professional_network_url':clean(social.get('url')) if isinstance(social,dict) else None}
def select_work_email(contact:dict[str,Any])->dict[str,Any]|None:
 values=[]
 if isinstance(contact.get('most_probable_work_email'),dict):values.append(contact['most_probable_work_email'])
 values.extend(x for x in (contact.get('work_emails') or []) if isinstance(x,dict))
 for x in values:
  email,status=clean(x.get('email')),clean(x.get('status'))
  if email and re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",email):
   return {'value':email.casefold(),'status':status or 'unknown','provider_status':status,'status_source':'fullenrich' if status else 'a2_missing_provider_status_fallback','source':'fullenrich_contact_enrichment'}
 return None
def select_mobile(contact:dict[str,Any])->dict[str,Any]|None:
 values=[]
 if isinstance(contact.get('most_probable_phone'),dict):values.append(contact['most_probable_phone'])
 values.extend(x for x in (contact.get('phones') or []) if isinstance(x,dict))
 for x in values:
  number=clean(x.get('number'))
  if not number or x.get('line_status')=='INACTIVE' or x.get('ownership_match')=='MISMATCH':continue
  if x.get('line_type') in {'MOBILE','UNKNOWN',None}:return {'value':number,'region':clean(x.get('region')),'line_type':x.get('line_type'),'line_status':x.get('line_status'),'ownership_match':x.get('ownership_match')}
 return None


def fullenrich_preflight(base:str,key:str,minimum_credits:float=0)->dict[str,Any]:
 verify,vr=http_json('GET',base+'/account/keys/verify',token=key,retries=1)
 credits,cr=http_json('GET',base+'/account/credits',token=key,retries=1)
 balance=credits.get('balance') if isinstance(credits,dict) else None
 if not isinstance(balance,(int,float)):raise IntegrationError('FullEnrich credit response missing numeric balance',code='credit_response_invalid')
 if balance<minimum_credits:raise IntegrationError('FullEnrich credit balance below required minimum',code='credit_block')
 return {'workspace_id_present':bool(verify.get('workspace_id')) if isinstance(verify,dict) else False,'credits_before':balance,'receipts':[vr,cr]}
