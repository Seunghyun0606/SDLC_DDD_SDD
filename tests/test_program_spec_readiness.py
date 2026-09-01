import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sdlc/scripts/validate_program_spec.py"
spec = importlib.util.spec_from_file_location("validate_program_spec", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ProgramSpecReadinessTest(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT/"sdlc/config/program-spec-readiness.json").read_text(encoding="utf-8"))

    def complete_text(self):
        markers = [x["marker"] for x in self.config["required_fields"]]
        return "\n".join(markers) + "\nImplementation Readiness: PARTIAL\nOPEN_REAL_SOURCE\n"

    def test_required_field_count_is_17(self):
        self.assertEqual(17, len(self.config["required_fields"]))

    def test_complete_partial_spec_passes(self):
        self.assertEqual([], module.validate_text(self.complete_text(), self.config))

    def test_missing_section_fails(self):
        text = self.complete_text().replace("### Input DTO Contract", "")
        self.assertTrue(any(x.startswith("MISSING_SECTION:input_dto") for x in module.validate_text(text, self.config)))

    def test_simulated_source_cannot_be_ready(self):
        text = self.complete_text().replace("Implementation Readiness: PARTIAL", "Implementation Readiness: READY")
        text = text.replace("OPEN_REAL_SOURCE", "SIMULATED_REFERENCE_ARCHITECTURE\nOPEN Count: 0")
        self.assertIn("READY_WITH_SIMULATED_SOURCE", module.validate_text(text, self.config))

    def test_open_real_source_cannot_be_ready(self):
        text = self.complete_text().replace("Implementation Readiness: PARTIAL", "Implementation Readiness: READY") + "\nOPEN Count: 0"
        self.assertIn("READY_WITH_OPEN_REAL_SOURCE", module.validate_text(text, self.config))

    def test_ready_requires_zero_open(self):
        text = self.complete_text().replace("Implementation Readiness: PARTIAL", "Implementation Readiness: READY").replace("OPEN_REAL_SOURCE", "")
        self.assertIn("READY_WITH_NONZERO_OR_UNKNOWN_OPEN", module.validate_text(text, self.config))

if __name__ == "__main__":
    unittest.main()
