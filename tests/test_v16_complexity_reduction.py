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
