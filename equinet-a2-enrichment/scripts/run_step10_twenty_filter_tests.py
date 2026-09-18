#!/usr/bin/env python3
from __future__ import annotations
import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];FIX=ROOT/'evaluations/step10/filters/companies.json';SCRIPT=ROOT/'scripts/pull_twenty_companies.py'
def run(*args):
 td=tempfile.TemporaryDirectory();out=Path(td.name)/'out.json';p=subprocess.run([sys.executable,str(SCRIPT),'--run-id','FILTER-TEST','--fixture',str(FIX),'--output',str(out),*args],cwd=ROOT,capture_output=True,text=True);data=json.loads(out.read_text()) if out.exists() else {};return td,p,data
class FilterTests(unittest.TestCase):
 def test_latest_two_farriers(self):
  td,p,d=run('--batch-size','2','--segment','FARRIER');self.addCleanup(td.cleanup);self.assertEqual(p.returncode,0);self.assertEqual([x['twenty_company_id'] for x in d['companies']],['dup2','dup1']);self.assertIn('segment[eq]:FARRIER',d['twenty_query']['params']['filter'])
 def test_specific_id_default_eligibility(self):
  td,p,d=run('--batch-size','1','--company-id','f-mid');self.addCleanup(td.cleanup);self.assertEqual(p.returncode,0);self.assertEqual([x['twenty_company_id'] for x in d['companies']],['f-mid'])
 def test_completed_id_requires_explicit_reprocess(self):
  td,p,d=run('--batch-size','1','--company-id','done');self.addCleanup(td.cleanup);self.assertEqual(p.returncode,0);self.assertEqual(d['company_count'],0)
  td,p,d=run('--batch-size','1','--company-id','done','--allow-any-status');self.addCleanup(td.cleanup);self.assertEqual(p.returncode,0);self.assertEqual([x['twenty_company_id'] for x in d['companies']],['done'])
 def test_exact_name(self):
  td,p,d=run('--batch-size','1','--company-name','Middle Farrier');self.addCleanup(td.cleanup);self.assertEqual(p.returncode,0);self.assertEqual([x['twenty_company_id'] for x in d['companies']],['f-mid']);self.assertIn('name[eq]:"Middle Farrier"',d['twenty_query']['params']['filter'])
 def test_ambiguous_name_is_error(self):
  td,p,d=run('--batch-size','1','--company-name','Duplicate Name');self.addCleanup(td.cleanup);self.assertEqual(p.returncode,1);self.assertIn('ambiguous',d['error'])
 def test_location_and_date(self):
  td,p,d=run('--batch-size','10','--city','LEXINGTON','--created-after','2026-09-03T12:00:00Z');self.addCleanup(td.cleanup);self.assertEqual(p.returncode,0);self.assertEqual({x['twenty_company_id'] for x in d['companies']},{'h-new','dup1','dup2'})
 def test_multiple_status_or_null_filter(self):
  td,p,d=run('--batch-size','10','--status','NOT_ENRICHED','--status','RETRYABLE_ERROR','--include-null');self.addCleanup(td.cleanup);self.assertEqual(p.returncode,0);self.assertTrue(d['twenty_query']['params']['filter'].startswith('or('))
if __name__=='__main__':unittest.main(verbosity=2)
