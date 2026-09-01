import json
import unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]

class OpenResolutionContractTest(unittest.TestCase):
    def setUp(self):
        self.contract=json.loads((ROOT/'sdlc/design/contracts/open-resolution-contract.json').read_text(encoding='utf-8'))

    def test_sop_is_optional_and_open_is_actionable(self):
        p=self.contract['principles']
        self.assertTrue(p['open_is_actionable_design_backlog'])
        self.assertTrue(p['sop_is_optional'])
        self.assertTrue(p['missing_sop_does_not_block_design'])

    def test_resolution_methods_cover_human_analysis_and_experience(self):
        methods=set(self.contract['resolution_methods'])
        expected={'CUSTOMER_INTERVIEW','WORKSHOP','EXISTING_SYSTEM_ANALYSIS','SOURCE_ANALYSIS','DATA_ANALYSIS','PROJECT_STANDARD','DESIGNER_PROPOSAL','DEVELOPER_PROPOSAL','ARCHITECT_DECISION'}
        self.assertTrue(expected.issubset(methods))

    def test_proposal_is_not_business_truth(self):
        self.assertTrue(self.contract['principles']['proposal_is_not_automatic_business_truth'])
        self.assertIn('CONFIRMED_BUSINESS',self.contract['resolution_status'])
        self.assertIn('ACCEPTED_DESIGN',self.contract['resolution_status'])

    def test_existing_system_is_as_is_not_target_policy(self):
        self.assertTrue(self.contract['principles']['existing_system_observation_is_not_automatic_target_policy'])
        self.assertIn('OBSERVED_AS_IS',self.contract['resolution_status'])

    def test_required_item_fields_make_resolution_traceable(self):
        required=set(self.contract['required_item_fields'])
        expected={'open_item_id','category','decision_domain','resolution_method','basis_class','proposed_or_observed_value','evidence_or_rationale','decision_owner_role','resolution_status','downstream_impact'}
        self.assertTrue(expected.issubset(required))

    def test_default_routes_are_category_specific(self):
        route=self.contract['default_resolution_route']
        self.assertIn('BUSINESS_OWNER_INTERVIEW',route['SIX_W_WHY'])
        self.assertIn('EXISTING_SYSTEM_ANALYSIS',route['UI_SCREEN'])
        self.assertIn('DEVELOPER_PROPOSAL',route['DATA_QUERY'])
        self.assertIn('PROJECT_STANDARD',route['NFR'])

    def test_project_authority_profile_is_customizable(self):
        txt=(ROOT/'sdlc/config/open-resolution-profile.example.yaml').read_text(encoding='utf-8')
        for marker in ['authority_matrix:','BUSINESS:','TECHNICAL:','can_confirm:','can_propose:','sop_required: false']:
            self.assertIn(marker,txt)

    def test_workbook_covers_business_and_developer_open_items(self):
        txt=(ROOT/'sdlc/templates/core/open-resolution-workbook.md').read_text(encoding='utf-8')
        for marker in ['### OPEN 해소 목록','### 6하원칙 업무정의 해소표','### 화면·필드·CRUD 해소표','### 업무 규칙·상태·예외 해소표','### 데이터·조회·공통코드 해소표','### 연계·권한·NFR·테스트 해소표','### 결정 기록']:
            self.assertIn(marker,txt)

    def test_interview_view_is_not_question_only(self):
        txt=(ROOT/'sdlc/templates/core/interview-questions.md').read_text(encoding='utf-8')
        for marker in ['왜 필요한가','권장 선택지/예시','인터뷰 없이 분석으로 해소할 항목','설계자·개발자 제안 항목','확인/채택 권한자']:
            self.assertIn(marker,txt)

    def test_clarify_uses_multiple_resolution_routes(self):
        txt=(ROOT/'.cursor/skills/work/references/clarify.md').read_text(encoding='utf-8')
        for marker in ['인터뷰·현행/Source/Data 분석·프로젝트 표준·설계/개발 제안','open-resolution-workbook.md','모든 OPEN을 인터뷰 질문으로만 바꾸지 않는다']:
            self.assertIn(marker,txt)

    def test_greenfield_and_brownfield_do_not_require_sop(self):
        g=(ROOT/'sdlc/starter-kits/greenfield/README.md').read_text(encoding='utf-8')
        b=(ROOT/'sdlc/starter-kits/brownfield/README.md').read_text(encoding='utf-8')
        self.assertIn('필수 입력이 아니다',g)
        self.assertIn('선택 Evidence',b)
        self.assertIn('OPEN 해소 기본 경로',g)
        self.assertIn('OPEN 해소 기본 경로',b)

    def test_work_skill_routes_open_to_resolution_skill(self):
        txt=(ROOT/'.cursor/skills/work/SKILL.md').read_text(encoding='utf-8')
        self.assertIn('OPEN은 대기표시가 아니라 해소할 설계 Backlog',txt)
        self.assertIn('.cursor/skills/open-resolve/SKILL.md',txt)

if __name__=='__main__': unittest.main()
