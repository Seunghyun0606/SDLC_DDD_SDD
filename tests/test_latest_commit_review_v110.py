from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "sdlc/scripts"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


TAILOR = load_module("v110_review_tailoring", "tailoring_runtime.py")
SCAFFOLD = load_module("v110_review_scaffold", "build_project_scaffold.py")


class LatestCommitReviewV110Test(unittest.TestCase):
    def test_direct_tailoring_defaults_match_current_project_config_defaults(self):
        profiles = TAILOR.project_profile_ids({"documents": {}})
        self.assertEqual(TAILOR.CONFIG.DEFAULT_ENGINEERING_PROFILE, profiles["internal"])
        self.assertEqual("ENGINEERING_SDD_COMPACT", profiles["internal"])
        self.assertEqual(TAILOR.CONFIG.DEFAULT_CUSTOMER_PROFILE, profiles["customer"])
        self.assertEqual("CUSTOMER_STANDARD_3", profiles["customer"])
        self.assertEqual(TAILOR.CONFIG.DEFAULT_PM_PROFILE, profiles["pm"])
        self.assertEqual("PM_STANDARD", profiles["pm"])

    def test_scaffold_bundled_optional_matches_actual_default_distribution(self):
        contract = json.loads(
            (ROOT / "sdlc/design/contracts/project-scaffold-contract.json").read_text(encoding="utf-8")
        )
        self.assertEqual(7, contract["schema_version"])
        bundled = set(contract["distribution_boundary"]["PROJECT_BUNDLED_OPTIONAL"])
        expected = {
            "CUSTOMER_WATERFALL_FULL",
            "sdlc/scripts/component_state_runtime.py",
            "sdlc/scripts/impact_learning_runtime.py",
            "sdlc/scripts/unexpected_discovery_runtime.py",
            "sdlc/scripts/architecture_check.py",
            "sdlc/config/architecture-rules.json",
            "sdlc/scripts/sdlc_metrics_runtime.py",
        }
        self.assertTrue(expected <= bundled)
        self.assertTrue(contract["bundled_optional_policy"]["included_in_default_scaffold"])
        self.assertTrue(contract["bundled_optional_policy"]["activation_optional"])

        selected = set(SCAFFOLD.select_files(ROOT))
        for rel in expected - {"CUSTOMER_WATERFALL_FULL"}:
            self.assertIn(rel, selected)
        self.assertIn("sdlc/tailoring/standard/CUSTOMER_WATERFALL_FULL.yaml", selected)

    def test_true_optional_extensions_are_not_silently_bundled(self):
        selected = set(SCAFFOLD.select_files(ROOT))
        for rel in [
            "sdlc/scripts/build_reverse_inputs.py",
            "sdlc/scripts/detect_source_drift.py",
            "sdlc/scripts/run_source_reverse_check.py",
            "sdlc/scripts/generate_program_spec_reverse_candidate.py",
            "sdlc/scripts/extract_document_evidence.py",
            "sdlc/scripts/normalize_external_evidence.py",
        ]:
            self.assertNotIn(rel, selected)

    def test_active_metadata_uses_external_current_head_evidence_pointer(self):
        metadata = (ROOT / "framework/design/branch-version.yaml").read_text(encoding="utf-8")
        self.assertIn("authoritative_review: framework/validation/LATEST_COMMIT_REVIEW_V110.md", metadata)
        self.assertIn("current_head_ci_required: true", metadata)
        self.assertIn("exact_run_ids_and_test_count_are_external_evidence: true", metadata)
        self.assertNotIn("last_verified_head_before_framework_governance_refresh", metadata)
        self.assertNotIn("full_unittest_count:", metadata)

    def test_inventory_distinguishes_bundled_optional_from_separate_optional(self):
        inventory = (ROOT / "framework/ASSET_INVENTORY_V110.md").read_text(encoding="utf-8")
        self.assertIn("PROJECT_BUNDLED_OPTIONAL", inventory)
        self.assertIn("component_state_runtime.py", inventory)
        self.assertIn("CUSTOMER_WATERFALL_FULL", inventory)
        self.assertIn("별도 Brownfield/Document-ingest/External-tool Extension", inventory)


if __name__ == "__main__":
    unittest.main()
