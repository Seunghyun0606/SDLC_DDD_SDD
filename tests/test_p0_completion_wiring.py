import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = json.loads((ROOT / "sdlc/design/contracts/harness-package-contract.json").read_text(encoding="utf-8"))
SOURCE_DRIFT = json.loads((ROOT / "sdlc/design/contracts/source-drift-contract.json").read_text(encoding="utf-8"))


class P0CompletionWiringTest(unittest.TestCase):
    def test_semantic_reverse_candidate_is_core_executable_but_non_destructive(self):
        script = "sdlc/scripts/generate_program_spec_reverse_candidate.py"
        self.assertIn(script, HARNESS["core_required_files"])
        reverse = HARNESS["source_drift_reverse"]
        self.assertEqual(script, reverse["program_spec_reverse_candidate_script"])
        self.assertTrue(reverse["program_spec_candidate_requires_review"])
        self.assertFalse(reverse["auto_rewrite_artifact"])
        self.assertFalse(reverse["auto_update_business_truth"])
        contract = SOURCE_DRIFT["program_spec_reverse_candidate"]
        self.assertFalse(contract["auto_apply"])
        self.assertFalse(contract["functional_design_auto_update"])
        self.assertFalse(contract["business_truth_auto_update"])

    def test_change_skill_wires_semantic_reverse_without_full_reverse_claim(self):
        text = (ROOT / ".cursor/skills/change/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("generate_program_spec_reverse_candidate.py", text)
        self.assertIn("전역 Coverage 변화만으로 관계 없는 Program Spec Candidate를 만들지 않는다", text)
        self.assertIn("auto_apply: false", text)
        self.assertIn("Functional Design 재작성기가 아니다", text)

    def test_repeatability_requires_actual_external_provider_for_empirical_pass(self):
        agent = HARNESS["agent_execution"]
        self.assertTrue(agent["actual_provider_execution_required_for_empirical_pass"])
        self.assertTrue(agent["repeatability_runner_is_validation_utility_not_core_stage_runtime"])
        self.assertNotIn(agent["repeatability_experiment_runner"], HARNESS["core_required_files"])
        profile = json.loads((ROOT / agent["repeatability_profile"]).read_text(encoding="utf-8"))
        self.assertFalse(profile["enabled"])
        self.assertEqual("EXTERNAL_AGENT_PROVIDER_REQUIRED", profile["provider_id"])

    def test_public_brownfield_pilot_is_real_integration_validation_not_core_dependency(self):
        brownfield = HARNESS["brownfield_impact"]
        validator = brownfield["public_repository_pilot_validator"]
        self.assertTrue(brownfield["public_repository_pilot_is_validation_only"])
        self.assertNotIn(validator, HARNESS["core_required_files"])
        workflow = (ROOT / ".github/workflows/public-brownfield-pilot.yml").read_text(encoding="utf-8")
        self.assertIn("repository: macrozheng/mall", workflow)
        self.assertIn("0504e86b1f1b6f1b8aa6a734d37a90fb67346be7", workflow)
        self.assertIn("validate_public_brownfield_pilot.py", workflow)

    def test_greenfield_pilot_uses_real_requirement_and_materializes_six_user_docs(self):
        validation = HARNESS["validation_pilots"]
        self.assertEqual(6, validation["greenfield_materializes_user_artifact_count"])
        self.assertTrue(validation["greenfield_human_usability_not_measured"])
        seed = json.loads((ROOT / validation["greenfield_real_requirement_seed"]).read_text(encoding="utf-8"))
        self.assertEqual("REQ_TM_FL001", seed["external_id"])
        self.assertEqual("탄력근로제 근무계획 저장", seed["requirement_text"])
        workflow = (ROOT / validation["greenfield_workflow"]).read_text(encoding="utf-8")
        self.assertIn("--artifact-root", workflow)
        self.assertIn("-eq 6", workflow)


if __name__ == "__main__":
    unittest.main()
