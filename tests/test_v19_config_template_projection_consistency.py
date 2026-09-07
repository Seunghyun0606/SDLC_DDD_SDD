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


CONFIG = load("consistency_config", "runtime_config_v19.py")
TAILOR = load("consistency_tailor", "tailoring_runtime.py")

EXPECTED_PROFILES = {
    "internal": "STANDARD_5",
    "customer": "CUSTOMER_STANDARD_3",
    "pm": "PM_STANDARD",
}
FAST_PRECONDITIONS = [
    "INTENT_DECOMPOSED",
    "AS_IS_SOURCE_ANALYZED",
    "IMPACT_CHECKED",
]


class V19ConfigTemplateProjectionConsistencyTest(unittest.TestCase):
    def read(self, rel: str) -> str:
        return (ROOT / rel).read_text(encoding="utf-8")

    def json(self, rel: str) -> dict:
        return json.loads(self.read(rel))

    def profile(self, profile_id: str) -> dict:
        data, _ = TAILOR.load_profile(ROOT, profile_id)
        return data

    def test_default_profiles_match_runtime_config_and_guides(self):
        self.assertEqual(EXPECTED_PROFILES, TAILOR.DEFAULT_PROFILES)
        example = CONFIG.load_config(ROOT / "sdlc/config/project.example.yaml")
        for audience, profile_id in EXPECTED_PROFILES.items():
            self.assertEqual(profile_id, CONFIG.nested(example, "documents", audience, "profile"))

        for rel in [
            "docs/00_시작/START_HERE.md",
            "docs/00_시작/02_PROJECT_설정가이드.md",
            "docs/00_시작/03_TAILORING_설정가이드.md",
        ]:
            text = self.read(rel)
            for profile_id in EXPECTED_PROFILES.values():
                self.assertIn(profile_id, text, rel)
            self.assertIn("STAGE_ORIENTED_FULL", text, rel)
            self.assertTrue(
                any(marker in text for marker in ["기본값이 아니다", "신규 프로젝트에서 Full을 기본값으로 두지 않는다"]),
                rel,
            )

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

        for rel in [
            "sdlc/agent/skills/work/SKILL.md",
            "docs/00_시작/04_TEMPLATE_및_산출물_가이드.md",
        ]:
            text = self.read(rel)
            for key in FAST_PRECONDITIONS:
                self.assertIn(key, text, rel)

        start = self.read("docs/00_시작/START_HERE.md")
        project_guide = self.read("docs/00_시작/02_PROJECT_설정가이드.md")
        for phrase in ["Requirement Intent Decomposition", "AS-IS Source Analysis", "Impact Check"]:
            self.assertIn(phrase, start)
            self.assertIn(phrase, project_guide)

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
        for row in readiness["conditional_fields"]:
            self.assertIn(row["trigger"], template, row["field_id"])

    def test_standard_internal_profile_is_five_real_human_templates(self):
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
        self.assertEqual("v1.9.0-redteam-simplified", contract["candidate_design"])

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
        self.assertTrue(any("특정 Internal Profile" in x for x in contract["principles"]))
        self.assertTrue(all(row["authoring"] == "GENERATED_VIEW" for row in profile["artifacts"].values()))
        self.assertIn('"business_truth_authority": False', runtime)
        self.assertIn('"customer_edit_auto_updates_canonical": False', runtime)
        for text in [guide, skill]:
            self.assertIn("특정 Internal Profile", text)
            self.assertIn("Business Truth", text)


if __name__ == "__main__":
    unittest.main()
