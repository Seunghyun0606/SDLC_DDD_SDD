import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'sdlc/scripts'))
import validate_document_experience as v
import render_customer_document as r

class DocumentExperienceTest(unittest.TestCase):
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
        self.assertIn('프로그램 상세 설계',txt)

    def test_customer_contract_covers_all_workflow_stages(self):
        c=json.loads((ROOT/'sdlc/design/contracts/customer-document-contract.json').read_text(encoding='utf-8'))
        stages={s for x in c['document_types'].values() for s in x['stages']}
        expected={'INTAKE','DECOMPOSE','CLARIFY','PROCESS','DISCOVERY','IMPACT','DESIGN','PROGRAM','DEVELOPMENT','TEST','VERIFY','KNOWLEDGE_PROMOTION'}
        self.assertTrue(expected.issubset(stages))

    def test_customer_required_sections_cannot_be_optional(self):
        c=json.loads((ROOT/'sdlc/design/contracts/customer-document-contract.json').read_text(encoding='utf-8'))
        optional=set(c['optional_section_catalog'])
        self.assertFalse(set(c['required_base_sections']) & optional)

    def test_customer_profile_hides_internal_detail_by_default(self):
        p=json.loads((ROOT/'sdlc/config/customer-document-profile.example.json').read_text(encoding='utf-8'))
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

    def test_customer_renderer_keeps_required_sections(self):
        c=json.loads((ROOT/'sdlc/design/contracts/customer-document-contract.json').read_text(encoding='utf-8'))
        p=json.loads((ROOT/'sdlc/config/customer-document-profile.example.json').read_text(encoding='utf-8'))
        text=r.render('design_review',c,p)
        for sec in c['required_base_sections']:
            self.assertIn('## '+sec,text)

    def test_customer_renderer_applies_optional_profile(self):
        c=json.loads((ROOT/'sdlc/design/contracts/customer-document-contract.json').read_text(encoding='utf-8'))
        p=json.loads((ROOT/'sdlc/config/customer-document-profile.example.json').read_text(encoding='utf-8'))
        text=r.render('design_review',c,p)
        self.assertIn('테스트와 인수기준 (선택)',text)
        self.assertNotIn('기술 상세 부록 (선택)',text)

if __name__=='__main__': unittest.main()
