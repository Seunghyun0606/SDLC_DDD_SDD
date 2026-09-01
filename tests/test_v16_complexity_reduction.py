import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ComplexityReductionRegressionTest(unittest.TestCase):
    def test_requirement_intake_and_analysis_use_one_active_artifact(self):
        harness=json.loads((ROOT/'sdlc/design/contracts/harness-package-contract.json').read_text(encoding='utf-8'))
        self.assertTrue(harness['stage_contracts']['DECOMPOSE']['single_requirement_artifact'])
        self.assertEqual('requirement.md',harness['stage_contracts']['DECOMPOSE']['template'])
        legacy=(ROOT/'sdlc/templates/core/requirement-analysis.md').read_text(encoding='utf-8')
        self.assertIn('DEPRECATED_COMPATIBILITY_VIEW',legacy)

    def test_program_spec_does_not_duplicate_functional_design_semantics(self):
        harness=json.loads((ROOT/'sdlc/design/contracts/harness-package-contract.json').read_text(encoding='utf-8'))
        self.assertTrue(harness['developer_specification']['functional_design_is_semantic_source_of_truth'])
        self.assertTrue(harness['developer_specification']['program_spec_is_implementation_delta'])
        program=(ROOT/'sdlc/templates/core/program-spec.md').read_text(encoding='utf-8')
        self.assertIn('기능 설계 기준점',program)
        self.assertIn('구현 매핑과 차이',program)
        self.assertNotIn('### 업무 정의(6하원칙)',program)
        self.assertNotIn('### 화면·입력·출력 필드 명세',program)
        self.assertNotIn('### CRUD 및 사용자/시스템 행위',program)
        self.assertNotIn('### 핵심 업무 로직과 판단 규칙',program)

    def test_program_readiness_is_one_table_with_seventeen_items(self):
        harness=json.loads((ROOT/'sdlc/design/contracts/harness-package-contract.json').read_text(encoding='utf-8'))
        rules=harness['program_readiness_rules']
        self.assertEqual('SINGLE_READINESS_TABLE',rules['representation'])
        self.assertEqual(17,rules['readiness_item_count'])
        program=(ROOT/'sdlc/templates/core/program-spec.md').read_text(encoding='utf-8')
        self.assertEqual(1,program.count('### 구현 준비도'))

    def test_open_human_view_hides_machine_taxonomy(self):
        harness=json.loads((ROOT/'sdlc/design/contracts/harness-package-contract.json').read_text(encoding='utf-8'))
        self.assertTrue(harness['open_resolution']['human_view_uses_five_status_values'])
        self.assertTrue(harness['open_resolution']['machine_taxonomy_hidden_by_default'])
        workbook=(ROOT/'sdlc/templates/core/open-resolution-workbook.md').read_text(encoding='utf-8')
        self.assertIn('미확정',workbook)
        self.assertIn('확인중',workbook)
        self.assertIn('제안',workbook)
        self.assertIn('확정',workbook)
        self.assertIn('보류',workbook)

    def test_setup_has_five_question_fast_path(self):
        setup=(ROOT/'.cursor/skills/setup/SKILL.md').read_text(encoding='utf-8')
        self.assertIn('5개 질문',setup)
        self.assertIn('프로젝트 유형',setup)
        self.assertIn('요구사항 또는 변경요청 위치',setup)
        self.assertIn('Source/Repository 위치',setup)
        self.assertIn('Build/Test 경로',setup)
        self.assertIn('고객용 문서 필요 여부',setup)

    def test_customer_documents_have_three_active_views_and_projection_runtime(self):
        harness=json.loads((ROOT/'sdlc/design/contracts/harness-package-contract.json').read_text(encoding='utf-8'))
        doc=harness['document_experience']
        self.assertEqual(3,doc['active_customer_view_count'])
        self.assertTrue(doc['legacy_customer_document_ids_are_aliases'])
        self.assertTrue(doc['customer_projection_accepts_internal_markdown_and_canonical_json'])
        self.assertTrue(doc['customer_projection_must_not_invent_missing_business_facts'])
        self.assertTrue((ROOT/doc['customer_projection_script']).is_file())

    def test_canonical_runtime_is_executable_and_wired_to_work_and_change(self):
        harness=json.loads((ROOT/'sdlc/design/contracts/harness-package-contract.json').read_text(encoding='utf-8'))
        runtime=harness['canonical_runtime']
        self.assertTrue(runtime['all_or_nothing'])
        self.assertTrue(runtime['optimistic_revision'])
        self.assertFalse(runtime['delete_supported'])
        self.assertFalse(runtime['source_derived_can_overwrite_confirmed_business'])
        self.assertTrue((ROOT/runtime['script']).is_file())
        self.assertIn(runtime['script'],harness['core_required_files'])
        for skill_path in ['.cursor/skills/work/SKILL.md','.cursor/skills/change/SKILL.md']:
            text=(ROOT/skill_path).read_text(encoding='utf-8')
            self.assertIn('apply_canonical_delta.py',text)
            self.assertIn('--dry-run',text)
            self.assertIn('ADD_PROVENANCE',text)

    def test_reverse_capability_is_not_overclaimed(self):
        harness=json.loads((ROOT/'sdlc/design/contracts/harness-package-contract.json').read_text(encoding='utf-8'))
        self.assertEqual('SOURCE_DRIFT_AND_REVERSE_REVIEW_CANDIDATE',harness['source_drift_reverse']['capability_name'])
        self.assertFalse(harness['source_drift_reverse']['auto_rewrite_artifact'])
        self.assertFalse(harness['source_drift_reverse']['auto_update_business_truth'])

    def test_branch_metadata_does_not_self_validate(self):
        text=(ROOT/'sdlc/design/branch-version.yaml').read_text(encoding='utf-8')
        self.assertIn('status: P0_IMPLEMENTATION_COMPLETE_EXTERNAL_VALIDATION_PENDING',text)
        self.assertIn('verdict: RC_P0_IMPLEMENTED_EXTERNAL_EMPIRICAL_VALIDATION_PENDING',text)
        self.assertIn('self_assessment_is_not_validation: true',text)
        self.assertNotIn('status: VALIDATED',text)
        self.assertNotIn('verdict: VALIDATED',text)
        self.assertNotIn('verdict: PASS\n',text)


if __name__=='__main__':
    unittest.main()
