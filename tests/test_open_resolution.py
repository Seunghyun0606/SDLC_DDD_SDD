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

    def test_human_view_is_five_simple_statuses(self):
        self.assertEqual(['미확정','확인중','제안','확정','보류'],self.contract['human_view']['status_values'])
        self.assertTrue(self.contract['principles']['human_view_is_simpler_than_machine_metadata'])

    def test_machine_fields_remain_traceable_but_not_human_required(self):
        machine=set(self.contract['machine_required_item_fields'])
        expected={'open_item_id','category','decision_domain','resolution_method','basis_class','proposed_or_observed_value','evidence_or_rationale','decision_owner_role','resolution_status','downstream_impact'}
        self.assertTrue(expected.issubset(machine))
        human=set(self.contract['human_view']['required_fields'])
        self.assertNotIn('decision_domain',human)
        self.assertNotIn('basis_class',human)
        self.assertNotIn('resolution_method',human)
        self.assertIn('resolution_action',human)
        self.assertIn('human_status',human)

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

    def test_workbook_uses_human_first_sections(self):
        txt=(ROOT/'sdlc/templates/core/open-resolution-workbook.md').read_text(encoding='utf-8')
        for marker in ['### OPEN 해소 목록','### 업무 시나리오 확인','### 설계 확인 항목','### 결정 기록','### 내부 자동 관리 정보']:
            self.assertIn(marker,txt)
        header='| OPEN ID | 관련 항목 | 무엇을 확인하거나 결정해야 하는가 | 어떻게 확인할 것인가 | 현재 확인된 내용 또는 제안 | 누가 확인하거나 결정하는가 | 진행 상태 |'
        self.assertIn(header,txt)

    def test_interview_view_is_derived_not_source_of_resolution(self):
        skill=(ROOT/'.cursor/skills/open-resolve/SKILL.md').read_text(encoding='utf-8')
        self.assertIn('동일 OPEN 정보에서 필요한 고객 질문만 파생',skill)

    def test_clarify_hides_machine_taxonomy_from_required_user_input(self):
        txt=(ROOT/'.cursor/skills/work/references/clarify.md').read_text(encoding='utf-8')
        self.assertIn('Machine metadata',txt)
        self.assertIn('일반 사용자에게 Decision Domain/Resolution Method/Basis Class를 필수 입력으로 요구하지 않는다',txt)

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
