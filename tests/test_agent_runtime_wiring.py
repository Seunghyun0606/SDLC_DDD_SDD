import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class AgentRuntimeWiringTest(unittest.TestCase):
    def test_harness_registers_stage_result_validator(self):
        harness = json.loads((ROOT / "sdlc/design/contracts/harness-package-contract.json").read_text(encoding="utf-8"))
        agent = harness["agent_execution"]
        self.assertEqual("sdlc/scripts/validate_agent_stage_result.py", agent["stage_result_validator"])
        self.assertTrue(agent["machine_verifiable_output"])
        self.assertTrue(agent["semantic_repeatability_check"])
        self.assertTrue(agent["validator_does_not_claim_llm_determinism"])
        self.assertIn(agent["stage_result_validator"], harness["core_required_files"])
        self.assertTrue((ROOT / agent["stage_result_validator"]).is_file())

    def test_agent_contract_has_small_machine_result_envelope(self):
        contract = json.loads((ROOT / "sdlc/design/contracts/agent-execution-contract.json").read_text(encoding="utf-8"))
        envelope = contract["runtime_output_envelope"]
        self.assertEqual(
            ["stage", "artifact_path", "canonical_delta", "quality_gate", "alerts", "uncertainty"],
            envelope["required_fields"],
        )
        self.assertEqual(["PASS", "WARNING", "FAIL"], envelope["quality_gate_status"])
        self.assertTrue(envelope["canonical_delta_required"])
        self.assertFalse(envelope["unresolved_template_placeholder_allowed"])
        self.assertTrue(envelope["delta_stage_must_match_result_stage"])
        self.assertTrue(envelope["delta_source_artifact_must_match_artifact_path"])
        self.assertTrue(contract["repeatability"]["validator_does_not_claim_llm_determinism"])

    def test_work_enforces_stage_result_before_canonical_apply(self):
        text = (ROOT / ".cursor/skills/work/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## Agent Stage Result 실행 경계", text)
        self.assertIn("validate_agent_stage_result.py", text)
        self.assertIn("validation.executable = true", text)
        self.assertIn("--compare", text)
        self.assertIn("semantic fingerprint", text)
        self.assertIn("Agent/LLM 자체가 결정론적임을 증명하는 기능이 아니다", text)
        self.assertLess(text.index("validate_agent_stage_result.py"), text.index("## Canonical 실행 경로"))

    def test_change_uses_same_stage_result_boundary(self):
        text = (ROOT / ".cursor/skills/change/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## 변경 Stage Result 검증", text)
        self.assertIn("validate_agent_stage_result.py", text)
        self.assertIn("validation.executable = true", text)
        self.assertIn("--compare", text)
        self.assertIn("LLM 자체의 결정론을 보장하지 않으며", text)
        self.assertLess(text.index("## 변경 Stage Result 검증"), text.index("## Canonical 변경 적용"))


if __name__ == "__main__":
    unittest.main()
