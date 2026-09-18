#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from a2_twenty_fullenrich_common import normalise_twenty_company,sha256_json
import push_twenty_enrichment as push
from push_twenty_enrichment import validate_plan
class Tests(unittest.TestCase):
 def run_merge(self,request):
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);inp=td/'in.json';out=td/'out.json';inp.write_text(json.dumps(request));p=subprocess.run([sys.executable,str(ROOT/'scripts/build_company_contact_merge_plan.py'),str(inp),'--output',str(out)],cwd=ROOT,capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr);return json.loads(out.read_text())
 def base(self):return {'email':{'primaryEmail':'a1@example.com','additionalEmails':[]},'phone':{'primaryPhoneNumber':'+15550001','primaryPhoneCountryCode':'US','primaryPhoneCallingCode':'+1','additionalPhones':[]},'linkedinLink':{'primaryLinkUrl':'','primaryLinkLabel':'','secondaryLinks':[]},'facebook':{'primaryLinkUrl':'','primaryLinkLabel':'','secondaryLinks':[]},'instagram':{'primaryLinkUrl':'','primaryLinkLabel':'','secondaryLinks':[]},'youtube':{'primaryLinkUrl':'','primaryLinkLabel':'','secondaryLinks':[]},'tiktok':{'primaryLinkUrl':'','primaryLinkLabel':'','secondaryLinks':[]},'xTwitter':{'primaryLinkUrl':'','primaryLinkLabel':'','secondaryLinks':[]}}
 def test_preserve_primary_and_append(self):
  b=self.base();r=self.run_merge({'run_id':'x','company_id':'c','baseline':b,'observations':[{'field':'email','value':'web@example.com','accepted':True,'source':'official_website','evidence_refs':['e1']},{'field':'phone','value':'+15550002','country_code':'US','calling_code':'+1','accepted':True,'source':'official_website','evidence_refs':['e2']}]});self.assertEqual(r['merged_fields']['email']['primaryEmail'],'a1@example.com');self.assertEqual(r['merged_fields']['email']['additionalEmails'],['web@example.com']);self.assertEqual(r['merged_fields']['phone']['additionalPhones'][0]['number'],'+15550002')
 def test_empty_primary_uses_website(self):
  b=self.base();b['email']={'primaryEmail':'','additionalEmails':[]};r=self.run_merge({'run_id':'x','company_id':'c','baseline':b,'observations':[{'field':'email','value':'web@example.com','accepted':True,'source':'official_website','evidence_refs':['e']}]});self.assertEqual(r['merged_fields']['email']['primaryEmail'],'web@example.com')
 def test_duplicate_is_no_change(self):
  b=self.base();r=self.run_merge({'run_id':'x','company_id':'c','baseline':b,'observations':[{'field':'email','value':'A1@EXAMPLE.COM','accepted':True,'source':'official_website','evidence_refs':['e']}]});self.assertEqual(r['company_field_updates'],{});self.assertEqual(r['decisions'][0]['action'],'no_change')
 def test_social_canonicalisation(self):
  b=self.base();r=self.run_merge({'run_id':'x','company_id':'c','baseline':b,'observations':[{'field':'facebook','value':'https://www.facebook.com/acme/?utm_source=x','accepted':True,'source':'official_website','evidence_refs':['e']}]});self.assertEqual(r['merged_fields']['facebook']['primaryLinkUrl'],'https://facebook.com/acme')
 def test_write_plan_company_operation_first(self):
  b=self.base();merge=self.run_merge({'run_id':'x','company_id':'c','baseline':b,'observations':[{'field':'email','value':'web@example.com','accepted':True,'source':'official_website','evidence_refs':['e']}]});proposal={'run_id':'x','company_id':'c','company_final_status':'PARTIALLY_ENRICHED','company_merge':{'baseline':b,'baseline_sha256':sha256_json(b),'company_field_updates':merge['company_field_updates']},'resolved_people':[]}
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);inp=td/'p.json';out=td/'w.json';inp.write_text(json.dumps(proposal));p=subprocess.run([sys.executable,str(ROOT/'scripts/build_twenty_enrichment_write_plan.py'),str(inp),'--output',str(out)],cwd=ROOT,capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr);plan=json.loads(out.read_text());self.assertEqual(plan['operations'][0]['operation_type'],'update_company_fields');self.assertEqual(plan['operations'][-1]['operation_type'],'update_company_status');self.assertEqual(validate_plan(plan),[])
 def test_generic_company_contact_never_person(self):
  b=self.base();request={'run_id':'x','company_id':'c','baseline':b,'observations':[{'field':'person_email','value':'x@example.com','accepted':True,'source':'official_website','evidence_refs':['e']}]}
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);inp=td/'in.json';out=td/'out.json';inp.write_text(json.dumps(request));p=subprocess.run([sys.executable,str(ROOT/'scripts/build_company_contact_merge_plan.py'),str(inp),'--output',str(out)],cwd=ROOT,capture_output=True,text=True);self.assertEqual(p.returncode,1);self.assertEqual(json.loads(out.read_text())['status'],'invalid')
 def test_apply_company_merge_and_readback(self):
  b=self.base();updated={**b,'email':{'primaryEmail':'a1@example.com','additionalEmails':['web@example.com']}};plan={'company_id':'c','operations':[{'operation_id':'merge','operation_type':'update_company_fields','twenty_company_id':'c','baseline_sha256':sha256_json(b),'baseline_fields':b,'fields':{'email':updated['email']}},{'operation_id':'final','operation_type':'update_company_status','twenty_company_id':'c','fields':{'a2EnrichmentStatus':'PARTIALLY_ENRICHED'}}],'expected_read_back':{'company_fields':{'email':updated['email'],'a2EnrichmentStatus':'PARTIALLY_ENRICHED'},'people':[]}}
  state={**b,'id':'c','people':[],'a2EnrichmentStatus':'PROCESSING'};old_env,old_http=push.twenty_env,push.http_json
  def fake(method,url,token,body=None,retries=0):
   if method=='GET':return {'data':{'company':dict(state)}},{'http_status':200}
   state.update(body or {});return {'data':{'company':dict(state)}},{'http_status':200}
  try:
   push.twenty_env=lambda:('http://twenty.invalid','token');push.http_json=fake;result=push.apply(plan,True)
  finally:push.twenty_env, push.http_json=old_env,old_http
  self.assertEqual(result['status'],'reconciled');self.assertEqual(result['external_writes'],2)
 def test_apply_blocks_changed_baseline(self):
  b=self.base();plan={'company_id':'c','operations':[{'operation_id':'merge','operation_type':'update_company_fields','twenty_company_id':'c','baseline_sha256':sha256_json(b),'baseline_fields':b,'fields':{'email':{'primaryEmail':'x@example.com','additionalEmails':[]}}}],'expected_read_back':{'company_fields':{},'people':[]}};state={**b,'id':'c','people':[]};state['email']={'primaryEmail':'changed@example.com','additionalEmails':[]};old_env,old_http=push.twenty_env,push.http_json
  def fake(method,url,token,body=None,retries=0):return {'data':{'company':dict(state)}},{'http_status':200}
  try:
   push.twenty_env=lambda:('http://twenty.invalid','token');push.http_json=fake
   with self.assertRaises(Exception):push.apply(plan,True)
  finally:push.twenty_env,push.http_json=old_env,old_http
 def test_website_person_without_role_can_be_created(self):
  proposal={'run_id':'x','company_id':'c','company_final_status':'PARTIALLY_ENRICHED','resolved_people':[{'source_kind':'new','selection_stage':'website','website_person_id':'web-person-1','full_name':'Alex Smith','statuses':{'identity':'VERIFIED','role':'CURRENT_AT_COMPANY','priority':'UNKNOWN','company_match':'CONFIRMED','enrichment':'PARTIAL'},'field_decisions':{}}]}
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);inp=td/'p.json';out=td/'w.json';inp.write_text(json.dumps(proposal));p=subprocess.run([sys.executable,str(ROOT/'scripts/build_twenty_enrichment_write_plan.py'),str(inp),'--output',str(out)],cwd=ROOT,capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr);plan=json.loads(out.read_text());self.assertEqual(plan['operations'][0]['operation_type'],'create_person');self.assertEqual(plan['operations'][0]['source_website_person_id'],'web-person-1');self.assertEqual(plan['operations'][0]['fields']['a2RolePriority'],'UNKNOWN')
 def test_company_normalisation_includes_contacts_and_socials(self):
  raw={'id':'c','name':'Acme','domainName':{'primaryLinkUrl':'https://acme.example','primaryLinkLabel':'Official','secondaryLinks':[]},'email':{'primaryEmail':'a@acme.example','additionalEmails':['b@acme.example']},'phone':{'primaryPhoneNumber':'+15550001','primaryPhoneCountryCode':'US','primaryPhoneCallingCode':'+1','additionalPhones':[{'number':'+15550002','countryCode':'US','callingCode':'+1'}]},'facebook':{'primaryLinkUrl':'https://facebook.com/acme','primaryLinkLabel':'Facebook','secondaryLinks':[]},'people':[]}
  c=normalise_twenty_company(raw);self.assertEqual(c['website_url'],'https://acme.example');self.assertEqual(c['company_emails'],['a@acme.example','b@acme.example']);self.assertEqual(len(c['company_phones']),2);self.assertEqual(c['social_links']['facebook'][0]['url'],'https://facebook.com/acme')
 def test_website_person_preserves_multiple_channels(self):
  proposal={'run_id':'x','company_id':'c','company_final_status':'PARTIALLY_ENRICHED','resolved_people':[{'source_kind':'new','selection_stage':'website','website_person_id':'wp','full_name':'Alex Smith','merged_work_emails':['site@acme.example',{'value':'provider@acme.example'}],'merged_phones':[{'value':'+15550001','region':'US'},{'value':'+15550002','region':'US'}],'statuses':{'identity':'VERIFIED','role':'CURRENT_AT_COMPANY','priority':'UNKNOWN','company_match':'CONFIRMED','enrichment':'ENRICHED'},'field_decisions':{}}]}
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);inp=td/'p.json';out=td/'w.json';inp.write_text(json.dumps(proposal));p=subprocess.run([sys.executable,str(ROOT/'scripts/build_twenty_enrichment_write_plan.py'),str(inp),'--output',str(out)],cwd=ROOT,capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stdout+p.stderr);fields=json.loads(out.read_text())['operations'][0]['fields'];self.assertEqual(fields['emails']['primaryEmail'],'site@acme.example');self.assertEqual(fields['emails']['additionalEmails'],['provider@acme.example']);self.assertEqual(len(fields['phones']['additionalPhones']),1)
if __name__=='__main__':unittest.main(verbosity=2)
