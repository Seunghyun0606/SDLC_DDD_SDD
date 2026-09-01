import json
import unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]


class ComplexityReductionRegressionTest(unittest.TestCase):
    def test_setup_has_five_question_fast_path(self):
        text=(ROOT/'.cursor/skills/setup/SKILL.md').read_text(encoding='utf-8')
        for marker in [
            '1. **프로젝트 유형**',
            '2. **요구사항 또는 변경요청 위치**',
            '3. **Source/Repository 위치**',
            '4. **Build/Test 경로**',
            '5. **고객용 문서 필요 여부**',
        ]:
            self.assertIn(marker,text)
        self.assertIn('이 5개가 있으면 `/work`를 시작할 수 있다',text)
        self.assertIn('Profile을 채우는 것만으로 Adapter 기능이 구현되는 것은 아니다',text)

    def test_requirement_intake_and_analysis_use_one_active_artifact(self):
        harness=json.loads((ROOT/'sdlc/design/contracts/harness-package-contract.json').read_text(encoding='utf-8'))
        decompose=harness['stage_contracts']['DECOMPOSE']
        self.assertEqual('requirement.md',decompose['template'])
        self.assertTrue(decompose['single_requirement_artifact'])
        req=(ROOT/'sdlc/templates/core/requirement.md').read_text(encoding='utf-8')
        for marker in ['### 원문과 식별정보','### 기능 요구사항(FR)','### 업무 규칙(BR) 후보','### 인수 조건(AC)']:
            self.assertIn(marker,req)
        legacy=(ROOT/'sdlc/templates/core/requirement-analysis.md').read_text(encoding='utf-8')
        self.assertIn('DEPRECATED_COMPATIBILITY_VIEW',legacy)
        self.assertIn('이 View에서 FR/BR/AC를 다시 작성하지 않는다',legacy)

    def test_program_spec_does_not_duplicate_functional_design_semantics(self):
        text=(ROOT/'sdlc/templates/core/program-spec.md').read_text(encoding='utf-8')
        for old in [
            '### 업무 시나리오(6하원칙) 연결',
            '### 화면·메뉴·컴포넌트 상세',
            '### 화면·입력·출력 필드 상세',
            '### CRUD 동작 매트릭스',
            '### 업무 검증·판단·상태 규칙',
        ]:
            self.assertNotIn(old,text)
        self.assertIn('### 기능 설계 기준점',text)
        self.assertIn('### 구현 매핑과 차이',text)

    def test_program_readiness_is_one_table_with_seventeen_items(self):
        config=json.loads((ROOT/'sdlc/config/program-spec-readiness.json').read_text(encoding='utf-8'))
        text=(ROOT/'sdlc/templates/core/program-spec.md').read_text(encoding='utf-8')
        self.assertEqual('SINGLE_READINESS_TABLE',config['representation'])
        self.assertEqual(17,len(config['required_fields']))
        for field in config['required_fields']:
            self.assertIn(field['marker'],text,field['id'])

    def test_open_human_view_hides_machine_taxonomy(self):
        contract=json.loads((ROOT/'sdlc/design/contracts/open-resolution-contract.json').read_text(encoding='utf-8'))
        workbook=(ROOT/'sdlc/templates/core/open-resolution-workbook.md').read_text(encoding='utf-8')
        self.assertEqual(['미확정','확인중','제안','확정','보류'],contract['human_view']['status_values'])
        human=set(contract['human_view']['required_fields'])
        for internal in ['decision_domain','resolution_method','basis_class','resolution_status','downstream_impact']:
            self.assertNotIn(internal,human)
        self.assertIn('### 내부 자동 관리 정보',workbook)
        self.assertIn('어떻게 확인할 것인가',workbook)

    def test_customer_documents_have_three_active_views_and_projection_runtime(self):
        harness=json.loads((ROOT/'sdlc/design/contracts/harness-package-contract.json').read_text(encoding='utf-8'))
        customer=json.loads((ROOT/'sdlc/design/contracts/customer-document-contract.json').read_text(encoding='utf-8'))
        expected=['solution_agreement','delivery_scope','acceptance_handover']
        self.assertEqual(expected,customer['active_document_types'])
        self.assertEqual(expected,harness['document_experience']['active_customer_views'])
        self.assertEqual(3,harness['document_experience']['active_customer_view_count'])
        self.assertEqual(8,len(customer['legacy_document_aliases']))
        self.assertTrue(harness['document_experience']['legacy_customer_document_ids_are_aliases'])
        self.assertTrue((ROOT/harness['document_experience']['customer_projection_script']).is_file())
        for dtype in expected:
            template=customer['document_types'][dtype]['template']
            self.assertTrue((ROOT/'sdlc/templates/customer/standard'/template).is_file())

    def test_canonical_runtime_is_executable_and_wired_to_work_and_change(self):
        harness=json.loads((ROOT/'sdlc/design/contracts/harness-package-contract.json').read_text(encoding='utf-8'))
        runtime=harness['canonical_runtime']
        self.assertEqual('sdlc/scripts/apply_canonical_delta.py',runtime['script'])
        self.assertEqual('sdlc/canonical/store.json',runtime['default_store'])
        self.assertEqual(['UPSERT_ENTITY','UPSERT_RELATION','ADD_PROVENANCE'],runtime['operations'])
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
        self.assertIn('status: IMPLEMENTATION_IN_PROGRESS',text)
        self.assertIn('verdict: RC_IMPLEMENTATION_NOT_YET_VALIDATED',text)
        self.assertIn('self_assessment_is_not_validation: true',text)


if __name__=='__main__':
    unittest.main()
