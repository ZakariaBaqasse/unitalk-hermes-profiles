#!/usr/bin/env python3
"""Dedicated tests for the Step 11 official-Facebook Apify fallback."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "evaluations" / "step11" / "fixtures" / "apify"
sys.path.insert(0, str(ROOT / "scripts"))

import apify_facebook_page_contact as connector
import build_apify_facebook_requests as builder
import validate_apify_facebook_results as validator


def read(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def one_request(batch: dict, company_id: str = "company-trigger") -> dict:
    result = copy.deepcopy(batch)
    result["requests"] = [item for item in result["requests"] if item["company_id"] == company_id]
    result["request_count"] = len(result["requests"])
    return result


class OfficialFacebookApifyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = read("companies.json")
        cls.batch = builder.build_requests(cls.source)

    def test_trigger_when_company_email_or_phone_is_missing(self):
        ids = {item["company_id"] for item in self.batch["requests"]}
        self.assertEqual(ids, {"company-trigger", "company-duplicate"})
        trigger = next(item for item in self.batch["requests"] if item["company_id"] == "company-trigger")
        self.assertEqual(trigger["missing_fields"], ["company.company_email", "company.company_phone"])

    def test_no_trigger_when_company_email_and_phone_exist_across_sources(self):
        self.assertNotIn("company-complete", {item["company_id"] for item in self.batch["requests"]})
        blocked = next(item for item in self.batch["blocked_requests"] if item["company_id"] == "company-complete")
        self.assertIn("company_email_and_phone_already_present_across_a1_twenty_and_website", blocked["reasons"])

    def test_exact_url_comes_from_validated_official_site_evidence(self):
        request = next(item for item in self.batch["requests"] if item["company_id"] == "company-trigger")
        self.assertEqual(request["actor_id"], "apify~facebook-page-contact-information")
        self.assertEqual(request["actor_input"], {"pages": ["https://www.facebook.com/BluegrassFarm/"], "language": "en-US"})
        self.assertEqual(request["facebook_url"], request["official_site_evidence"]["facebook_url"])
        self.assertEqual(request["missing_channels"], ["email", "phone"])
        self.assertEqual(request["official_site_evidence"]["status"], "validated")
        bad = copy.deepcopy(self.source["companies"][0])
        bad["facebook_url"] = "https://www.facebook.com/Unproven/"
        bad.pop("official_site_evidence")
        output = builder.build_requests({"run_id": "bad", "companies": [bad]})
        self.assertEqual(output["requests"], [])
        self.assertIn("no_validated_official_site_facebook_url", output["blocked_requests"][0]["reasons"])

    def test_one_actor_run_per_company_and_no_company_count_max(self):
        base = self.source["companies"][0]
        companies = []
        for index in range(80):
            company = copy.deepcopy(base)
            company["company_id"] = f"company-{index:03d}"
            company["company_name"] = f"Company {index:03d} Farm"
            company["official_site_evidence"][0]["value"] = f"https://www.facebook.com/Company{index:03d}Farm/"
            companies.append(company)
        output = builder.build_requests({"run_id": "unbounded", "companies": companies})
        self.assertEqual(output["request_count"], 80)
        self.assertIsNone(output["controls"]["company_count_max"])
        duplicate = copy.deepcopy(companies[0])
        output = builder.build_requests({"run_id": "dedupe", "companies": [companies[0], duplicate]})
        self.assertEqual(output["request_count"], 1)
        self.assertIn("duplicate_company", output["blocked_requests"][0]["reason"])

    def test_success_yields_company_only_append_candidates_and_audit(self):
        result = connector.run_batch(self.batch, read("provider-success.json"), max_polls=3, poll_interval=0, timeout=1)
        self.assertEqual(result["external_calls"], 0)
        self.assertEqual(result["audit"]["operation_counts"], {"actor_run_posts": 2, "status_polls": 2, "dataset_gets": 2})
        first = next(item for item in result["results"] if item["company_id"] == "company-trigger")
        for key in ("build_sha256", "input_sha256", "run_response_sha256", "dataset_sha256", "output_sha256"):
            self.assertRegex(first["audit"][key], r"^[0-9a-f]{64}$")
        self.assertEqual(first["audit"]["cost"]["usageTotalUsd"], 0.0066)
        validated = validator.validate_results(result)
        self.assertEqual(validated["status"], "valid")
        self.assertEqual(validated["results"][0]["facebook_url"], "https://www.facebook.com/BluegrassFarm/")
        self.assertIn("company_candidates", validated["results"][0])
        candidates = [item for item in validated["append_candidates"] if item["company_id"] == "company-trigger"]
        self.assertEqual({item["field_key"] for item in candidates}, {"company.company_email", "company.company_phone"})
        self.assertTrue(all(item["entity_type"] == "Company" and item["operation"] == "append_candidate" for item in candidates))
        self.assertTrue(all(item["write_authorized"] is False for item in candidates))
        self.assertFalse(any("person" in key.casefold() for item in candidates for key in item))

    def test_duplicate_or_no_change_result_emits_no_candidate(self):
        result = connector.run_batch(self.batch, read("provider-success.json"), max_polls=3, poll_interval=0, timeout=1)
        validated = validator.validate_results(result)
        duplicate = next(item for item in validated["companies"] if item["company_id"] == "company-duplicate")
        self.assertEqual(duplicate["status"], "no_change")
        self.assertEqual(duplicate["append_candidates"], [])

    def test_mismatched_page_is_rejected(self):
        batch = one_request(self.batch)
        result = connector.run_batch(batch, read("provider-mismatch.json"), max_polls=2, poll_interval=0, timeout=1)
        validated = validator.validate_results(result)
        self.assertEqual(validated["status"], "invalid")
        self.assertIn("does not match", validated["companies"][0]["errors"][0])
        self.assertEqual(validated["append_candidates"], [])

    def test_personal_profile_data_is_rejected(self):
        batch = one_request(self.batch)
        result = connector.run_batch(batch, read("provider-personal-profile.json"), max_polls=2, poll_interval=0, timeout=1)
        validated = validator.validate_results(result)
        self.assertEqual(validated["status"], "invalid")
        self.assertEqual(validated["companies"][0]["errors"], ["personalProfileData is prohibited"])

    def test_failure_has_one_start_and_no_retry_poll_resurrection_or_dataset(self):
        batch = one_request(self.batch)
        with patch.dict(os.environ, {}, clear=True):
            result = connector.run_batch(batch, read("provider-failure.json"), max_polls=10, poll_interval=0, timeout=1)
        row = result["results"][0]
        self.assertEqual(row["terminal_status"], "failed")
        self.assertEqual(row["audit"]["operation_counts"], {"actor_run_posts": 1, "status_polls": 0, "dataset_gets": 0})
        self.assertIsNone(row["audit"]["dataset_sha256"])
        self.assertEqual(result["controls"], {"max_retries": 0, "resurrection": False, "fallback_actor": None, "max_polls": 10})

    def test_async_post_bounded_poll_and_dataset_protocol_without_live_call(self):
        item = one_request(self.batch)["requests"][0]
        calls = []

        def fake_transport(method, url, token, body, timeout):
            calls.append((method, url, token, body, timeout))
            if method == "POST":
                return {"data": {"id": "run-protocol", "status": "RUNNING", "buildId": "build-protocol"}}
            if "/actor-runs/" in url:
                return {"data": {"id": "run-protocol", "status": "SUCCEEDED", "buildId": "build-protocol", "defaultDatasetId": "dataset-protocol"}}
            if "/datasets/" in url:
                return [{"pageUrl": item["exact_facebook_url"], "title": item["company_name"], "email": None, "phone": None, "website": None}]
            raise AssertionError((method, url))

        row = connector.execute_one(item, token="test-token", fixture=None, max_polls=2, poll_interval=0, timeout=1, transport=fake_transport)
        self.assertEqual(row["terminal_status"], "succeeded")
        self.assertEqual([call[0] for call in calls], ["POST", "GET", "GET"])
        self.assertIn("/actors/apify~facebook-page-contact-information/runs", calls[0][1])
        self.assertNotIn("run-sync", calls[0][1])
        self.assertEqual(calls[0][3], item["actor_input"])
        self.assertTrue(calls[2][1].endswith("/items?clean=true&format=json"))

    def test_multiple_items_and_unexpected_data_are_rejected(self):
        batch = one_request(self.batch)
        result = connector.run_batch(batch, read("provider-success.json"), max_polls=3, poll_interval=0, timeout=1)
        row = result["results"][0]
        row["dataset_items"].append(copy.deepcopy(row["dataset_items"][0]))
        self.assertEqual(validator.validate_results(result)["status"], "invalid")
        result = connector.run_batch(batch, read("provider-success.json"), max_polls=3, poll_interval=0, timeout=1)
        result["results"][0]["dataset_items"][0]["likes"] = 100
        checked = validator.validate_results(result)
        self.assertEqual(checked["status"], "invalid")
        self.assertIn("unexpected dataset fields", checked["companies"][0]["errors"][0])

    def test_cli_fixture_end_to_end_and_failed_cli_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            requests = work / "requests.json"
            results = work / "results.json"
            candidates = work / "candidates.json"
            commands = [
                [sys.executable, str(ROOT / "scripts" / "build_apify_facebook_requests.py"), str(FIXTURES / "companies.json"), "--output", str(requests)],
                [sys.executable, str(ROOT / "scripts" / "apify_facebook_page_contact.py"), str(requests), "--fixture", str(FIXTURES / "provider-success.json"), "--poll-interval", "0", "--output", str(results)],
                [sys.executable, str(ROOT / "scripts" / "validate_apify_facebook_results.py"), str(results), "--output", str(candidates)],
            ]
            for command in commands:
                completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            output = json.loads(candidates.read_text(encoding="utf-8"))
            self.assertEqual(output["status"], "valid")
            self.assertEqual(output["candidate_count"], 2)
            failed_requests = work / "failed-requests.json"
            failed_results = work / "failed-results.json"
            failed_requests.write_text(json.dumps(one_request(self.batch)), encoding="utf-8")
            completed = subprocess.run([
                sys.executable, str(ROOT / "scripts" / "apify_facebook_page_contact.py"), str(failed_requests),
                "--fixture", str(FIXTURES / "provider-failure.json"), "--poll-interval", "0", "--output", str(failed_results),
            ], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 1, completed.stdout + completed.stderr)
            failed = json.loads(failed_results.read_text(encoding="utf-8"))
            self.assertEqual(failed["audit"]["operation_counts"]["actor_run_posts"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
