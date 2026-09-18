#!/usr/bin/env python3
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];CID='c'
def packet():return {'company_id':CID,'official_url':'https://acme.example','company':{'name':'Acme Forge','domain':'acme.example'},'candidate_people':[{'observation_id':'p1','observed_name':'Corey Baxter, CJF','observed_role':'Farrier','page_evidence':[{'page_url':'https://acme.example/team','evidence_text':'Corey Baxter, CJF — Farrier'}]},{'observation_id':'p2','observed_name':'Jamie Staff','observed_role':None,'page_evidence':[{'page_url':'https://acme.example/about','evidence_text':'Jamie Staff'}]}]}
def validation(extra=None):return {'status':'valid','company_id':CID,'retained_people':[{'observation_id':'p1','name':'Corey Baxter, CJF','provider_comparison_name':'Corey Baxter','role':'Farrier','role_priority':'PRIMARY','page_evidence':[{'page_url':'x'}]},{'observation_id':'p2','name':'Jamie Staff','provider_comparison_name':'Jamie Staff','role':None,'role_priority':'UNKNOWN','page_evidence':[{'page_url':'y'}]}]+(extra or []),'retained_contacts':[{'observation_id':'e','contact_type':'email','value':'jamie@acme.example','attribution':{'entity_type':'Person','entity_id':'p2'}},{'observation_id':'ph','contact_type':'phone','value':'+15550001','attribution':{'entity_type':'Person','entity_id':'p2'}}]}
class Tests(unittest.TestCase):
 def invoke(self,pkt,val):
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);(td/'p.json').write_text(json.dumps(pkt));(td/'v.json').write_text(json.dumps(val));out=td/'o.json';p=subprocess.run([sys.executable,str(ROOT/'scripts/build_website_people_contact_batch.py'),str(td/'p.json'),str(td/'v.json'),'--run-id','r','--output',str(out)],cwd=ROOT,capture_output=True,text=True);return p.returncode,json.loads(out.read_text()),p.stdout+p.stderr
 def test_missing_channels_routes_contact_enrichment(self):
  rc,out,msg=self.invoke(packet(),validation());self.assertEqual(rc,0,msg);self.assertEqual(len(out['selected_people']),1);self.assertEqual(out['selected_people'][0]['full_name'],'Corey Baxter');self.assertEqual(out['selected_people'][0]['source_full_name'],'Corey Baxter, CJF');self.assertEqual(out['selected_people'][0]['selection_stage'],'website')
 def test_complete_website_person_skips_provider(self):
  rc,out,msg=self.invoke(packet(),validation());self.assertEqual(len(out['complete_people']),1);self.assertEqual(out['complete_people'][0]['website_work_email'],'jamie@acme.example')
 def test_unknown_role_is_allowed(self):
  rc,out,msg=self.invoke(packet(),validation());self.assertEqual(rc,0,msg);self.assertEqual(out['complete_people'][0]['selected_target_priority'],'UNKNOWN');self.assertIsNone(out['complete_people'][0]['exact_current_role'])
 def test_maximum_two(self):
  pkt=packet();pkt['candidate_people'].append({'observation_id':'p3','observed_name':'Third Person','observed_role':None,'page_evidence':[{'page_url':'z'}]});extra=[{'observation_id':'p3','name':'Third Person','provider_comparison_name':'Third Person','role':None,'role_priority':'UNKNOWN','page_evidence':[{'page_url':'z'}]}];rc,out,msg=self.invoke(pkt,validation(extra));self.assertEqual(rc,1);self.assertEqual(out['status'],'invalid')
if __name__=='__main__':unittest.main(verbosity=2)
