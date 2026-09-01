import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS = json.loads((ROOT / "sdlc/design/contracts/harness-package-contract.json").read_text(encoding="utf-8"))
SOURCE_DRIFT = json.loads((ROOT / "sdlc/design/contracts/source-drift-contract.json").read_text(encoding="utf-8"))


def deployment_files(name: str) -> set[str]:
    value = HARNESS.get("deployment_sets", {}).get(name, [])
    return set(value if isinstance(value, list) else [])


class P0CompletionWiringTest(unittest.TestCase):
    def test_semantic_reverse_candidate_is_brownfield_extension_and_non_destructive(self):
        script = "sdlc/scripts/generate_program_spec_reverse_candidate.py"
        self.assertNotIn(script, HARNESS["core_required_files"])
        self.assertIn(script, deployment_files("BROWNFIELD_EXTENSION"))
        reverse = HARNESS["source_drift_reverse"]
        self.assertEqual(script, reverse["program_spec_reverse_candidate_script"])
        self.assertTrue(reverse["program_spec_candidate_requires_review"])
        self.assertFalse(reverse["auto_rewrite_artifact"])
        self.assertFalse(reverse["auto_update_business_truth"])
        contract = SOURCE_DRIFT["program_spec_reverse_candidate"]
        self.assertFalse(contract["auto_apply"])
        self.assertFalse(contract["functional_design_auto_update"])
        self.assertFalse(contract["business_truth_auto_update"])
        self.assertTrue((ROOT / script).is_file())

    def test_work_executor_is_core_and_supports_explicit_target_stage_document_reentry(self):
        work = HARNESS["work_execution"]
        self.assertEqual("sdlc/scripts/run_work.py", work["executor"])
        self.assertIn(work["executor"], HARNESS["core_required_files"])
        self.assertTrue(work["target_types_are_open_ended"])
        self.assertTrue(work["explicit_stage_reentry"])
        self.assertTrue(work["explicit_artifact_override"])
        self.assertTrue(work["target_and_stage_are_independent"])
        self.assertTrue(work["target_graph_existing_entity_scope_guard"])
        text = (ROOT / ".cursor/skills/work/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("--target PGM-001 --stage PROGRAM", text)
        self.assertIn("--target ANA001", text)
        self.assertIn("--artifact", text)

    def test_canonical_runtime_hashes_delta_identity_and_blocks_nonconfirmed_truth_overwrite(self):
        runtime = HARNESS["canonical_runtime"]
        self.assertTrue(runtime["idempotency_requires_same_semantic_payload_hash"])
        self.assertTrue(runtime["delta_id_content_conflict_fails_closed"])
        self.assertTrue(runtime["confirmed_business_mutation_requires_confirmed_evidence"])
        self.assertFalse(runtime["non_confirmed_evidence_can_overwrite_confirmed_business"])
        self.assertTrue(runtime["no_change_supported"])
        self.assertFalse(runtime["no_change_advances_revision"])

    def test_repeatability_requires_actual_external_provider_for_empirical_pass(self):
        agent = HARNESS["agent_execution"]
        self.assertTrue(agent["actual_provider_execution_required_for_empirical_pass"])
        self.assertTrue(agent["validation_fixture_provider_cannot_claim_agent_pass"])
        self.assertEqual("sdlc/scripts/run_work_repeatability_experiment.py", agent["work_repeatability_experiment_runner"])
        profile = json.loads((ROOT / agent["repeatability_profile"]).read_text(encoding="utf-8"))
        self.assertFalse(profile["enabled"])
        self.assertEqual("EXTERNAL_AGENT_PROVIDER_REQUIRED", profile["provider_id"])
        self.assertEqual("EXTERNAL_AGENT", profile["provider_class"])

    def test_source_reverse_inputs_are_brownfield_extension_and_built_automatically(self):
        reverse = HARNESS["source_drift_reverse"]
        self.assertEqual("sdlc/scripts/build_reverse_inputs.py", reverse["input_builder"])
        self.assertEqual("sdlc/scripts/run_source_reverse_check.py", reverse["orchestrator"])
        self.assertFalse(reverse["manual_observed_manifest_authoring_required"])
        self.assertFalse(reverse["manual_artifact_index_authoring_required"])
        self.assertTrue(reverse["auto_generated_upstream_edges_are_check_required_only"])
        brownfield = deployment_files("BROWNFIELD_EXTENSION")
        for path in [reverse["input_builder"], reverse["orchestrator"]]:
            self.assertNotIn(path, HARNESS["core_required_files"])
            self.assertIn(path, brownfield)
            self.assertTrue((ROOT / path).is_file())

    def test_public_brownfield_pilot_is_real_integration_validation_not_core_dependency(self):
        brownfield = HARNESS["brownfield_impact"]
        validator = brownfield["public_repository_pilot_validator"]
        self.assertTrue(brownfield["public_repository_pilot_is_validation_only"])
        self.assertNotIn(validator, HARNESS["core_required_files"])
        workflow = (ROOT / ".github/workflows/public-brownfield-pilot.yml").read_text(encoding="utf-8")
        self.assertIn("repository: macrozheng/mall", workflow)
        self.assertIn("validate_public_brownfield_pilot.py", workflow)

    def test_greenfield_pilot_is_provider_driven_and_fixture_is_not_agent_pass(self):
        validation = HARNESS["validation_pilots"]
        self.assertTrue(validation["greenfield_provider_driven"])
        self.assertTrue(validation["greenfield_fixture_provider_is_not_agent_validation"])
        self.assertTrue(validation["greenfield_actual_agent_provider_required_for_agent_pass"])
        self.assertEqual(5, validation["greenfield_default_stage_count"])
        seed = json.loads((ROOT / validation["greenfield_real_requirement_seed"]).read_text(encoding="utf-8"))
        self.assertEqual("REQ_TM_FL001", seed["external_id"])
        workflow = (ROOT / validation["greenfield_workflow"]).read_text(encoding="utf-8")
        self.assertIn("--provider-config", workflow)
        self.assertIn("fixture-provider.json", workflow)
        self.assertIn("PASS_EXECUTOR_E2E_FIXTURE_PROVIDER", workflow)
        self.assertIn("actual_agent_provider_executed", workflow)


if __name__ == "__main__":
    unittest.main()
