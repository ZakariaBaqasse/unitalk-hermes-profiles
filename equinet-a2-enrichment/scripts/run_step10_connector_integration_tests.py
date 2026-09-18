#!/usr/bin/env python3
from __future__ import annotations
import json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));F=ROOT/'evaluations/step10/fixtures'
import fullenrich_contact_enrichment as contact
import push_twenty_enrichment as push
from a2_twenty_fullenrich_common import IntegrationError
class ConnectorTests(unittest.TestCase):
 def test_contact_submit_poll_and_minimise(self):
  state={'polls':0}
  final=json.loads((F/'contact-provider.json').read_text());final['data']=final['data'][:1];final['cost']={'credits':11}
  def fake_http(method,url,**kwargs):
   if method=='POST':return {'enrichment_id':'mock-id'},{'http_status':200}
   state['polls']+=1
   if state['polls']==1:raise IntegrationError('not ready',status=400,code='error.enrichment.in_progress')
   return final,{'http_status':200}
  req=json.loads((F/'selected-people.json').read_text());req['selected_people']=req['selected_people'][:1]
  with tempfile.TemporaryDirectory() as td:
   prior=os.environ.get('A2_FULLENRICH_CREDIT_LEDGER');os.environ['A2_FULLENRICH_CREDIT_LEDGER']=str(Path(td)/'credits.json')
   inp=Path(td)/'in.json';out=Path(td)/'out.json';inp.write_text(json.dumps(req))
   argv=['x',str(inp),'--poll-seconds','1','--max-polls','2','--output',str(out)]
   with patch.object(sys,'argv',argv),patch.object(contact,'fullenrich_env',return_value=('mock','key')),patch.object(contact,'fullenrich_preflight',return_value={'credits_before':100}),patch.object(contact,'http_json',side_effect=fake_http),patch.object(contact.time,'sleep',return_value=None):rc=contact.main()
   result=json.loads(out.read_text());self.assertEqual(rc,0);self.assertEqual(result['terminal_status'],'FINISHED');self.assertEqual(len(result['results']),1);self.assertFalse(result['personal_email_requested']);self.assertEqual(state['polls'],2);self.assertEqual(result['budget']['settlement']['actual_credits'],11)
   if prior is None:os.environ.pop('A2_FULLENRICH_CREDIT_LEDGER',None)
   else:os.environ['A2_FULLENRICH_CREDIT_LEDGER']=prior
 def test_twenty_apply_and_reconcile(self):
  plan=json.loads((ROOT/'evaluations/step10/work/write-plan.json').read_text());company_id=plan['company_id'];state={'company':{'id':company_id,'a2EnrichmentStatus':'PROCESSING'},'people':{}}
  def fake_http(method,url,**kwargs):
   body=kwargs.get('body') or {};path=url.split('?')[0]
   if method=='POST' and path.endswith('/rest/people'):
    pid=f"person-{len(state['people'])+1}";state['people'][pid]={'id':pid,**body};return {'data':{'person':state['people'][pid]}},{'http_status':200}
   if method=='PATCH' and '/rest/people/' in path:
    pid=path.rsplit('/',1)[-1];state['people'].setdefault(pid,{'id':pid});state['people'][pid].update(body);return {'data':{'person':state['people'][pid]}},{'http_status':200}
   if method=='PATCH' and path.endswith('/rest/companies/'+company_id):state['company'].update(body);return {'data':{'company':state['company']}},{'http_status':200}
   if method=='GET' and path.endswith('/rest/companies/'+company_id):return {'data':{'company':{**state['company'],'people':list(state['people'].values())}}},{'http_status':200}
   raise AssertionError((method,url,body))
  with patch.object(push,'twenty_env',return_value=('mock','key')),patch.object(push,'http_json',side_effect=fake_http):result=push.apply(plan,True)
  self.assertEqual(result['status'],'reconciled');self.assertEqual(result['mismatches'],[]);self.assertEqual(len(state['people']),2);self.assertEqual(state['company']['a2EnrichmentStatus'],'ENRICHED')
if __name__=='__main__':unittest.main(verbosity=2)
