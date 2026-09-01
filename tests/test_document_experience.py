import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'sdlc/scripts'))
import validate_document_experience as v
import render_customer_document as r

class DocumentExperienceTest(unittest.TestCase):
    def contract_profile(self):
        c=json.loads((ROOT/'sdlc/design/contracts/customer-document-contract.json').read_text(encoding='utf-8'))
        p=json.loads((ROOT/'sdlc/config/customer-document-profile.example.json').read_text(encoding='utf-8'))
        return c,p

    def test_document_experience_validator_passes(self):
        self.assertEqual(v.validate(ROOT),[])

    def test_all_core_templates_use_korean_visible_sections(self):
        for p in (ROOT/'sdlc/templates/core').glob('*.md'):
            txt=p.read_text(encoding='utf-8')
            for sec in v.KOREAN_SECTIONS:
                self.assertIn(sec,txt,p.name)

    def test_internal_machine_keys_can_remain_stable(self):
        txt=(ROOT/'sdlc/templates/core/program-spec.md').read_text(encoding='utf-8')
        self.assertIn('document_type: program_spec',txt)
        self.assertIn('stage: PROGRAM',txt)
        self.assertIn('프로그램 구현 명세',txt)

    def test_customer_contract_has_exactly_three_active_views(self):
        c,_=self.contract_profile()
        self.assertEqual(['solution_agreement','delivery_scope','acceptance_handover'],c['active_document_types'])
        self.assertEqual(set(c['active_document_types']),set(c['document_types']))
        for dtype in c['active_document_types']:
            template=ROOT/'sdlc/templates/customer/standard'/c['document_types'][dtype]['template']
            self.assertTrue(template.exists(),dtype)

    def test_customer_contract_covers_all_workflow_stages(self):
        c,_=self.contract_profile()
        stages={s for x in c['document_types'].values() for s in x['stages']}
        expected={'INTAKE','DECOMPOSE','CLARIFY','PROCESS','DISCOVERY','IMPACT','DESIGN','PROGRAM','DEVELOPMENT','TEST','VERIFY','KNOWLEDGE_PROMOTION'}
        self.assertTrue(expected.issubset(stages))

    def test_legacy_eight_customer_document_ids_map_to_three_views(self):
        c,_=self.contract_profile()
        self.assertEqual(8,len(c['legacy_document_aliases']))
        for old,target in c['legacy_document_aliases'].items():
            self.assertIn(target,c['active_document_types'],old)

    def test_customer_required_sections_cannot_be_optional(self):
        c,_=self.contract_profile()
        optional=set(c['optional_section_catalog'])
        self.assertFalse(set(c['required_base_sections']) & optional)

    def test_customer_profile_hides_internal_detail_by_default(self):
        _,p=self.contract_profile()
        self.assertFalse(p['display']['show_internal_ids'])
        self.assertFalse(p['display']['show_source_hash'])
        self.assertEqual(p['display']['technical_detail_location'],'APPENDIX')

    def test_br_intake_minimum_is_lightweight_and_nonblocking(self):
        p=json.loads((ROOT/'sdlc/config/br-intake-profile.example.json').read_text(encoding='utf-8'))
        self.assertEqual(p['minimum_manifest_fields'],['document_id','path'])
        self.assertTrue(p['preserve_original_files'])
        self.assertTrue(p['non_blocking_missing_metadata'])

    def test_br_candidate_requires_provenance(self):
        s=json.loads((ROOT/'sdlc/design/contracts/br-candidate.schema.json').read_text(encoding='utf-8'))
        ev=s['properties']['source_evidence']
        self.assertEqual(ev['minItems'],1)
        self.assertEqual(set(ev['items']['required']),{'document_id','locator','source_hash','confidence'})

    def test_br_conflicts_are_not_auto_resolved(self):
        guide=(ROOT/'sdlc/guides/09_비정형_고객문서_BR_Intake_가이드.md').read_text(encoding='utf-8')
        self.assertIn('자동으로',guide)
        self.assertIn('BR_CONFLICT',guide)

    def test_customer_renderer_keeps_required_sections_and_legacy_alias(self):
        c,p=self.contract_profile()
        text=r.render('design_review',c,p)
        self.assertIn('요구·업무·기능 합의서',text)
        self.assertIn('Legacy customer document type `design_review`',text)
        for sec in c['required_base_sections']:
            self.assertIn('## '+sec,text)

    def test_customer_renderer_applies_optional_profile(self):
        c,p=self.contract_profile()
        text=r.render('design_review',c,p)
        self.assertIn('테스트와 인수기준 (선택)',text)
        self.assertNotIn('기술 상세 부록 (선택)',text)

    def test_customer_projection_uses_real_internal_content_and_hides_machine_detail(self):
        c,p=self.contract_profile()
        internal='''---
document_type: functional_design
generated_by:
  skill: work
  stage: DESIGN
---
# RQ-CAND-0001 탄력근로 최초근무계획 기능설계

## 한눈에 보기
탄력근로 대상자의 최초 근무계획을 기본 근무스케줄에 따라 자동으로 생성한다.

## 현재 문제 또는 요청 내용
최초 근무계획을 수작업으로 등록해야 한다.

## 업무 정의(6하원칙)
관리자가 근무계획 화면에서 대상자를 선택하면 기본 근무스케줄을 기준으로 계획을 만든다.

## 기능 요구사항(FR)
- FR-0001 최초 근무계획을 자동 생성한다.
- Source Hash: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa

## 합의된 내용
- 최초 계획은 기본 근무스케줄을 기준으로 생성한다.

## 미확정 사항·주의·가정
- OPEN: 관리자 승인 시점을 고객과 확인해야 한다.

## 다음 작업
고객과 승인 시점을 확인한 뒤 기능 설계를 확정한다.
'''
        artifact=r.parse_markdown_artifact(internal,'functional-design.md')
        projected=r.project('design_review',c,p,[artifact])
        text=r.render('design_review',c,p,projected)
        self.assertIn('탄력근로 대상자의 최초 근무계획',text)
        self.assertIn('최초 근무계획을 자동 생성한다',text)
        self.assertIn('관리자 승인 시점을 고객과 확인',text)
        self.assertNotIn('FR-0001',text)
        self.assertNotIn('RQ-CAND-0001',text)
        self.assertNotIn('Source Hash',text)
        self.assertNotIn('sha256:',text)
        self.assertNotIn('OPEN:',text)
        self.assertNotIn('{{',text)

    def test_customer_projection_does_not_invent_missing_agreement(self):
        c,p=self.contract_profile()
        artifact=r.parse_markdown_artifact('''---\ndocument_type: requirement\ngenerated_by:\n  stage: INTAKE\n---\n# 요청\n\n## 한눈에 보기\n근무계획 자동 생성 요청\n''','requirement.md')
        projected=r.project('solution_agreement',c,p,[artifact])
        self.assertEqual(c['projection']['empty_section_text'],projected['합의된 내용'])

if __name__=='__main__': unittest.main()
