import importlib.util
import json
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sdlc/scripts/run_agent_repeatability_experiment.py"

spec = importlib.util.spec_from_file_location("repeatability_experiment", SCRIPT)
MOD = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(MOD)


class AgentRepeatabilityExperimentTest(unittest.TestCase):
    def write_provider(self, root: Path, *, semantic_variation: bool = False, exit_code: int = 0) -> Path:
        path = root / "provider.py"
        body_expr = "f'내용 run={run_index}'" if semantic_variation else "'동일한 의미 내용'"
        path.write_text(textwrap.dedent(f'''\
            import json
            import sys
            from pathlib import Path

            result_path = Path(sys.argv[1])
            run_index = int(sys.argv[2])
            if {exit_code}:
                raise SystemExit({exit_code})
            artifact = result_path.parent / "artifact.md"
            artifact.write_text("generated_at: 2026-09-02T00:00:0" + str(run_index) + "+09:00\\n" + {body_expr} + "\\n", encoding="utf-8")
            result = {{
                "schema_version": 1,
                "stage": "DECOMPOSE",
                "artifact_path": "artifact.md",
                "generated_at": "2026-09-02T00:00:0" + str(run_index) + "+09:00",
                "canonical_delta": {{
                    "schema_version": 1,
                    "delta_id": "REPEATABILITY-SAME-DELTA",
                    "base_revision": 0,
                    "stage": "DECOMPOSE",
                    "source_artifact": "artifact.md",
                    "operations": []
                }},
                "quality_gate": {{"status": "PASS", "failures": []}},
                "alerts": [],
                "uncertainty": []
            }}
            result_path.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
        '''), encoding="utf-8")
        return path

    def config(self, provider: Path, *, enabled=True, run_count=3):
        return {
            "schema_version": 1,
            "provider_id": "TEST_PROVIDER",
            "enabled": enabled,
            "run_count": run_count,
            "timeout_seconds": 30,
            "result_filename": "stage-result.json",
            "command": [sys.executable, str(provider), "{result_path}", "{run_index}"],
        }

    def test_disabled_provider_is_not_fake_pass(self):
        config = {
            "schema_version": 1,
            "provider_id": "NO_PROVIDER",
            "enabled": False,
            "run_count": 3,
            "result_filename": "stage-result.json",
            "command": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            result = MOD.run_experiment(config, Path(tmp) / "runs")
        self.assertEqual("NOT_EXECUTED_PROVIDER_UNAVAILABLE_OR_DISABLED", result["verdict"])
        self.assertFalse(result["actual_provider_executed"])
        self.assertEqual(0, result["run_count_executed"])
        self.assertIsNone(result["semantic_match_rate"])

    def test_same_semantics_with_volatile_timestamps_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            provider = self.write_provider(root)
            result = MOD.run_experiment(self.config(provider), root / "runs")
        self.assertEqual("PASS_REPEATED_PROVIDER_OUTPUT_SEMANTIC_MATCH", result["verdict"])
        self.assertEqual(3, result["run_count_executed"])
        self.assertEqual(1.0, result["semantic_match_rate"])
        self.assertTrue(result["actual_provider_executed"])
        self.assertFalse(result["llm_determinism_proven"])

    def test_semantic_variation_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            provider = self.write_provider(root, semantic_variation=True)
            result = MOD.run_experiment(self.config(provider), root / "runs")
        self.assertEqual("FAIL_SEMANTIC_REPEATABILITY_MISMATCH", result["verdict"])
        self.assertLess(result["semantic_match_rate"], 1.0)

    def test_provider_command_failure_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            provider = self.write_provider(root, exit_code=7)
            result = MOD.run_experiment(self.config(provider, run_count=2), root / "runs")
        self.assertEqual("FAIL_PROVIDER_COMMAND", result["verdict"])
        self.assertTrue(result["actual_provider_executed"])

    def test_invalid_run_count_fails_closed(self):
        with self.assertRaises(ValueError):
            MOD.run_experiment({
                "schema_version": 1,
                "provider_id": "X",
                "enabled": False,
                "run_count": 1,
                "command": [],
            }, Path("unused"))

    def test_example_profile_requires_real_provider(self):
        profile = json.loads((ROOT / "sdlc/config/agent-repeatability-profile.example.json").read_text(encoding="utf-8"))
        self.assertFalse(profile["enabled"])
        self.assertEqual("EXTERNAL_AGENT_PROVIDER_REQUIRED", profile["provider_id"])
        self.assertTrue(profile["rules"]["actual_provider_execution_required_for_pass"])
        self.assertFalse(profile["rules"]["llm_determinism_claimed"])


if __name__ == "__main__":
    unittest.main()
