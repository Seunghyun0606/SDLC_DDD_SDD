import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sdlc/scripts/run_greenfield_e2e_pilot.py"
SEED = ROOT / "sdlc/validation/pilot/greenfield/REQ_TM_FL001-seed.json"

spec = importlib.util.spec_from_file_location("greenfield_e2e_pilot", SCRIPT)
MOD = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(MOD)


class GreenfieldE2EPilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.seed = json.loads(SEED.read_text(encoding="utf-8"))
        cls.result = MOD.run(cls.seed)
        cls.stages = {row["stage"]: row for row in cls.result["stages"]}

    def test_real_requirement_id_and_text_are_preserved(self):
        self.assertEqual("REQ_TM_FL001", self.result["input"]["external_id"])
        self.assertEqual("탄력근로제 근무계획 저장", self.result["input"]["requirement_text"])
        self.assertEqual("요구사항목록.xlsx", self.result["input"]["source_document"])

    def test_greenfield_can_start_without_repository(self):
        self.assertIsNone(self.result["input"]["existing_source_repository"])
        self.assertFalse(self.result["metrics"]["source_repository_required_to_start"])
        self.assertEqual("NOT_APPLICABLE_NO_EXISTING_SOURCE", self.stages["DISCOVERY"]["status"])
        self.assertFalse(self.stages["DISCOVERY"]["brownfield_adapter_invoked"])

    def test_missing_business_context_becomes_open_not_invented(self):
        six_w = self.stages["PROCESS"]["six_w"]
        for key in ["Who", "When", "Where", "Why"]:
            self.assertEqual("OPEN", six_w[key])
        self.assertEqual(0, self.result["metrics"]["business_fact_invention_count"])
        self.assertGreaterEqual(self.result["metrics"]["open_item_count"], 5)

    def test_human_open_view_uses_simple_status_only(self):
        statuses = {row["human_status"] for row in self.result["open_items"]}
        self.assertEqual({"미확정"}, statuses)
        serialized = json.dumps(self.result["open_items"], ensure_ascii=False)
        for machine_term in ["decision_domain", "basis_class", "downstream_impact", "resolution_method"]:
            self.assertNotIn(machine_term, serialized)

    def test_program_and_development_do_not_fake_readiness(self):
        self.assertEqual("OPEN_REAL_SOURCE", self.stages["PROGRAM"]["source_state"])
        self.assertEqual("NOT_READY", self.stages["PROGRAM"]["readiness"])
        self.assertFalse(self.stages["DEVELOPMENT"]["source_write_performed"])
        self.assertEqual(0, self.result["metrics"]["source_write_count"])

    def test_verify_and_knowledge_do_not_claim_success(self):
        self.assertFalse(self.stages["VERIFY"]["success_claimed"])
        self.assertEqual("NOT_PROMOTED", self.stages["KNOWLEDGE"]["status"])

    def test_active_user_artifacts_are_compact(self):
        self.assertEqual(6, self.result["metrics"]["active_user_artifact_count"])
        self.assertFalse(self.result["metrics"]["machine_result_envelope_is_user_artifact"])
        self.assertEqual(0, self.result["metrics"]["required_machine_taxonomy_input_count"])

    def test_all_workflow_stages_are_accounted_for(self):
        self.assertEqual(MOD.WORKFLOW, self.result["workflow"])
        self.assertEqual(len(MOD.WORKFLOW), self.result["metrics"]["workflow_stage_count"])

    def test_verdict_does_not_claim_human_usability(self):
        self.assertEqual("PASS_AGENT_E2E_REPLAY_HUMAN_USABILITY_NOT_MEASURED", self.result["verdict"])
        self.assertTrue(any("사용시간" in item for item in self.result["limitations"]))

    def test_cli_writes_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "greenfield.json"
            rc = MOD.main(["--seed", str(SEED), "--output", str(output)])
            self.assertEqual(0, rc)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("REQ_TM_FL001", payload["input"]["external_id"])


if __name__ == "__main__":
    unittest.main()
