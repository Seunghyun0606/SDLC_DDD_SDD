from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "sdlc" / "scripts"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CONFIG = load("consistency_config", "project_config.py")
TAILOR = load("consistency_tailor", "tailoring_runtime.py")

EXPECTED_PROJECT_PROFILES = {
    "engineering": "ENGINEERING_SDD_COMPACT",
    "customer": "CUSTOMER_STANDARD_3",
    "pm": "PM_STANDARD",
}
FAST_PRECONDITIONS = [
    "INTENT_DECOMPOSED",
    "AS_IS_SOURCE_ANALYZED",
    "IMPACT_CHECKED",
]


class V19ConfigTemplateProjectionConsistencyTest(unittest.TestCase):
    """Cross-version consistency: preserve v1.9 contracts without freezing v1.9 topology as v1.10 default."""

    def read(self, rel: str) -> str:
        return (ROOT / rel).read_text(encoding="utf-8")

    def json(self, rel: str) -> dict:
        return json.loads(self.read(rel))

    def profile(self, profile_id: str) -> dict:
        data, _ = TAILOR.load_profile(ROOT, profile_id)
        return data

    def test_default_profiles_match_project_config_and_guides(self):
        raw = CONFIG.load_config(ROOT / "sdlc/config/project.example.yaml")
        example = CONFIG.normalize_document_profiles(raw)
        for audience, profile_id in EXPECTED_PROJECT_PROFILES.items():
            self.assertEqual(profile_id, CONFIG.nested(example, "documents", audience, "profile"))

        # Legacy internal alias must resolve to the same effective Engineering profile rather than
        # becoming a second source of truth.
        self.assertEqual(
            EXPECTED_PROJECT_PROFILES["engineering"],
            CONFIG.nested(example, "documents", "internal", "profile"),
        )

        start = self.read("docs/00_시작/START_HERE.md")
        project_guide = self.read("docs/00_시작/02_PROJECT_설정가이드.md")
        tailoring_guide = self.read("docs/00_시작/03_TAILORING_설정가이드.md")
        for text, rel in [
            (start, "START_HERE"),
            (project_guide, "PROJECT_GUIDE"),
            (tailoring_guide, "TAILORING_GUIDE"),
        ]:
            self.assertIn("ENGINEERING_SDD_COMPACT", text, rel)
            self.assertIn("CUSTOMER_STANDARD_3", text, rel)
            self.assertIn("STAGE_ORIENTED_FULL", text, rel)
            self.assertTrue(
                any(marker in text for marker in ["Legacy", "기본값이 아니다", "호환"]),
                rel,
            )
        self.assertIn("PM_STANDARD", start)
        self.assertIn("PM_STANDARD", project_guide)

    def test_fast_path_preconditions_match_policy_runtime_skill_and_guide(self):
        policy = self.json("sdlc/config/change-execution-policy.json")
        for level in ["L1", "L2"]:
            self.assertEqual(FAST_PRECONDITIONS, policy["levels"][level]["source_write_preconditions"])
            semantic = set(policy["levels"][level]["semantic_work"])
            self.assertIn("INTENT_DECOMPOSITION", semantic)
            self.assertIn("AS_IS_SOURCE_ANALYSIS", semantic)
            self.assertTrue({"IMPACT_SANITY_CHECK", "IMPACT"} & semantic)

        runtime = self.read("sdlc/scripts/run_work.py")
        self.assertIn("validate_fast_path_prewrite_analysis", runtime)
        self.assertIn('policy.get("source_write_preconditions")', runtime)
        self.assertIn("if not source_changed", runtime)

        skill = self.read("sdlc/agent/skills/work/SKILL.md")
        guide = self.read("docs/00_시작/04_TEMPLATE_및_산출물_가이드.md")
        for key in FAST_PRECONDITIONS:
            self.assertIn(key, skill)
            self.assertIn(key, guide)

        start = self.read("docs/00_시작/START_HERE.md")
        project_guide = self.read("docs/00_시작/02_PROJECT_설정가이드.md")
        # Human guides must retain the semantic meaning; exact machine gate identifiers are not the
        # user-facing contract outside the implementation-oriented template guide.
        for phrase in ["Requirement Intent Decomposition", "AS-IS Source Analysis", "Impact Check"]:
            self.assertIn(phrase, project_guide)
        self.assertIn("AS-IS Source", start)
        self.assertIn("Impact", start)

    def test_program_readiness_config_template_contract_and_guide_match(self):
        readiness = self.json("sdlc/config/program-spec-readiness.json")
        package = self.json("sdlc/design/contracts/harness-package-contract.json")
        template = self.read("sdlc/templates/core/program-spec.md")
        guide = self.read("docs/00_시작/04_TEMPLATE_및_산출물_가이드.md")

        self.assertEqual("CORE_PLUS_RISK_TRIGGERED_CONDITIONAL", readiness["representation"])
        self.assertEqual(6, len(readiness["core_required_field_ids"]))
        self.assertEqual(17, len(readiness["legacy_compatibility"]["required_field_ids"]))
        self.assertEqual(6, package["program_readiness_rules"]["core_required_item_count"])
        self.assertEqual(17, package["program_readiness_rules"]["legacy_full_item_count"])
        self.assertEqual(readiness["representation"], package["program_readiness_rules"]["representation"])

        self.assertIn("Core Required 6개", template)
        self.assertIn("LEGACY_FULL_17", template)
        self.assertIn("Core Required 6 + Risk-triggered Conditional", guide)
        self.assertIn("LEGACY_FULL_17", guide)
        for row in readiness["conditional_fields"]:
            self.assertIn(row["trigger"], template, row["field_id"])

    def test_standard_internal_profile_is_five_real_human_templates(self):
        # STANDARD_5 remains a valid Legacy/Formal compatibility profile; it is simply no longer
        # the new-project Engineering default.
        profile = self.profile("STANDARD_5")
        artifacts = profile["artifacts"]
        self.assertEqual(5, len(artifacts))
        for artifact_id, row in artifacts.items():
            self.assertEqual("INTERNAL_IT", row["audience"], artifact_id)
            self.assertEqual("AGENT_DRAFT_HUMAN_REVIEW", row["authoring"], artifact_id)
            self.assertTrue((ROOT / row["template"]).is_file(), row["template"])
            self.assertTrue(str(row["output_path"]).startswith("docs/10_산출물/"), artifact_id)

    def test_customer_profile_contract_profile_config_and_templates_match(self):
        profile = self.profile("CUSTOMER_STANDARD_3")
        contract = self.json("sdlc/design/contracts/customer-document-contract.json")
        customer_config = self.json("sdlc/config/customer-document-profile.example.json")
        artifacts = profile["artifacts"]

        active = contract["active_document_types"]
        self.assertEqual(active, customer_config["active_document_types"])
        self.assertEqual(set(active), set(artifacts))
        self.assertEqual(set(active), set(contract["document_types"]))

        for artifact_id in active:
            row = artifacts[artifact_id]
            definition = contract["document_types"][artifact_id]
            self.assertEqual("CUSTOMER", row["audience"], artifact_id)
            self.assertEqual("GENERATED_VIEW", row["authoring"], artifact_id)
            self.assertNotIn("artifacts", row["sources"], artifact_id)
            self.assertTrue(row["sources"].get("canonical"), artifact_id)
            self.assertTrue(set(row["sources"]["stages"]) <= set(definition["stages"]), artifact_id)
            self.assertEqual(Path(row["template"]).name, definition["template"], artifact_id)

            template = self.read(row["template"])
            for section in contract["required_base_sections"]:
                self.assertIn("## " + section, template, f"{artifact_id}:{section}")
            for section in definition["projection_sections"]:
                self.assertIn("## " + section, template, f"{artifact_id}:{section}")
            for section_id in definition["required_add"]:
                heading = section_id.replace("_", " ")
                self.assertIn("## " + heading, template, f"{artifact_id}:{heading}")

    def test_customer_projection_remains_generated_view_not_business_truth(self):
        contract = self.json("sdlc/design/contracts/customer-document-contract.json")
        profile = self.profile("CUSTOMER_STANDARD_3")
        runtime = self.read("sdlc/scripts/customer_projection_runtime.py")
        guide = self.read("docs/00_시작/03_TAILORING_설정가이드.md")
        skill = self.read("sdlc/agent/skills/work/SKILL.md")

        self.assertTrue(any("새로운 업무 사실" in x for x in contract["principles"]))
        self.assertTrue(any("Internal Profile" in x for x in contract["principles"]))
        self.assertTrue(all(row["authoring"] == "GENERATED_VIEW" for row in profile["artifacts"].values()))
        self.assertIn('"business_truth_authority": False', runtime)
        self.assertIn('"customer_edit_auto_updates_canonical": False', runtime)
        self.assertIn("Engineering Profile ID", guide)
        self.assertIn("Business Truth", skill)
        self.assertIn("Customer Runtime", guide)
        self.assertNotIn("internal_profile_id", runtime)
        self.assertNotIn("expected Engineering filename", runtime)


if __name__ == "__main__":
    unittest.main()
