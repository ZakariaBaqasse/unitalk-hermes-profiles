#!/usr/bin/env python3
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
 def invoke(self,data,env=None):
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);inp=td/'in.json';out=td/'out.json';inp.write_text(json.dumps(data));p=subprocess.run([sys.executable,str(ROOT/'scripts/preflight_step11_source_action.py'),str(inp),'--output',str(out)],cwd=ROOT,capture_output=True,text=True,env=env);return p.returncode,json.loads(out.read_text())
 def test_website_fixture_allowed(self):
  rc,out=self.invoke({'run_id':'r','company_id':'c','source_id':'prospect_official_website','execution_mode':'local_fixture_simulation','official_url':'https://example.com','maximum_pages':5,'agent_web_extract':False});self.assertEqual(rc,0);self.assertEqual(out['preflight_status'],'allowed_fixture')
 def test_live_website_requires_candidate_specific_approval(self):
  rc,out=self.invoke({'run_id':'r','company_id':'c','source_id':'prospect_official_website','execution_mode':'live','official_url':'https://example.com','maximum_pages':5,'agent_web_extract':False});self.assertEqual(rc,1);self.assertIn('candidate_specific_integration_validation_approval_required',out['blocks'])
 def test_agent_web_extract_blocked(self):
  rc,out=self.invoke({'run_id':'r','company_id':'c','source_id':'prospect_official_website','execution_mode':'preflight_only','official_url':'https://example.com','maximum_pages':5,'agent_web_extract':True});self.assertEqual(rc,1);self.assertIn('agent_web_extract_runtime_prohibited',out['blocks'])
 def test_facebook_requires_official_link(self):
  rc,out=self.invoke({'run_id':'r','company_id':'c','source_id':'apify_facebook_page_contact_information','execution_mode':'local_fixture_simulation','missing_channels':['email'],'actor_calls_per_company':1,'automatic_retries':0});self.assertEqual(rc,1);self.assertIn('official_website_facebook_link_required',out['blocks'])
 def test_facebook_fixture_allowed(self):
  rc,out=self.invoke({'run_id':'r','company_id':'c','source_id':'apify_facebook_page_contact_information','execution_mode':'local_fixture_simulation','official_facebook_link_evidence':True,'missing_channels':['phone'],'actor_calls_per_company':1,'automatic_retries':0});self.assertEqual(rc,0)
if __name__=='__main__':unittest.main(verbosity=2)
