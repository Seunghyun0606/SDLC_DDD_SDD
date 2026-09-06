import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sdlc/scripts/empirical_pilot_runtime.py"
SPEC = importlib.util.spec_from_file_location("empirical_pilot_runtime", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)
PILOT_ROOT = ROOT / "sdlc/validation/pilots"


class EmpiricalPilotRuntimeTest(unittest.TestCase):
    def _copy_templates(self, root: Path) -> None:
        target = root / "sdlc/validation/pilots"
        target.mkdir(parents=True, exist_ok=True)
        for spec in MOD.PILOT_SPECS.values():
            name = Path(spec["template"]).name
            shutil.copy2(PILOT_ROOT / name, target / name)

    def test_status_without_runtime_evidence_is_three_explicit_not_run(self):
        with tempfile.TemporaryDirectory() as td:
            result = MOD.status(root=Path(td))
        self.assertEqual("EMPIRICAL_PILOT_STATUS", result["status"])
        self.assertEqual(3, result["pilot_count"])
        self.assertEqual(0, result["empirical_pass_count"])
        self.assertFalse(result["all_empirical_pass"])
        self.assertEqual({"NOT_RUN": 3}, result["verdict_counts"])
        self.assertTrue(all(row["source"] == "EVIDENCE_FILE_MISSING" for row in result["pilots"]))

    def test_init_copies_not_run_template_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._copy_templates(root)
            result = MOD.init_pilot(root=root, pilot="human-first-use")
            evidence = root / result["evidence_file"]
            self.assertTrue(evidence.is_file())
            data = json.loads(evidence.read_text(encoding="utf-8"))
            self.assertEqual("HUMAN_FIRST_USE", data["pilot_type"])
            self.assertEqual("NOT_RUN", data["execution_status"])
            self.assertFalse(result["empirical_pass"])
            with self.assertRaises(FileExistsError):
                MOD.init_pilot(root=root, pilot="human-first-use")

    def test_init_rejects_output_path_outside_project_root(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._copy_templates(root)
            with self.assertRaises(ValueError):
                MOD.init_pilot(root=root, pilot="brownfield-reconciliation", output="../escape.json")

    def test_runtime_validate_uses_fail_closed_empirical_contract(self):
        data = json.loads((PILOT_ROOT / "external-agent-tailoring-pilot.example.json").read_text(encoding="utf-8"))
        data["claims"]["external_agent_empirical_pass"] = True
        with tempfile.TemporaryDirectory() as td:
            evidence = Path(td) / "evidence.json"
            evidence.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            result = MOD.validate_file(evidence)
        self.assertEqual("FAIL_OVERCLAIMED_PASS", result["verdict"])
        self.assertFalse(result["empirical_pass"])
        self.assertIn("UNOBSERVED_PILOT_CANNOT_CLAIM_PASS", result["errors"])

    def test_cli_status_can_materialize_machine_summary(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cp = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "status",
                    "--root",
                    str(root),
                    "--output",
                    "sdlc/runtime/pilots/status.json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, cp.returncode, cp.stderr + "\n" + cp.stdout)
            payload = json.loads(cp.stdout)
            self.assertEqual("EMPIRICAL_PILOT_STATUS", payload["status"])
            output = root / "sdlc/runtime/pilots/status.json"
            self.assertTrue(output.is_file())
            written = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual({"NOT_RUN": 3}, written["verdict_counts"])


if __name__ == "__main__":
    unittest.main()
