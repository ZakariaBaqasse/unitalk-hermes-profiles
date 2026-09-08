import importlib.util
import json
import unittest
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[3]
SKILL = PROFILE / "skills" / "ranked-prospect-review-package"
SCRIPT = SKILL / "scripts" / "build_review_package.py"
FIXTURE = PROFILE / "evaluations" / "wave3" / "fixtures" / "james-review-input.json"
POLICY = PROFILE / "configurations" / "operations" / "a1-runtime-policy-v1.yaml"


def load_builder():
    spec = importlib.util.spec_from_file_location("build_review_package", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TwentyIntegrationStatusTests(unittest.TestCase):
    def test_runtime_policy_allows_company_only_staging(self):
        policy = POLICY.read_text(encoding="utf-8")
        self.assertIn("status: company_review_staging_enabled", policy)
        self.assertIn("allowed_objects: [companies,people]", policy)
        self.assertIn("people_write: permitted_when_linked_to_staged_company", policy)
        self.assertNotIn("twenty_write_until_staging_is_implemented", policy)

    def test_review_schema_supports_twenty_lifecycle(self):
        schema = json.loads((SKILL / "references" / "review-package.schema.json").read_text())
        twenty = schema["properties"]["integration_status"]["properties"]["twenty"]
        self.assertEqual(
            set(twenty["enum"]),
            {"not_staged", "staged", "possible_match", "sync_failed"},
        )

    def test_new_review_package_defaults_to_not_staged(self):
        builder = load_builder()
        package = builder.build(json.loads(FIXTURE.read_text()))
        self.assertEqual(package["schema_version"], "1.1.0")
        self.assertEqual(package["integration_status"]["twenty"], "not_staged")
        limitations = package["candidates"][0]["integration_limitations"]
        self.assertIn("Mandatory Twenty Company staging has not completed for this review package.", limitations)
        self.assertNotIn("Twenty staging and review status are unavailable.", limitations)


if __name__ == "__main__":
    unittest.main()
