import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
CONTRACT = ROOT / "sdlc/validation/pilot/RQ-CAND-0001-workflow-pilot.json"


class WorkflowPilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def test_actual_xlsx_external_ids_are_preserved_in_intake(self):
        text = (ROOT / "docs/99_파일럿/RQ-CAND-0001/01_INTAKE_요구사항.md").read_text(encoding="utf-8")
        for rid in self.data["input"]["external_ids"]:
            self.assertIn(rid, text)

    def test_each_workflow_has_user_visible_artifact(self):
        root = ROOT / "docs/99_파일럿/RQ-CAND-0001"
        expected = ["01_INTAKE", "02_DECOMPOSE", "03_CLARIFY", "04_PROCESS", "05_DISCOVERY", "06_IMPACT", "07_DESIGN", "08_PROGRAM", "09_DEVELOPMENT", "10_TEST", "11_VERIFY", "12_KNOWLEDGE"]
        names = [p.name for p in root.glob("*.md")]
        for prefix in expected:
            self.assertTrue(any(n.startswith(prefix) for n in names), prefix)

    def test_fixture_hashes_match(self):
        fixture_root = ROOT / "sdlc/validation/pilot/source-fixture"
        for rel, expected in self.data["fixture_hashes"].items():
            actual = "sha256:" + hashlib.sha256((fixture_root / Path(rel).relative_to("fixture")).read_bytes()).hexdigest()
            self.assertEqual(expected, actual, rel)

    def test_development_changes_service_but_not_mapper(self):
        fixture = ROOT / "sdlc/validation/pilot/source-fixture"
        asis = (fixture / "as-is/src/main/java/com/acme/tm/FlexibleWorkPlanService.java").read_text()
        tobe = (fixture / "to-be/src/main/java/com/acme/tm/FlexibleWorkPlanService.java").read_text()
        self.assertNotIn("initializeFirstPlan", asis)
        self.assertIn("initializeFirstPlan", tobe)
        self.assertEqual(
            (fixture / "as-is/src/main/resources/mapper/FlexibleWorkPlanMapper.xml").read_text(),
            (fixture / "to-be/src/main/resources/mapper/FlexibleWorkPlanMapper.xml").read_text(),
        )

    def test_source_stages_are_explicitly_simulated(self):
        root = ROOT / "docs/99_파일럿/RQ-CAND-0001"
        for prefix in ["05_DISCOVERY", "06_IMPACT", "07_DESIGN", "08_PROGRAM", "09_DEVELOPMENT", "10_TEST", "11_VERIFY"]:
            path = next(root.glob(prefix + "*.md"))
            self.assertIn("SIMULATED", path.read_text(encoding="utf-8"), path.name)

    def test_verify_does_not_claim_real_application_success(self):
        text = (ROOT / "docs/99_파일럿/RQ-CAND-0001/11_VERIFY_검증결과.md").read_text(encoding="utf-8")
        self.assertIn("PILOT_STRUCTURAL_PASS / REAL_SOURCE_PENDING", text)
        self.assertIn("Actual build/test: NOT_RUN", text)

    def test_pilot_overlay_materializes_in_order(self):
        script = ROOT / "sdlc/scripts/resolve_overlay.py"
        spec = importlib.util.spec_from_file_location("resolve_overlay", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            manifest = mod.materialize(ROOT, ROOT / "sdlc/validation/pilot/overlay-resolution.json", Path(tmp) / "effective")
            self.assertEqual(["core", "project_overlay", "domain_overlay"], manifest["resolution_order"])
            text = (Path(tmp) / "effective/templates/program-spec.md").read_text(encoding="utf-8")
            self.assertIn("Pilot Project Context", text)
            self.assertIn("Pilot Time Domain Context", text)


if __name__ == "__main__":
    unittest.main()
