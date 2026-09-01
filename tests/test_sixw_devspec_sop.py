import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIXW = json.loads((ROOT / "sdlc/design/contracts/business-scenario-sixw-contract.json").read_text(encoding="utf-8"))
DEV = json.loads((ROOT / "sdlc/design/contracts/developer-spec-contract.json").read_text(encoding="utf-8"))
SOP = json.loads((ROOT / "sdlc/design/contracts/sop-extraction-contract.json").read_text(encoding="utf-8"))
EXTRACT = json.loads((ROOT / "sdlc/design/contracts/br-document-extraction-contract.json").read_text(encoding="utf-8"))
READINESS = json.loads((ROOT / "sdlc/config/program-spec-readiness.json").read_text(encoding="utf-8"))


class SixWBusinessScenarioTest(unittest.TestCase):
    def test_six_dimensions_are_exact_and_ordered(self):
        self.assertEqual(["who", "when", "where", "what", "how", "why"], [x["id"] for x in SIXW["required_dimensions"]])

    def test_missing_sixw_is_open_not_invented(self):
        self.assertTrue(SIXW["rules"]["missing_dimension_must_be_open_not_invented"])
        self.assertTrue(SIXW["rules"]["program_spec_must_trace_to_business_scenario"])

    def test_process_template_has_sixw_business_definition(self):
        text = (ROOT / "sdlc/templates/core/process-analysis.md").read_text(encoding="utf-8")
        for marker in ["누가(Who)", "언제(When)", "어디서(Where)", "무엇을(What)", "어떻게(How)", "왜(Why)"]:
            self.assertIn(marker, text)
        self.assertIn("자연어 업무 정의", text)

    def test_customer_process_and_design_views_expose_sixw(self):
        for path in [
            ROOT / "sdlc/templates/customer/standard/02_업무_프로세스_협의서.md",
            ROOT / "sdlc/templates/customer/standard/04_기능_설계_협의서.md",
        ]:
            self.assertIn("누가·언제·어디서·무엇을·어떻게·왜", path.read_text(encoding="utf-8"))


class DeveloperSpecificationTest(unittest.TestCase):
    def test_functional_design_contains_semantic_required_markers(self):
        text = (ROOT / "sdlc/templates/core/functional-design.md").read_text(encoding="utf-8")
        for marker in DEV["functional_design_required_markers"]:
            self.assertIn(marker, text)

    def test_program_spec_contains_only_implementation_delta_markers(self):
        text = (ROOT / "sdlc/templates/core/program-spec.md").read_text(encoding="utf-8")
        for marker in DEV["program_spec_required_markers"]:
            self.assertIn(marker, text)
        for old_duplicate in [
            "### 업무 시나리오(6하원칙) 연결",
            "### 화면·메뉴·컴포넌트 상세",
            "### 화면·입력·출력 필드 상세",
            "### CRUD 동작 매트릭스",
            "### 업무 검증·판단·상태 규칙",
        ]:
            self.assertNotIn(old_duplicate, text)

    def test_functional_design_is_semantic_source_of_truth(self):
        ownership=DEV["ownership_model"]
        self.assertEqual("SEMANTIC_SOURCE_OF_TRUTH",ownership["functional_design"])
        self.assertEqual("IMPLEMENTATION_DELTA_AND_EXECUTION_READINESS",ownership["program_spec"])
        self.assertTrue(DEV["rules"]["functional_design_semantics_must_not_be_duplicated_in_program_spec"])
        self.assertTrue(DEV["rules"]["program_spec_records_only_implementation_mapping_and_delta"])

    def test_program_dor_remains_17_items_but_one_table(self):
        self.assertEqual(17, len(READINESS["required_fields"]))
        self.assertEqual("SINGLE_READINESS_TABLE",READINESS["representation"])

    def test_na_requires_reason(self):
        self.assertTrue(DEV["rules"]["not_applicable_requires_reason"])
        self.assertTrue(DEV["rules"]["screen_sections_are_not_applicable_only_for_non_ui_entry_points_with_reason"])


class SopExtractionTest(unittest.TestCase):
    def test_extraction_contract_preserves_structure(self):
        self.assertIn("content_kind", EXTRACT["required_output_fields"])
        self.assertIn("structured_content", EXTRACT["optional_structure_fields"])
        self.assertIn("format_context", EXTRACT["optional_structure_fields"])

    def test_sop_skill_has_pre_extraction_prompt_and_targets(self):
        text = (ROOT / ".cursor/skills/sop-extract/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("## 사전 추출 Prompt", text)
        for marker in ["누가(Who)", "언제(When)", "어디서(Where)", "무엇을(What)", "어떻게(How)", "왜(Why)", "공통코드", "Integration Candidate"]:
            self.assertIn(marker, text)

    def test_format_parser_and_semantic_extraction_are_separate(self):
        boundary = SOP["format_adapter_boundary"]
        self.assertTrue(boundary["core_skill_consumes_normalized_evidence_chunks"])
        self.assertEqual("ADAPTER_OR_TOOL_RESPONSIBILITY", boundary["pdf_docx_xlsx_pptx_ocr_parser_implementation"])

    def test_sop_does_not_auto_promote_business_truth(self):
        self.assertTrue(SOP["rules"]["source_rule_is_candidate_until_authority_or_human_confirmation"])
        text = (ROOT / ".cursor/skills/sop-extract/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("CONFIRMED_BR", text)
        self.assertIn("승격하지 않는다", text)


if __name__ == "__main__":
    unittest.main()
