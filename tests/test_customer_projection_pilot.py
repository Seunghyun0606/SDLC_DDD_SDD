import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'sdlc/scripts'))
import render_customer_document as r


class CustomerProjectionPilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=json.loads((ROOT/'sdlc/design/contracts/customer-document-contract.json').read_text(encoding='utf-8'))
        cls.profile=json.loads((ROOT/'sdlc/config/customer-document-profile.example.json').read_text(encoding='utf-8'))
        cls.pilot_root=ROOT/'docs/99_파일럿/RQ-CAND-0001'
        cls.artifacts=r.load_artifact_input(cls.pilot_root,cls.contract)

    def test_legacy_pilot_filenames_infer_workflow_stages(self):
        stages={a.get('stage') for a in self.artifacts if a.get('stage')}
        expected={
            'INTAKE','DECOMPOSE','CLARIFY','PROCESS','DISCOVERY','IMPACT',
            'DESIGN','PROGRAM','DEVELOPMENT','TEST','VERIFY','KNOWLEDGE_PROMOTION'
        }
        self.assertTrue(expected.issubset(stages))
        knowledge=next(a for a in self.artifacts if a['source'].endswith('12_KNOWLEDGE_지식승격후보.md'))
        self.assertEqual('KNOWLEDGE_PROMOTION',knowledge['stage'])

    def test_unclassified_index_change_and_check_do_not_contaminate_customer_views(self):
        solution=r.project('solution_agreement',self.contract,self.profile,self.artifacts)
        delivery=r.project('delivery_scope',self.contract,self.profile,self.artifacts)
        acceptance=r.project('acceptance_handover',self.contract,self.profile,self.artifacts)
        self.assertEqual(5,solution['_source_count'])
        self.assertEqual(4,delivery['_source_count'])
        self.assertEqual(3,acceptance['_source_count'])
        self.assertNotIn(None,solution['_source_stages'])
        self.assertNotIn(None,delivery['_source_stages'])
        self.assertNotIn(None,acceptance['_source_stages'])

    def test_existing_requirement_pilot_projects_to_solution_agreement(self):
        projected=r.project('solution_agreement',self.contract,self.profile,self.artifacts,'탄력근로 최초근무계획')
        text=r.render('solution_agreement',self.contract,self.profile,projected)
        self.assertIn('탄력근로제 개선 최초근무계획 자동 설정하는 기능',text)
        self.assertIn('요구·업무·기능 합의서',text)
        self.assertNotIn('RQ-CAND-0001',text)
        self.assertNotIn('REQ_TM_FL001',text)
        self.assertNotIn('Source Hash',text)
        self.assertNotIn('sha256:',text)
        self.assertNotIn('{{',text)

    def test_simulated_source_pilot_projects_to_delivery_scope_without_claiming_real_source(self):
        projected=r.project('delivery_scope',self.contract,self.profile,self.artifacts,'탄력근로 최초근무계획')
        text=r.render('delivery_scope',self.contract,self.profile,projected)
        self.assertIn('Mapper/Schema는 변경하지 않았다',text)
        self.assertIn('영향·개발범위 공유서',text)
        self.assertNotIn('SIMULATED_SOURCE_FIXTURE',text)
        self.assertNotIn('PGM-PILOT-001',text)
        self.assertNotIn('TASK-PILOT',text)
        self.assertNotIn('sha256:',text)

    def test_verify_pilot_projects_limitations_in_customer_language(self):
        projected=r.project('acceptance_handover',self.contract,self.profile,self.artifacts,'탄력근로 최초근무계획')
        text=r.render('acceptance_handover',self.contract,self.profile,projected)
        self.assertIn('구조 검증 완료',text)
        self.assertIn('실제 시스템 검증 필요',text)
        self.assertIn('미실행',text)
        self.assertNotIn('PILOT_STRUCTURAL_PASS',text)
        self.assertNotIn('REAL_SOURCE_PENDING',text)
        self.assertNotIn('NOT_RUN',text)
        self.assertNotIn('INT-PILOT',text)
        self.assertNotIn('ASM-PILOT',text)


if __name__=='__main__': unittest.main()
