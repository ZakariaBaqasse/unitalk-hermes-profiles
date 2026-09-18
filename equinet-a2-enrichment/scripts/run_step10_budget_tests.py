#!/usr/bin/env python3
from __future__ import annotations
import json,os,sys,tempfile,unittest
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from a2_fullenrich_budget import estimate_credits,reserve_credits,settle_credits,usage_summary
from a2_twenty_fullenrich_common import IntegrationError
class BudgetTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=os.environ.get('A2_FULLENRICH_CREDIT_LEDGER');self.path=Path(self.tmp.name)/'ledger.json';os.environ['A2_FULLENRICH_CREDIT_LEDGER']=str(self.path)
 def tearDown(self):
  if self.old is None:os.environ.pop('A2_FULLENRICH_CREDIT_LEDGER',None)
  else:os.environ['A2_FULLENRICH_CREDIT_LEDGER']=self.old
  self.tmp.cleanup()
 def test_estimates(self):
  self.assertEqual(estimate_credits('people_lookup',[{}]),0.25);self.assertEqual(estimate_credits('people_search',[{'limit':2}]),0.5);self.assertEqual(estimate_credits('contact_enrichment',[{},{}]),22)
 def test_idempotent_reservation_and_settlement(self):
  a=reserve_credits(run_id='R1',action='people_lookup',maximum_credits=.25,request={'x':1});b=reserve_credits(run_id='R1',action='people_lookup',maximum_credits=.25,request={'x':1});self.assertEqual(a['reservation_id'],b['reservation_id']);self.assertTrue(b['reused']);settle_credits(a['reservation_id'],.25);self.assertEqual(usage_summary()['pilot_used'],.25)
 def test_per_run_hard_stop(self):
  reserve_credits(run_id='R1',action='a',maximum_credits=49,request={'x':1})
  with self.assertRaisesRegex(IntegrationError,'run'):reserve_credits(run_id='R1',action='b',maximum_credits=2,request={'x':2})
 def test_daily_hard_stop(self):
  day=datetime.now(timezone.utc).date().isoformat();self.path.write_text(json.dumps({'schema_id':'a2-fullenrich-credit-ledger','version':'0.1.0','pilot_id':'test','entries':[{'reservation_id':'a','run_id':'R1','action':'x','request_sha256':'a','reserved_credits':50,'actual_credits':50,'status':'settled','created_at':day+'T00:00:00Z'},{'reservation_id':'b','run_id':'R2','action':'x','request_sha256':'b','reserved_credits':50,'actual_credits':50,'status':'settled','created_at':day+'T00:00:00Z'}]}))
  with self.assertRaisesRegex(IntegrationError,'day'):reserve_credits(run_id='R3',action='x',maximum_credits=.25,request={'x':3})
 def test_pilot_hard_stop(self):
  entries=[{'reservation_id':str(i),'run_id':f'R{i}','action':'x','request_sha256':str(i),'reserved_credits':50,'actual_credits':50,'status':'settled','created_at':f'2026-09-{i:02d}T00:00:00Z'} for i in range(1,6)];self.path.write_text(json.dumps({'schema_id':'a2-fullenrich-credit-ledger','version':'0.1.0','pilot_id':'test','entries':entries}))
  with self.assertRaisesRegex(IntegrationError,'pilot'):reserve_credits(run_id='R6',action='x',maximum_credits=.25,request={'x':6})
if __name__=='__main__':unittest.main(verbosity=2)
