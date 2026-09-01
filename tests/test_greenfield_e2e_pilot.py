import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sdlc/scripts/run_greenfield_e2e_pilot.py"
FIXTURE_PROVIDER = ROOT / "sdlc/validation/providers/deterministic_stage_provider.py"

spec = importlib.util.spec_from_file_location("greenfield_e2e_pilot", SCRIPT)
MOD = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(MOD)


def copy_harness(root: Path):
    target = root / "sdlc/design/contracts/harness-package-contract.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text((ROOT / "sdlc/design/contracts/harness-package-contract.json").read_text(encoding="utf-8"), encoding="utf-8")


def provider(enabled=True):
    return {
        "schema_version": 1,
        "provider_id": "GREENFIELD_TEST_FIXTURE",
        "provider_class": "VALIDATION_FIXTURE",
        "enabled": enabled,
        "timeout_seconds": 30,
        "result_filename": "stage-result.json",
        "command": [
            sys.executable,
            str(FIXTURE_PROVIDER),
            "--context",
            "{context_path}",
            "--result",
            "{result_path}",
        ],
    }


class GreenfieldProviderDrivenE2ETest(unittest.TestCase):
    def test_runner_source_has_no_time_domain_stage_answers(self):
        text = SCRIPT.read_text(encoding="utf-8")
        for hardcoded in ["근무계획", "탄력근로", "누가 이 기능을 사용하거나 실행하는가?", "PASS_AGENT_E2E_REPLAY"]:
            self.assertNotIn(hardcoded, text)
        self.assertIn("run_work.py", text)
        self.assertIn("PASS_EXECUTOR_E2E_FIXTURE_PROVIDER", text)

    def test_non_time_domain_requirement_runs_real_work_executor_with_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_harness(root)
            seed = {
                "schema_version": 1,
                "pilot_id": "CLAIM-001",
                "mode": "GREENFIELD",
                "external_id": "CLM-001",
                "requirement_text": "보험금 청구 심사 기능이 필요하다.",
            }
            result = MOD.run(
                root,
                seed,
                provider(),
                runtime_root=root / "runtime/greenfield",
                stages=["DECOMPOSE", "PROCESS", "DESIGN", "PROGRAM"],
            )
            self.assertEqual("PASS_EXECUTOR_E2E_FIXTURE_PROVIDER", result["verdict"])
            self.assertFalse(result["actual_agent_provider_executed"])
            self.assertEqual(4, len(result["stage_results"]))
            self.assertEqual(4, len(result["materialized_artifacts"]))
            self.assertTrue(all(row["execution"]["validation"]["status"] == "PASS" for row in result["stage_results"]))

    def test_disabled_provider_is_not_reported_as_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_harness(root)
            seed = {
                "schema_version": 1,
                "pilot_id": "BANK-001",
                "mode": "GREENFIELD",
                "external_id": "LOAN-001",
                "requirement_text": "은행 대출 승인 기능이 필요하다.",
            }
            result = MOD.run(root, seed, provider(False), runtime_root=root / "runtime/greenfield")
            self.assertEqual("NOT_EXECUTED_PROVIDER_UNAVAILABLE_OR_DISABLED", result["verdict"])
            self.assertFalse(result["actual_agent_provider_executed"])
            self.assertEqual([], result["stage_results"])

    def test_only_external_agent_class_can_claim_agent_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_harness(root)
            seed = {
                "schema_version": 1,
                "pilot_id": "SAAS-001",
                "mode": "GREENFIELD",
                "external_id": "AUTH-001",
                "requirement_text": "SaaS 사용자 권한 변경 기능이 필요하다.",
            }
            fixture = provider()
            result = MOD.run(root, seed, fixture, runtime_root=root / "runtime/greenfield", stages=["DESIGN"])
            self.assertEqual("VALIDATION_FIXTURE", result["provider_class"])
            self.assertFalse(result["actual_agent_provider_executed"])
            self.assertNotEqual("PASS_AGENT_E2E_PROVIDER_EXECUTION", result["verdict"])


if __name__ == "__main__":
    unittest.main()
