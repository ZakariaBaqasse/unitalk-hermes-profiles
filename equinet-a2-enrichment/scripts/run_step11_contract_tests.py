#!/usr/bin/env python3
import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(rel):return json.loads((ROOT/rel).read_text())
class Tests(unittest.TestCase):
 def test_decision(self):
  d=load('foundations/decisions/A2-WEBSITE-FIRST-FIRECRAWL-FACEBOOK-20260918.json')['decisions'];self.assertTrue(d['website_before_fullenrich']);self.assertEqual(d['max_pages_per_company'],5);self.assertFalse(d['agent_web_extract_for_prospects']);self.assertFalse(d['firecrawl_credit_policy_required']);self.assertEqual(d['facebook_actor_calls_per_company'],1);self.assertEqual(d['facebook_automatic_retries'],0);self.assertIsNone(d['facebook_company_count_cap'])
 def test_firecrawl_contract(self):
  d=load('foundations/contracts/integrations/a2-official-website-firecrawl-integration-0.1.0.json');self.assertEqual(d['credential']['environment_variable'],'FIRECRAWL_API_KEY');self.assertEqual(d['limits']['max_pages_per_company'],5);self.assertFalse(d['operations']['homepage']['onlyMainContent']);self.assertFalse(d['operations']['homepage']['storeInCache']);self.assertIsNone(d['firecrawl_credit_policy'])
 def test_apify_contract(self):
  d=load('foundations/contracts/integrations/a2-apify-facebook-page-contact-integration-0.1.0.json');self.assertEqual(d['actor']['name'],'apify~facebook-page-contact-information');self.assertEqual(d['limits']['actor_calls_per_company'],1);self.assertEqual(d['limits']['automatic_retries'],0);self.assertTrue(d['trigger']['official_facebook_url_from_website_required'])
 def test_source_order(self):
  d=load('foundations/contracts/sources/a2-source-register-0.3.2.json')['source_sequence'];self.assertLess(d.index('prospect_official_website'),d.index('fullenrich_people_search'));self.assertLess(d.index('apify_facebook_page_contact_information'),d.index('fullenrich_people_search'))
 def test_twenty_mapping(self):
  f=load('foundations/contracts/twenty/a2-twenty-operational-mapping-0.1.2.json')['objects']['company']['business_fields'];self.assertEqual(f,{'website':'domainName','email':'email','phone':'phone','linkedin':'linkedinLink','facebook':'facebook','instagram':'instagram','youtube':'youtube','tiktok':'tiktok','x':'xTwitter'})
 def test_runtime_stays_blocked(self):
  p=load('foundations/contracts/runtime/a2-step11-runtime-policy-0.1.0-rc.1.json')['permissions'];self.assertFalse(p['firecrawl_live']);self.assertFalse(p['apify_facebook_live']);self.assertFalse(p['twenty_company_contact_social_write'])
if __name__=='__main__':unittest.main(verbosity=2)
