import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]
SCRIPT=ROOT/'sdlc/scripts/render_customer_document.py'
spec=importlib.util.spec_from_file_location('render_customer_document',SCRIPT)
r=importlib.util.module_from_spec(spec); sys.modules[spec.name]=r; spec.loader.exec_module(r)


class DocumentExperienceTest(unittest.TestCase):
    def contract_profile(self):
        c=json.loads((ROOT/'sdlc/design/contracts/customer-document-contract.json').read_text(encoding='utf-8'))
        p=json.loads((ROOT/'sdlc/config/customer-document-profile.example.json').read_text(encoding='utf-8'))
        return c,p

    def test_all_core_templates_use_korean_visible_sections(self):
        contract=json.loads((ROOT/'sdlc/design/contracts/harness-package-contract.json').read_text(encoding='utf-8'))
        for rel in [x for x in contract['core_required_files'] if x.startswith('sdlc/templates/core/') and x.endswith('.md')]:
            text=(ROOT/rel).read_text(encoding='utf-8')
            for sec in contract['template_required_sections']:
                self.assertIn(sec,text,rel)

    def test_internal_machine_keys_can_remain_stable(self):
        text=(ROOT/'sdlc/templates/core/requirement.md').read_text(encoding='utf-8')
        self.assertIn('<!-- machine:',text)
        self.assertIn('## 문서 목적',text)
        self.assertIn('## 한눈에 보기',text)

    def test_customer_contract_has_exactly_three_active_views(self):
        c,_=self.contract_profile()
        self.assertEqual(c['active_document_types'],['solution_agreement','delivery_scope','acceptance_handover'])
        self.assertEqual(len(c['document_types']),3)

    def test_legacy_eight_customer_document_ids_map_to_three_views(self):
        c,_=self.contract_profile()
        self.assertEqual(len(c['legacy_document_aliases']),8)
        self.assertEqual(set(c['legacy_document_aliases'].values()),set(c['active_document_types']))

    def test_customer_contract_covers_all_workflow_stages(self):
        c,_=self.contract_profile()
        stages=set()
        for spec in c['document_types'].values(): stages.update(spec['source_stages'])
        self.assertEqual(stages,{
            'INTAKE','DECOMPOSE','CLARIFY','PROCESS','DISCOVERY','IMPACT',
            'DESIGN','PROGRAM','DEVELOPMENT','TEST','VERIFY','KNOWLEDGE_PROMOTION'
        })

    def test_customer_required_sections_cannot_be_optional(self):
        c,_=self.contract_profile()
        required=set(c['required_base_sections'])
        for spec in c['document_types'].values():
            self.assertFalse(required.intersection(spec.get('optional',[])))

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
        guide=(ROOT/'docs/00_시작/11_INPUT_자료_준비가이드.md').read_text(encoding='utf-8')
        self.assertIn('자동',guide)
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
        self.assertIn('## 범위와 제외범위 (선택)',text)
        self.assertIn('## 테스트와 인수기준 (선택)',text)
        self.assertNotIn('## 기술 상세 부록 (선택)',text)

    def test_customer_projection_uses_real_internal_content_and_hides_machine_detail(self):
        c,p=self.contract_profile()
        artifacts=[
            {
                'source':'docs/01.md','stage':'DECOMPOSE','title':'RQ-0042 휴가 취소 자동반영',
                'sections':{
                    '한눈에 보기':'휴가 취소 시 근태를 다시 계산해야 합니다. RQ-0042',
                    '상세 내용':'기존 휴가 취소 후 근태 반영이 누락됩니다. REQ_TM_001',
                    '미확정 사항·주의·가정':'OPEN: 재계산 기준시각 확인 필요',
                    '다음 작업':'고객과 재계산 시점을 확인합니다.'
                },
                'raw':'Source Hash: sha256:abc\nConfidence: HIGH'
            },
            {
                'source':'docs/02.md','stage':'DESIGN','title':'기능 설계',
                'sections':{
                    '상세 내용':'취소 저장 후 근태 재계산 서비스를 호출합니다. PGM-001',
                    '한눈에 보기':'휴가 취소와 근태 재계산을 하나의 사용자 흐름으로 처리합니다.'
                },
                'raw':'Locator: src/A.java:10-20'
            }
        ]
        projected=r.project('solution_agreement',c,p,artifacts,'휴가 취소 자동반영')
        text=r.render('solution_agreement',c,p,projected)
        self.assertIn('휴가 취소 시 근태를 다시 계산해야 합니다.',text)
        self.assertIn('취소 저장 후 근태 재계산 서비스를 호출합니다.',text)
        self.assertNotIn('RQ-0042',text)
        self.assertNotIn('REQ_TM_001',text)
        self.assertNotIn('PGM-001',text)
        self.assertNotIn('sha256:',text)

    def test_customer_projection_does_not_invent_missing_agreement(self):
        c,p=self.contract_profile()
        artifacts=[{'source':'docs/impact.md','stage':'IMPACT','title':'영향분석','sections':{'상세 내용':'영향 분석 진행 중'}}]
        projected=r.project('delivery_scope',c,p,artifacts)
        self.assertIn('확정 내용을 찾지 못했습니다',projected['합의된 내용'])

    def test_document_experience_validator_passes(self):
        script=ROOT/'sdlc/scripts/validate_document_experience.py'
        spec=importlib.util.spec_from_file_location('validate_document_experience',script)
        mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        self.assertEqual([],mod.validate(ROOT))


if __name__=='__main__': unittest.main()
