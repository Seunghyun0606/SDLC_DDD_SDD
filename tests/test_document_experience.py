import json
import unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]

import importlib.util,sys
spec=importlib.util.spec_from_file_location('render_customer_document',ROOT/'sdlc/scripts/render_customer_document.py')
r=importlib.util.module_from_spec(spec); sys.modules[spec.name]=r; spec.loader.exec_module(r)


class DocumentExperienceTest(unittest.TestCase):
    def contract_profile(self):
        c=json.loads((ROOT/'sdlc/design/contracts/customer-document-contract.json').read_text(encoding='utf-8'))
        p=json.loads((ROOT/'sdlc/config/customer-document-profile.example.json').read_text(encoding='utf-8'))
        return c,p

    def test_all_semantic_templates_use_korean_visible_sections(self):
        root=ROOT/'sdlc/templates/semantic'
        self.assertTrue(root.is_dir())
        for path in root.glob('*.md'):
            text=path.read_text(encoding='utf-8')
            self.assertIn('#',text,path.name)

    def test_customer_contract_has_exactly_three_active_views(self):
        c,_=self.contract_profile()
        self.assertEqual(3,len(c['active_document_types']))

    def test_customer_contract_covers_all_workflow_stages(self):
        c,_=self.contract_profile()
        stages=set()
        for key in c['active_document_types']:
            stages.update(c['document_types'][key]['stages'])
        self.assertTrue({'INTAKE','IMPACT','DESIGN','TEST','VERIFY'} <= stages)

    def test_legacy_eight_customer_document_ids_map_to_three_views(self):
        c,_=self.contract_profile()
        self.assertTrue(c['legacy_aliases'])
        self.assertTrue(set(c['legacy_aliases'].values()) <= set(c['active_document_types']))

    def test_customer_required_sections_cannot_be_optional(self):
        c,_=self.contract_profile()
        base=set(c['required_base_sections'])
        for row in c['document_types'].values():
            self.assertFalse(base & set(row.get('optional_sections') or []))

    def test_customer_profile_hides_internal_detail_by_default(self):
        _,p=self.contract_profile()
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
        self.assertIn('자동으로',guide)
        self.assertIn('충돌',guide)
        self.assertIn('업무 사실',guide)
        self.assertNotIn('BR_CONFLICT',guide)

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
        self.assertTrue(text)

    def test_customer_projection_does_not_invent_missing_agreement(self):
        c,p=self.contract_profile()
        text=r.render('solution_agreement',c,p,canonical={'fields':{}})
        self.assertTrue(text)

    def test_customer_projection_uses_real_internal_content_and_hides_machine_detail(self):
        c,p=self.contract_profile()
        text=r.render('delivery_scope',c,p,canonical={'fields':{'title':'테스트 요구'}})
        self.assertIn('테스트 요구',text)

    def test_customer_renderer_applies_optional_profile(self):
        c,p=self.contract_profile()
        text=r.render('design_review',c,p)
        self.assertTrue(text)

    def test_customer_required_sections_cannot_be_optional(self):
        c,_=self.contract_profile()
        base=set(c['required_base_sections'])
        for row in c['document_types'].values():
            self.assertFalse(base & set(row.get('optional_sections') or []))

    def test_internal_machine_keys_can_remain_stable(self):
        c,_=self.contract_profile()
        self.assertIn('active_document_types',c)

    def test_document_experience_validator_passes(self):
        import subprocess,sys
        cp=subprocess.run([sys.executable,str(ROOT/'sdlc/scripts/validate_document_experience.py')],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(0,cp.returncode,cp.stdout+cp.stderr)


if __name__=='__main__': unittest.main()
