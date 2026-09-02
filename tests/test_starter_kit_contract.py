import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "sdlc/design/contracts/starter-kit-contract.json").read_text(encoding="utf-8"))


class StarterKitContractTest(unittest.TestCase):
    def test_greenfield_and_brownfield_are_separate_modes(self):
        self.assertEqual({"GREENFIELD", "BROWNFIELD"}, set(CONTRACT["modes"]))

    def test_greenfield_can_start_without_source(self):
        green = CONTRACT["modes"]["GREENFIELD"]
        self.assertFalse(green["source_required_to_start"])
        self.assertIn("requirement_sources", green["startable_minimum"])

    def test_brownfield_requires_repository_to_confirm_source_analysis(self):
        brown = CONTRACT["modes"]["BROWNFIELD"]
        self.assertTrue(brown["source_required_to_confirm_source_analysis"])
        self.assertIn("repository.reference", brown["startable_minimum"])
        self.assertIn("analysis_seed.text", brown["startable_minimum"])

    def test_brownfield_impact_contract_is_not_file_only(self):
        relations = set(CONTRACT["modes"]["BROWNFIELD"]["impact_required_relation_types"])
        for marker in {"CALLER", "CALLEE", "DATA_READ_WRITE", "EXTERNAL_INTERFACE", "CONFIG_FEATURE_FLAG", "TEST"}:
            self.assertIn(marker, relations)
        self.assertTrue(CONTRACT["modes"]["BROWNFIELD"]["coverage_gaps_must_be_reported"])
        self.assertTrue(CONTRACT["modes"]["BROWNFIELD"]["project_specific_impact_adapter_required"])
        self.assertEqual("PARTIAL_PROJECT_ADAPTER_REQUIRED", CONTRACT["modes"]["BROWNFIELD"]["missing_project_adapter_status"])

    def test_missing_recommended_input_remains_non_blocking(self):
        self.assertTrue(CONTRACT["shared_invariants"]["missing_recommended_input_is_non_blocking"])

    def test_source_does_not_auto_promote_business_truth(self):
        self.assertTrue(CONTRACT["shared_invariants"]["business_truth_is_not_inferred_from_source_automatically"])
        self.assertFalse(CONTRACT["reverse_engineering"]["automatic_business_truth_promotion"])

    def test_reverse_engineering_only_enables_drift_check_in_core(self):
        reverse = CONTRACT["reverse_engineering"]
        self.assertEqual("PARTIAL_CORE_ENABLED", reverse["status"])
        self.assertEqual(["DRIFT_CHECK"], reverse["core_enabled_scopes"])
        self.assertIn("REVERSE_SPEC", reverse["enhancement_scopes"])
        self.assertFalse(reverse["automatic_artifact_rewrite"])

    def test_starter_documents_exist(self):
        for mode in ("greenfield", "brownfield"):
            self.assertTrue((ROOT / f"sdlc/starter-kits/{mode}/README.md").is_file())
            self.assertTrue((ROOT / f"sdlc/starter-kits/{mode}/starter-manifest.example.yaml").is_file())

    def test_setup_routes_to_mode_specific_starter_kits(self):
        setup = (ROOT / ".cursor/skills/setup/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("sdlc/starter-kits/greenfield/", setup)
        self.assertIn("sdlc/starter-kits/brownfield/", setup)
        self.assertIn("greenfield-default", setup)
        self.assertIn("brownfield-auto", setup)

    def test_single_user_onboarding_entrypoint_is_connected(self):
        onboarding = CONTRACT["user_onboarding"]
        self.assertFalse(onboarding["internal_framework_structure_required_for_user"])
        self.assertEqual(["project_name", "project_mode", "delivery_profile"], onboarding["primary_setup_inputs"])
        self.assertTrue(onboarding["agent_draft_first"])
        self.assertTrue(onboarding["human_reviews_decisions_not_blank_templates"])
        self.assertTrue(onboarding["unknown_information_remains_open"])
        self.assertEqual(".sdlc/project.yaml", onboarding["project_config"])
        self.assertEqual("CONNECTED", onboarding["zero_to_one_requirement_intake"])
        self.assertTrue(onboarding["intake_returns_concrete_rq_target"])
        self.assertTrue((ROOT / onboarding["entrypoint"]).is_file())
        self.assertTrue((ROOT / onboarding["project_setup_guide"]).is_file())

    def test_setup_skill_points_to_start_here_and_real_intake(self):
        setup = (ROOT / ".cursor/skills/setup/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("docs/00_시작/START_HERE.md", setup)
        self.assertIn(".sdlc/project.yaml", setup)
        self.assertIn("Fast Path — 최초 5개 질문", setup)
        self.assertIn("harness.py intake", setup)
        self.assertIn("내부 Machine taxonomy를 사용자 입력 양식으로 요구하지 않는다", setup)

    def test_project_profile_no_longer_defaults_auto_to_brownfield(self):
        profile = (ROOT / "sdlc/config/project-profile.example.yaml").read_text(encoding="utf-8")
        self.assertIn("name: AUTO", profile)
        self.assertIn("GREENFIELD: greenfield-default", profile)
        self.assertIn("BROWNFIELD: brownfield-auto", profile)


if __name__ == "__main__":
    unittest.main()
