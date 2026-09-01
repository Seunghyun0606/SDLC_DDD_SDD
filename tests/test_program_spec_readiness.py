import importlib.util
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"sdlc/scripts/validate_program_spec.py"
spec=importlib.util.spec_from_file_location("validate_program_spec",SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class ProgramSpecReadinessTest(unittest.TestCase):
    def setUp(self):
        self.config=json.loads((ROOT/"sdlc/config/program-spec-readiness.json").read_text(encoding="utf-8"))

    def complete_text(self):
        markers=[x["marker"] for x in self.config["required_fields"]]
        return "\n".join(markers)+"\n구현 준비 상태: PARTIAL\nOPEN_REAL_SOURCE\n"

    def test_required_field_count_is_17(self):
        self.assertEqual(17,len(self.config["required_fields"]))

    def test_complete_partial_spec_passes(self):
        self.assertEqual([],module.validate_text(self.complete_text(),self.config))

    def test_missing_section_fails(self):
        text=self.complete_text().replace("### 입력 데이터 계약(DTO)","")
        self.assertTrue(any(x.startswith("MISSING_SECTION:input_dto") for x in module.validate_text(text,self.config)))

    def test_simulated_source_cannot_be_ready(self):
        text=self.complete_text().replace("구현 준비 상태: PARTIAL","구현 준비 상태: READY").replace("OPEN_REAL_SOURCE","SIMULATED_REFERENCE_ARCHITECTURE\n미확정 항목 수: 0")
        self.assertIn("READY_WITH_SIMULATED_SOURCE",module.validate_text(text,self.config))

    def test_open_real_source_cannot_be_ready(self):
        text=self.complete_text().replace("구현 준비 상태: PARTIAL","구현 준비 상태: READY")+"\n미확정 항목 수: 0"
        self.assertIn("READY_WITH_OPEN_REAL_SOURCE",module.validate_text(text,self.config))

    def test_ready_requires_zero_open(self):
        text=self.complete_text().replace("구현 준비 상태: PARTIAL","구현 준비 상태: READY").replace("OPEN_REAL_SOURCE","")
        self.assertIn("READY_WITH_NONZERO_OR_UNKNOWN_OPEN",module.validate_text(text,self.config))

    def test_legacy_english_readiness_is_backward_compatible(self):
        text=self.complete_text().replace("구현 준비 상태: PARTIAL","Implementation Readiness: READY").replace("OPEN_REAL_SOURCE","")+"\nOPEN Count: 0"
        self.assertEqual([],module.validate_text(text,self.config))

if __name__=="__main__": unittest.main()
