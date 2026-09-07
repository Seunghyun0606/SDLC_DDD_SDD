import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).parents[1]
sys.path.insert(0,str(ROOT/'sdlc/scripts'))
import validate_harness_structure as v

class HarnessStructureTest(unittest.TestCase):
    def setUp(self):
        self.contract=json.loads((ROOT/'sdlc/design/contracts/harness-package-contract.json').read_text(encoding='utf-8'))

    def test_contract_validation_passes(self):
        self.assertEqual(v.validate(ROOT),[])

    def test_official_entrypoint_dependencies_are_in_minimum_core(self):
        core=set(self.contract['core_required_files'])
        required=set(self.contract['official_entrypoint_required_files'])
        self.assertTrue(required)
        self.assertTrue(required <= core)
        for rel in required:
            self.assertTrue((ROOT/rel).is_file(), rel)
        for rel in [
            'sdlc/scripts/runtime_config_v19.py',
            'sdlc/scripts/intake_explainable.py',
            'sdlc/scripts/tailored_work.py',
            'sdlc/scripts/tailored_check.py',
            'sdlc/scripts/tailoring_runtime.py',
            'sdlc/scripts/change_execution_runtime.py',
            'sdlc/config/change-execution-policy.json',
            'sdlc/scripts/interactive_work.py',
            'sdlc/scripts/interactive_change.py',
            'sdlc/agent/skills/work/SKILL.md',
            'sdlc/agent/skills/change/SKILL.md',
            'sdlc/tailoring/standard/STAGE_ORIENTED_FULL.yaml',
            'sdlc/tailoring/standard/STANDARD_3.yaml',
            'sdlc/tailoring/standard/STANDARD_5.yaml',
            'sdlc/tailoring/standard/CUSTOMER_STANDARD_3.yaml',
            'sdlc/tailoring/standard/PM_STANDARD.yaml',
        ]:
            self.assertIn(rel, core)
        self.assertNotIn('sdlc/tailoring/standard/STAGE_ORIENTED_FULL.yaml', set(self.contract['default_tailoring_assets']))
        self.assertIn('sdlc/tailoring/standard/STAGE_ORIENTED_FULL.yaml', set(self.contract['compatibility_tailoring_assets']))
        self.assertNotIn('sdlc/scripts/render_customer_document.py', core)
        self.assertNotIn('sdlc/scripts/detect_source_drift.py', core)

    def test_minimum_executable_core_runs_v19_setup_check_and_tailored_plan(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for rel in self.contract['core_required_files']:
                src=ROOT/rel
                dst=root/rel
                dst.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(src,dst)

            harness=root/'sdlc/scripts/harness.py'
            setup=subprocess.run(
                [sys.executable,str(harness),'setup','--root',str(root),'--name','package-smoke','--mode','GREENFIELD','--delivery','STANDARD'],
                cwd=root,text=True,capture_output=True,check=False,
            )
            self.assertEqual(0,setup.returncode,setup.stderr+'\n'+setup.stdout)
            setup_result=json.loads(setup.stdout)
            self.assertEqual('READY_FOR_PLAN',setup_result['status'])
            self.assertEqual('INTERACTIVE',setup_result['agent_execution']['execution_mode'])
            for rel in [
                'docs/00_시작/START_HERE.md',
                'docs/00_시작/02_PROJECT_설정가이드.md',
                'docs/00_시작/03_TAILORING_설정가이드.md',
            ]:
                self.assertTrue((root/rel).is_file(),rel)

            check=subprocess.run(
                [sys.executable,str(harness),'check','--root',str(root),'--setup'],
                cwd=root,text=True,capture_output=True,check=False,
            )
            self.assertEqual(0,check.returncode,check.stderr+'\n'+check.stdout)
            check_result=json.loads(check.stdout)
            self.assertEqual('READY',check_result['status'])
            self.assertEqual('INTERACTIVE',check_result['setup']['agent_execution']['execution_mode'])

            tailoring=root/'sdlc/scripts/tailoring_runtime.py'
            for profile in ['STANDARD_3','STANDARD_5','STAGE_ORIENTED_FULL','CUSTOMER_STANDARD_3','PM_STANDARD']:
                cp=subprocess.run(
                    [sys.executable,str(tailoring),'validate-profile','--root',str(root),'--profile',profile],
                    cwd=root,text=True,capture_output=True,check=False,
                )
                self.assertEqual(0,cp.returncode,f'{profile}: {cp.stderr}\n{cp.stdout}')
                self.assertEqual('VALID',json.loads(cp.stdout)['status'])

            store_path=root/'sdlc/canonical/store.json'
            store=json.loads(store_path.read_text(encoding='utf-8'))
            store.setdefault('entities',{})['RQ-001']={
                'id':'RQ-001','entity_type':'RQ','fields':{'name':'패키지 스모크'},
                'truth_status':'CANDIDATE','provenance':[],
            }
            store_path.write_text(json.dumps(store,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            work=subprocess.run(
                [sys.executable,str(harness),'work','--root',str(root),'--target','RQ-001','--stage','DESIGN','--plan-only'],
                cwd=root,text=True,capture_output=True,check=False,
            )
            self.assertEqual(0,work.returncode,work.stderr+'\n'+work.stdout)
            work_result=json.loads(work.stdout)
            self.assertEqual('PLAN_READY',work_result['status'])
            self.assertEqual('DESIGN',work_result['plan']['selection']['stage'])
            self.assertTrue(work_result['plan']['selection']['artifact_path'].startswith('docs/10_산출물/'))
            self.assertEqual('STANDARD_5',work_result['plan']['tailoring']['profiles']['internal'])
            self.assertIn('execution_policy', work_result['plan'])

    def test_all_source_enabled_stages_have_evidence_templates(self):
        stages=[k for k,x in self.contract['stage_contracts'].items() if x.get('source_evidence')]
        self.assertEqual(stages,['DISCOVERY','IMPACT','DESIGN','PROGRAM','DEVELOPMENT','TEST','VERIFY'])
        for stage in stages:
            txt=(ROOT/'sdlc/templates/core'/self.contract['stage_contracts'][stage]['template']).read_text(encoding='utf-8')
            for marker in ['Locator','Source Hash','Confidence','Status']:
                self.assertIn(marker,txt)

    def test_work_references_use_standard_contract_sections(self):
        for spec in self.contract['stage_contracts'].values():
            txt=(ROOT/'.cursor/skills/work/references'/spec['reference']).read_text(encoding='utf-8')
            for sec in self.contract['work_reference_required_sections']:
                self.assertIn(sec,txt)

    def test_templates_keep_traceability_and_uncertainty_sections(self):
        for p in (ROOT/'sdlc/templates/core').glob('*.md'):
            txt=p.read_text(encoding='utf-8')
            self.assertIn('## 미확정 사항·주의·가정',txt,p.name)
            self.assertIn('## 관련 ID 및 추적성',txt,p.name)

    def test_overlay_precedence_is_portable(self):
        profile=(ROOT/'sdlc/config/project-profile.example.yaml').read_text(encoding='utf-8')
        positions=[profile.index('- '+x) for x in self.contract['overlay_precedence']]
        self.assertEqual(positions,sorted(positions))

    def test_source_profile_prevents_full_repo_llm_first(self):
        txt=(ROOT/'sdlc/config/source-profile.example.yaml').read_text(encoding='utf-8')
        self.assertIn('static_analysis_first: true',txt)
        self.assertIn('full_repository_llm_scan: false',txt)

    def test_core_rule_preserves_truth_and_execution_guard(self):
        txt=(ROOT/'.cursor/rules/00-core.mdc').read_text(encoding='utf-8')
        self.assertIn('OBSERVED',txt)
        self.assertIn('Business Rule로 자동 확정하지 않는다',txt)
        self.assertIn('Execution Guard',txt)
        self.assertIn('외부 요구사항 ID',txt)

    def test_project_overlay_skeleton_exists(self):
        for rel in ['sdlc/custom/project/README.md','sdlc/custom/project/rules/project-rule.example.mdc','sdlc/custom/project/config/source-profile.example.yaml','sdlc/custom/project/templates/README.md','sdlc/custom/project/standards/README.md','sdlc/custom/domain/README.md']:
            self.assertTrue((ROOT/rel).exists(),rel)

if __name__=='__main__': unittest.main()
