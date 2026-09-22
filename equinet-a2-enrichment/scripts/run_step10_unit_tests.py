#!/usr/bin/env python3
from __future__ import annotations
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from a2_twenty_fullenrich_common import domain_name,normalise_fullenrich_person,select_mobile,select_work_email,split_name
from fullenrich_people_search import build_payload as search_payload
from fullenrich_people_lookup import build_payload as lookup_payload
from fullenrich_contact_enrichment import minimise as minimise_contact
from classify_a2_target_role_v2 import classify
from push_twenty_enrichment import equivalent,validate_plan
class Tests(unittest.TestCase):
 def test_domainless_search(self):
  p=search_payload({'company_name':'Bluegrass Farm','location':{'city':'Lexington','region':'Kentucky'},'target_titles':['Farm Owner'],'limit':2})
  self.assertIn('current_company_names',p);self.assertNotIn('current_company_domains',p);self.assertEqual(p['limit'],2);self.assertIn('current_position_titles',p)
 def test_search_rejects_role_free(self):
  with self.assertRaises(ValueError):search_payload({'company_name':'Bluegrass Farm'})
 def test_lookup_identifier_rules(self):
  self.assertEqual(lookup_payload({'person_professional_network_url':'https://www.linkedin.com/in/test'}),{'person_professional_network_url':'https://www.linkedin.com/in/test'})
  with self.assertRaises(ValueError):lookup_payload({'person_name':'Test Person','company_name':'Unsupported'})
 def test_email_selection(self):
  invalid=select_work_email({'most_probable_work_email':{'email':'x@example.test','status':'INVALID'}});self.assertEqual(invalid['value'],'x@example.test');self.assertEqual(invalid['provider_status'],'INVALID')
  catch_all=select_work_email({'most_probable_work_email':{'email':'CatchAll@example.test','status':'CATCH_ALL'}});self.assertEqual(catch_all['value'],'catchall@example.test');self.assertEqual(catch_all['provider_status'],'CATCH_ALL')
  missing=select_work_email({'most_probable_work_email':{'email':'missing-status@example.test'}});self.assertEqual(missing['status'],'unknown');self.assertIsNone(missing['provider_status']);self.assertEqual(missing['status_source'],'a2_missing_provider_status_fallback')
  result=minimise_contact({'data':[{'custom':{'request_id':'r1','company_id':'c1'},'contact_info':{'most_probable_work_email':{'email':'missing-status@example.test'}}}]})[0];self.assertEqual(result['work_email_status'],'unknown');self.assertEqual(result['work_email_status_source'],'a2_missing_provider_status_fallback')
  self.assertEqual(select_work_email({'most_probable_work_email':{'email':'X@example.test','status':'DELIVERABLE'}})['value'],'x@example.test')
  self.assertIsNone(select_work_email({'most_probable_work_email':{'email':'not-an-email','status':'DELIVERABLE'}}))
 def test_phone_selection(self):
  self.assertIsNone(select_mobile({'most_probable_phone':{'number':'+1','line_status':'INACTIVE','line_type':'MOBILE'}}))
  self.assertIsNone(select_mobile({'most_probable_phone':{'number':'+1','line_status':'ACTIVE','line_type':'MOBILE','ownership_match':'MISMATCH'}}))
  self.assertEqual(select_mobile({'most_probable_phone':{'number':'+1','line_status':'ACTIVE','line_type':'MOBILE'}})['value'],'+1')
 def test_active_role_classifier(self):
  self.assertEqual(classify({'segment':'farrier','source_role_title':'Farrier'})['priority'],'primary')
  self.assertEqual(classify({'segment':'horse_owner','source_role_title':'Farm Owner'})['priority'],'primary')
 def test_name_split(self):self.assertEqual(split_name('Jordan Owner'),('Jordan','Owner'))
 def test_domain_normalisation(self):self.assertEqual(domain_name('http://www.HiddenCreek.Farm/path'),'hiddencreek.farm')
 def test_protected_write_rejected(self):
  errors=validate_plan({'operations':[{'operation_id':'x','operation_type':'update_company_status','fields':{'icpScore':99}}]})
  self.assertTrue(any('protected' in x for x in errors))
 def test_timestamp_equivalence(self):self.assertTrue(equivalent('2026-09-15T11:19:07Z','2026-09-15T11:19:07.000Z'))
 def test_status_last(self):
  errors=validate_plan({'operations':[{'operation_id':'s','operation_type':'update_company_status','fields':{}},{'operation_id':'p','operation_type':'update_person','fields':{}}]})
  self.assertTrue(any('must be last' in x for x in errors))
if __name__=='__main__':unittest.main(verbosity=2)
