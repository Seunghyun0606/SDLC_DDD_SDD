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
        self.config = json.loads((ROOT / "sdlc/config/program-spec-readiness.json").read_text(encoding="utf-8"))

    def complete_text(self):
        markers = [x["marker"] for x in self.config["required_fields"]]
        return "\n".join(markers) + "\n기능 설계 문서/버전: FD-1\n구현 준비 판정: PARTIAL\nOPEN_REAL_SOURCE\n남은 구현 OPEN 수: 1\n"

    def core_text(self):
        markers = {row["id"]: row["marker"] for row in self.config["required_fields"]}
        return "\n".join(markers[x] for x in self.config["core_required_field_ids"])

    def test_readiness_is_core_plus_conditional_with_legacy_catalog(self):
        self.assertEqual(17, len(self.config["required_fields"]))
        self.assertEqual("CORE_PLUS_RISK_TRIGGERED_CONDITIONAL", self.config["representation"])
        self.assertEqual(6, len(self.config["core_required_field_ids"]))
        self.assertEqual(17, len(self.config["legacy_compatibility"]["required_field_ids"]))

    def test_complete_partial_spec_passes(self):
        self.assertEqual([], module.validate_text(self.complete_text(), self.config))

    def test_missing_core_readiness_item_fails(self):
        text = self.core_text().replace("| 실제 구현 대상 |", "")
        errors = module.validate_text(text, self.config, "STANDARD", "L1", {})
        self.assertTrue(any(x.startswith("MISSING_READINESS_ITEM:implementation_target") for x in errors))

    def test_conditional_item_is_required_only_when_triggered(self):
        text = self.core_text()
        self.assertEqual([], module.validate_text(text, self.config, "STANDARD", "L2", {}))
        errors = module.validate_text(text, self.config, "STANDARD", "L2", {"DATA_MAPPING_IMPACT": "YES"})
        self.assertTrue(any(x.startswith("MISSING_READINESS_ITEM:io_mapping") for x in errors))

    def test_simulated_source_cannot_be_ready(self):
        text = self.complete_text().replace("구현 준비 판정: PARTIAL", "구현 준비 판정: READY").replace("OPEN_REAL_SOURCE", "SIMULATED_REFERENCE_ARCHITECTURE").replace("남은 구현 OPEN 수: 1", "남은 구현 OPEN 수: 0")
        self.assertIn("READY_WITH_SIMULATED_SOURCE", module.validate_text(text, self.config))

    def test_open_real_source_cannot_be_ready(self):
        text = self.complete_text().replace("구현 준비 판정: PARTIAL", "구현 준비 판정: READY").replace("남은 구현 OPEN 수: 1", "남은 구현 OPEN 수: 0")
        self.assertIn("READY_WITH_OPEN_REAL_SOURCE", module.validate_text(text, self.config))

    def test_ready_requires_zero_open(self):
        text = self.complete_text().replace("구현 준비 판정: PARTIAL", "구현 준비 판정: READY").replace("OPEN_REAL_SOURCE", "")
        self.assertIn("READY_WITH_NONZERO_OR_UNKNOWN_OPEN", module.validate_text(text, self.config))

    def test_l3_ready_requires_functional_design_reference(self):
        text = self.complete_text().replace("구현 준비 판정: PARTIAL", "구현 준비 판정: READY").replace("OPEN_REAL_SOURCE", "").replace("남은 구현 OPEN 수: 1", "남은 구현 OPEN 수: 0").replace("기능 설계 문서/버전: FD-1", "")
        self.assertIn("READY_WITHOUT_FUNCTIONAL_DESIGN_REFERENCE", module.validate_text(text, self.config, change_level="L3"))

    def test_l1_does_not_force_full_functional_design_document_reference(self):
        text = self.core_text() + "\n구현 준비 판정: READY\n남은 구현 OPEN 수: 0\n"
        self.assertNotIn("READY_WITHOUT_FUNCTIONAL_DESIGN_REFERENCE", module.validate_text(text, self.config, change_level="L1"))

    def test_legacy_english_readiness_is_backward_compatible(self):
        text = self.complete_text().replace("구현 준비 판정: PARTIAL", "Implementation Readiness: READY").replace("OPEN_REAL_SOURCE", "").replace("남은 구현 OPEN 수: 1", "OPEN Count: 0").replace("기능 설계 문서/버전: FD-1", "Functional Design Ref: FD-1")
        self.assertEqual([], module.validate_text(text, self.config))


if __name__ == "__main__":
    unittest.main()
