#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("resolve_discovery_location.py")


def load_module():
    spec = importlib.util.spec_from_file_location("resolve_discovery_location", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class LocationResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()
        cls.config = cls.module.load_config(cls.module.DEFAULT_CONFIG)

    def test_resolves_us_name_without_user_codes(self):
        location = self.module.resolve(self.config, "United States", "Kentucky", "Lexington")
        self.assertEqual(location["country_code"], "US")
        self.assertEqual(location["region_code"], "KY")
        self.assertEqual(location["location_key"], "US|KY|lexington")

    def test_resolves_australia_name_without_user_codes(self):
        location = self.module.resolve(self.config, "Australia", "Victoria", "Melbourne")
        self.assertEqual(location["country_code"], "AU")
        self.assertEqual(location["region_code"], "VIC")
        self.assertEqual(location["location_key"], "AU|VIC|melbourne")

    def test_resolves_new_zealand_name_without_user_codes(self):
        location = self.module.resolve(self.config, "New Zealand", "Waikato", "Hamilton")
        self.assertEqual(location["country_code"], "NZ")
        self.assertEqual(location["region_code"], "WKO")
        self.assertEqual(location["location_key"], "NZ|WKO|hamilton")

    def test_same_city_name_has_distinct_scopes(self):
        australia = self.module.resolve(self.config, "Australia", "Victoria", "Melbourne")
        united_states = self.module.resolve(self.config, "United States", "Arkansas", "Melbourne")
        self.assertNotEqual(australia["location_key"], united_states["location_key"])

    def test_missing_region_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "region"):
            self.module.resolve(self.config, "Australia", "", "Melbourne")

    def test_country_code_conflict_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "conflicts"):
            self.module.resolve(self.config, "Australia", "Victoria", "Melbourne", "US")

    def test_region_code_conflict_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "conflicts"):
            self.module.resolve(self.config, "New Zealand", "Waikato", "Hamilton", "NZ", "AUK")

    def test_unapproved_country_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "unsupported or ambiguous"):
            self.module.resolve(self.config, "United Kingdom", "England", "Newmarket")


if __name__ == "__main__":
    unittest.main()
