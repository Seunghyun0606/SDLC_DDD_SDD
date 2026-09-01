import json
import sys
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
