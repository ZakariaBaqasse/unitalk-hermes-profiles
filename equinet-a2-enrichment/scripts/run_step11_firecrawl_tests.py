#!/usr/bin/env python3
"""Dedicated offline tests for the bounded Step 11 Firecrawl official-site flow."""
from __future__ import annotations

import copy
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "evaluations" / "step11" / "fixtures" / "firecrawl"
sys.path.insert(0, str(SCRIPTS))

from build_official_site_plan import PlanError, build_plan, load_json, same_site_host, validate_public_url
from firecrawl_official_site_fetch import FORMATS, FixtureTransport, fetch_official_site, robots_allows_text
from extract_official_site_observations import _person_candidates, extract_observations
from build_website_decision_packet import PacketError, build_packet
from validate_website_person_observation_proposals import validate_proposals
from validate_website_decisions import validate_decisions

SCRIPT_NAMES = [
    "build_official_site_plan.py",
    "firecrawl_official_site_fetch.py",
    "extract_official_site_observations.py",
    "build_website_decision_packet.py",
    "validate_website_person_observation_proposals.py",
    "validate_website_decisions.py",
    "run_step11_firecrawl_tests.py",
]


def plan() -> dict:
    return build_plan(load_json(FIXTURES / "plan-input.json"))


def happy_fetch() -> dict:
    return fetch_official_site(plan(), fixture=load_json(FIXTURES / "happy-path.json"), sleeper=lambda _: None)


class BuildPlanTests(unittest.TestCase):
    def test_valid_company_run_and_official_url(self) -> None:
        result = plan()
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["company_id"], "company-fixture-001")
        self.assertEqual(result["page_limit"], 5)
        self.assertEqual(result["discovered_page_limit"], 4)
        self.assertEqual(result["firecrawl"]["formats"], ["markdown", "html", "links"])
        self.assertIs(result["firecrawl"]["onlyMainContent"], False)
        self.assertIs(result["firecrawl"]["json_or_llm_formats"], False)
        self.assertIs(result["firecrawl"]["credit_policy_calls"], False)
        self.assertIs(result["firecrawl"]["storeInCache"], False)
        self.assertIs(result["firecrawl"]["skipTlsVerification"], False)

    def test_required_input_validation(self) -> None:
        for request in (
            {},
            {"run_id": "r", "company": {"company_id": "c", "name": ""}, "official_url": "https://example.com"},
            {"run_id": "r", "company": {"name": "Example"}, "official_url": "https://example.com"},
        ):
            with self.subTest(request=request), self.assertRaises(PlanError):
                build_plan(request)

    def test_ssrf_and_scheme_blocks(self) -> None:
        blocked = [
            "file:///etc/passwd",
            "ftp://example.com/file",
            "https://user:secret@example.com/",
            "http://127.0.0.1/",
            "http://[::1]/",
            "http://10.0.0.4/",
            "http://169.254.169.254/latest/meta-data/",
            "http://169.254.170.2/credentials",
            "http://100.100.100.200/latest/meta-data/",
            "http://2130706433/",
            "http://127.1/",
            "http://0x7f000001/",
            "https://example.com:8443/",
        ]
        for url in blocked:
            with self.subTest(url=url), self.assertRaises(PlanError):
                validate_public_url(url)

    def test_dns_rebinding_targets_are_blocked(self) -> None:
        def private_resolver(*args, **kwargs):
            return [(2, 1, 6, "", ("192.168.1.9", 0))]
        with self.assertRaises(PlanError):
            validate_public_url("https://example.com", resolve_dns=True, resolver=private_resolver)

    def test_robots_rules_are_enforced(self) -> None:
        text="User-agent: EquinetA2\nDisallow: /private\nAllow: /"
        self.assertTrue(robots_allows_text(text,"https://example.com/contact"))
        self.assertFalse(robots_allows_text(text,"https://example.com/private/team"))

    def test_same_domain(self) -> None:
        self.assertTrue(same_site_host("www.example.com", "example.com"))
        self.assertTrue(same_site_host("team.example.com", "www.example.com"))
        self.assertFalse(same_site_host("example.com.evil.test", "example.com"))
        with self.assertRaises(PlanError):
            validate_public_url("https://evil.test/contact", official_host="www.example.com")


class FirecrawlFetchTests(unittest.TestCase):
    def test_homepage_then_bounded_batch_and_payload(self) -> None:
        fixture = load_json(FIXTURES / "happy-path.json")
        transport = FixtureTransport(fixture)
        result = fetch_official_site(plan(), transport=transport, resolve_dns=False, sleeper=lambda _: None)
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["page_count"], 5)
        self.assertLessEqual(result["page_count"], 5)
        self.assertEqual([row["method"] for row in transport.requests], ["POST", "POST", "GET"])
        home_body = transport.requests[0]["body"]
        batch_body = transport.requests[1]["body"]
        self.assertEqual(home_body, {"url": "https://www.example.com/", "formats": FORMATS, "onlyMainContent": False, "storeInCache": False, "skipTlsVerification": False, "removeBase64Images": True, "proxy": "auto"})
        self.assertEqual(batch_body["formats"], ["markdown", "html", "links"]);self.assertEqual(batch_body["maxConcurrency"],1);self.assertIs(batch_body["storeInCache"],False);self.assertIs(batch_body["skipTlsVerification"],False)
        self.assertIs(batch_body["onlyMainContent"], False)
        self.assertNotIn("json", batch_body)
        self.assertNotIn("extract", batch_body)
        self.assertLessEqual(len(batch_body["urls"]), 4)
        self.assertNotIn("https://evil.example.net/contact", batch_body["urls"])
        self.assertFalse(any("127.0.0.1" in url for url in batch_body["urls"]))
        self.assertEqual(result["external_calls"], 0)
        self.assertEqual(result["fixture_calls"], 3)
        self.assertEqual(len(result["provider_receipts"]), 3)
        self.assertTrue(all(row.get("request_sha256") or row["method"] == "GET" for row in result["provider_receipts"]))
        self.assertIs(result["browser_fallback"], False)
        self.assertIs(result["web_extract_fallback"], False)
        self.assertEqual(result["credit_policy_calls"], 0)
        self.assertEqual(result["plan_sha256"], plan()["artifact_sha256"])

    def test_fixture_mode_does_not_require_api_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            result = happy_fetch()
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["external_calls"], 0)

    def test_live_mode_requires_environment_key_before_network(self) -> None:
        with patch.dict(os.environ, {}, clear=True), patch("firecrawl_official_site_fetch.env_value", return_value=None):
            result = fetch_official_site(plan())
        self.assertEqual(result["status"], "blocked")
        self.assertIn("FIRECRAWL_API_KEY", result["errors"][0])
        self.assertEqual(result["provider_receipts"], [])

    def test_discovered_subdomain_private_dns_is_blocked_before_batch(self) -> None:
        fixture = load_json(FIXTURES / "happy-path.json")
        fixture["calls"][0]["response"]["data"]["links"].append("https://team.example.com/leadership")
        transport = FixtureTransport(fixture)
        def resolver(host, *args, **kwargs):
            address = "192.168.9.9" if host == "team.example.com" else "93.184.216.34"
            return [(2, 1, 6, "", (address, 0))]
        result = fetch_official_site(plan(), transport=transport, resolve_dns=True, resolver=resolver, sleeper=lambda _: None)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(len(transport.requests), 1)
        self.assertIn("non-public", result["errors"][0])

    def test_off_domain_provider_redirect_is_blocked(self) -> None:
        fixture = load_json(FIXTURES / "happy-path.json")
        fixture["calls"][0]["response"]["data"]["metadata"]["sourceURL"] = "https://evil.test/"
        result = fetch_official_site(plan(), fixture=fixture, sleeper=lambda _: None)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["page_count"], 0)

    def test_blocked_and_error_states(self) -> None:
        blocked = fetch_official_site(plan(), fixture=load_json(FIXTURES / "blocked-homepage.json"), sleeper=lambda _: None)
        failed = fetch_official_site(plan(), fixture=load_json(FIXTURES / "batch-error.json"), sleeper=lambda _: None)
        self.assertEqual(blocked["status"], "blocked")
        self.assertIn("403", blocked["errors"][0])
        self.assertEqual(failed["status"], "error")
        self.assertEqual(failed["page_count"], 1)
        self.assertIn("upstream unavailable", failed["errors"][0])


class ObservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fetch = happy_fetch()
        cls.observations = extract_observations(cls.fetch)

    def test_footer_contacts(self) -> None:
        values = {row["observed_value"] for row in self.observations["contacts"]}
        self.assertIn("office@example.com", values)
        self.assertIn("+1 (859) 555-0100", values)
        self.assertIn("alex.morgan@example.com", values)
        self.assertFalse(self.observations["business_decisions_made"])
        self.assertFalse(self.observations["role_classification_performed"])
        for item in self.observations["contacts"]:
            self.assertTrue(item["page_evidence"])
            self.assertTrue(item["page_evidence"][0]["evidence_text"])

    def test_all_supported_social_urls(self) -> None:
        platforms = {row["platform"] for row in self.observations["social_links"]}
        self.assertEqual(platforms, {"facebook", "instagram", "youtube", "linkedin", "tiktok", "x"})
        self.assertTrue(any(row["observed_url"] == "https://x.com/exampleequine" for row in self.observations["social_links"]))

    def test_candidate_people_preserve_page_name_and_role(self) -> None:
        people = {(row["observed_name"], row["observed_role"]) for row in self.observations["candidate_people"]}
        self.assertIn(("Alex Morgan", "Stable Operations Coordinator"), people)
        self.assertIn(("Riley Chen", "Community Liaison"), people)
        self.assertIn(("Taylor Brooks", "Veterinary Receptionist"), people)
        self.assertEqual(len(people), 3)
        self.assertNotIn(("Example Equine Centre", "Welcome."), people)
        for person in self.observations["candidate_people"]:
            self.assertTrue(person["page_evidence"])

    def test_candidate_person_without_role_is_retained(self) -> None:
        page={"resolved_url":"https://www.example.com/team","page_index":1,"category":"team","title":"Team","content_sha256":"x"}
        people=_person_candidates(["Jordan Smith"],[("h2","Jordan Smith")],page)
        self.assertEqual(len(people),1)
        self.assertEqual(people[0]["observed_name"],"Jordan Smith")
        self.assertIsNone(people[0]["observed_role"])

    def test_unheaded_staff_name_is_candidate(self) -> None:
        page={"resolved_url":"https://www.example.com/staff","page_index":1,"category":"staff","title":"Staff","content_sha256":"x"}
        people=_person_candidates(["Jordan Smith"],[],page)
        self.assertEqual([(x["observed_name"],x["observed_role"]) for x in people],[("Jordan Smith",None)])

    def test_extraction_rejects_blocked_fetch(self) -> None:
        with self.assertRaises(Exception):
            extract_observations({"schema_id": "a2-firecrawl-official-site-fetch", "status": "blocked", "pages": []})


class DecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.observations = extract_observations(happy_fetch())
        preliminary = build_packet(self.observations)
        proposals = {"run_id": preliminary["run_id"], "company_id": preliminary["company_id"], "reviewed_block_ids": [row["block_id"] for row in preliminary.get("person_evidence_blocks", [])], "proposals": []}
        self.packet = validate_proposals(preliminary, proposals)
        self.people = self.packet["candidate_people"]
        self.contacts = self.packet["contacts"]
        self.socials = self.packet["social_links"]

    def _decisions(self, people_count: int = 2) -> dict:
        people_rows = [
            {"observation_id": row["observation_id"], "retain": index < people_count, "name": row["observed_name"], "role": row.get("observed_role"), "identity_status":"VERIFIED", "company_match_status":"CONFIRMED", "role_status":"CURRENT_AT_COMPANY", "role_priority":"UNKNOWN"}
            for index, row in enumerate(self.people)
        ]
        retained_ids = [row["observation_id"] for index, row in enumerate(self.people) if index < people_count]
        contact_rows = []
        for index, row in enumerate(self.contacts):
            attribution = {"entity_type": "Company", "entity_id": self.packet["company_id"]}
            if index == 0 and retained_ids:
                attribution = {"entity_type": "Person", "person_observation_id": retained_ids[0]}
            contact_rows.append({"observation_id": row["observation_id"], "retain": True, "value": row["observed_value"], "attribution": attribution})
        socials = [{"observation_id": row["observation_id"], "retain": True, "url": row["observed_url"]} for row in self.socials]
        return {"run_id": self.packet["run_id"], "company_id": self.packet["company_id"], "people": people_rows, "contacts": contact_rows, "social_links": socials}

    def test_real_observations_only_and_non_target_roles_allowed(self) -> None:
        result = validate_decisions(self.packet, self._decisions(2))
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["retained_people_count"], 2)
        self.assertFalse(result["role_based_eligibility_filter_applied"])
        self.assertTrue(any(row["attribution"]["entity_type"] == "Company" for row in result["retained_contacts"]))
        self.assertTrue(any(row["attribution"]["entity_type"] == "Person" for row in result["retained_contacts"]))

    def test_missing_role_is_allowed_and_preserved(self) -> None:
        observations=copy.deepcopy(self.observations);observations["candidate_people"][0]["observed_role"]=None;observations["artifact_sha256"]=__import__("build_official_site_plan").sha256_json({k:v for k,v in observations.items() if k!="artifact_sha256"});preliminary=build_packet(observations);packet=validate_proposals(preliminary,{"run_id":preliminary["run_id"],"company_id":preliminary["company_id"],"reviewed_block_ids":[x["block_id"] for x in preliminary.get("person_evidence_blocks",[])],"proposals":[]});person=packet["candidate_people"][0];decisions={"run_id":packet["run_id"],"company_id":packet["company_id"],"people":[{"observation_id":x["observation_id"],"retain":i==0,"name":x["observed_name"],"role":x.get("observed_role"),"role_priority":"UNKNOWN"} for i,x in enumerate(packet["candidate_people"])],"contacts":[],"social_links":[]};result=validate_decisions(packet,decisions);self.assertEqual(result["status"],"valid",result["errors"]);self.assertIsNone(result["retained_people"][0]["role"])

    def test_maximum_two_retained_people(self) -> None:
        result = validate_decisions(self.packet, self._decisions(3))
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("at most two" in error for error in result["errors"]))

    def test_exact_name_and_role_required(self) -> None:
        decisions = self._decisions(1)
        decisions["people"][0]["role"] = decisions["people"][0]["role"].lower()
        result = validate_decisions(self.packet, decisions)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("exact observed role" in error for error in result["errors"]))

    def test_unobserved_values_and_bad_person_attribution_are_rejected(self) -> None:
        decisions = self._decisions(1)
        decisions["contacts"][0]["observation_id"] = "invented-contact"
        decisions["contacts"][1]["attribution"] = {"entity_type": "Person", "person_observation_id": "invented-person"}
        result = validate_decisions(self.packet, decisions)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("unobserved contact" in error for error in result["errors"]))
        self.assertTrue(any("observed person" in error for error in result["errors"]))

    def test_packet_rejects_unevidenced_observation(self) -> None:
        tampered = copy.deepcopy(self.observations)
        tampered["contacts"][0]["page_evidence"] = []
        with self.assertRaises(PacketError):
            build_packet(tampered)


class QuillinRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.observations = extract_observations(load_json(FIXTURES / "quillin-about-fetch.json"))

    def test_prose_people_are_found_without_product_false_positives(self) -> None:
        names = {row["observed_name"] for row in self.observations["candidate_people"]}
        self.assertEqual(names, {"Ralph Quillin", "Donna Quillin", "Rob Windels", "Vince Grupposo"})
        self.assertFalse(any(any(token in row["observed_name"] for token in ("Halter", "Shank", "Snap", "Leather Goods")) for row in self.observations["candidate_people"]))

    def test_shared_surname_and_multiple_full_names_preserve_source_mentions(self) -> None:
        people = {row["observed_name"]: row for row in self.observations["candidate_people"]}
        self.assertIn("Ralph and Donna Quillin", people["Donna Quillin"]["source_mentions"])
        self.assertIn("Rob Windels & Vince Grupposo", people["Rob Windels"]["source_mentions"])

    def test_exact_span_proposals_complete_coverage(self) -> None:
        preliminary = build_packet(self.observations)
        self.assertEqual(preliminary["status"], "ready_for_person_observation_proposals")
        block = next(row for row in preliminary["person_evidence_blocks"] if "Ralph and Donna Quillin" in row["text"] and "Rob Windels & Vince Grupposo" in row["text"])
        proposals = {
            "run_id": preliminary["run_id"],
            "company_id": preliminary["company_id"],
            "reviewed_block_ids": [row["block_id"] for row in preliminary["person_evidence_blocks"]],
            "proposals": [
                {"proposal_id": "ralph", "block_id": block["block_id"], "person_name": "Ralph Quillin", "source_mention": "Ralph and Donna Quillin", "derivation": "shared_surname_split", "role_text": None, "relationship_to_company": "current", "company_relationship_evidence": block["text"]},
                {"proposal_id": "donna", "block_id": block["block_id"], "person_name": "Donna Quillin", "source_mention": "Ralph and Donna Quillin", "derivation": "shared_surname_split", "role_text": None, "relationship_to_company": "current", "company_relationship_evidence": block["text"]},
                {"proposal_id": "rob", "block_id": block["block_id"], "person_name": "Rob Windels", "source_mention": "Rob Windels & Vince Grupposo", "derivation": "multiple_full_names", "role_text": None, "relationship_to_company": "current", "company_relationship_evidence": block["text"]},
                {"proposal_id": "vince", "block_id": block["block_id"], "person_name": "Vince Grupposo", "source_mention": "Rob Windels & Vince Grupposo", "derivation": "multiple_full_names", "role_text": None, "relationship_to_company": "current", "company_relationship_evidence": block["text"]},
            ],
        }
        augmented = validate_proposals(preliminary, proposals)
        self.assertEqual(augmented["status"], "ready_for_decision", augmented.get("proposal_errors"))
        self.assertEqual(augmented["person_extraction_coverage"]["status"], "complete")
        self.assertEqual({row["observed_name"] for row in augmented["candidate_people"]}, {"Ralph Quillin", "Donna Quillin", "Rob Windels", "Vince Grupposo"})

    def test_unreviewed_blocks_or_invented_names_are_rejected(self) -> None:
        preliminary = build_packet(self.observations)
        block = preliminary["person_evidence_blocks"][0]
        proposals = {"run_id": preliminary["run_id"], "company_id": preliminary["company_id"], "reviewed_block_ids": [], "proposals": [{"proposal_id": "invented", "block_id": block["block_id"], "person_name": "Invented Person", "source_mention": block["text"][:40], "derivation": "exact", "role_text": None, "relationship_to_company": "current", "company_relationship_evidence": block["text"]}]}
        result = validate_proposals(preliminary, proposals)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(result["proposal_errors"])


class CompileTests(unittest.TestCase):
    def test_all_dedicated_scripts_compile(self) -> None:
        for name in SCRIPT_NAMES:
            path = SCRIPTS / name
            with self.subTest(name=name):
                compile(path.read_text(encoding="utf-8"), str(path), "exec")


if __name__ == "__main__":
    unittest.main(verbosity=2)
