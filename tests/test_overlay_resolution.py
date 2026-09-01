import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / 'sdlc' / 'scripts' / 'resolve_overlay.py'
spec = importlib.util.spec_from_file_location('resolve_overlay', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class OverlayResolutionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / '.cursor/rules').mkdir(parents=True)
        (self.root / '.cursor/skills/work/references').mkdir(parents=True)
        (self.root / 'sdlc/templates/core').mkdir(parents=True)
        (self.root / 'sdlc/config').mkdir(parents=True)
        (self.root / 'sdlc/custom/project/rules').mkdir(parents=True)
        (self.root / 'sdlc/custom/domain/time').mkdir(parents=True)
        (self.root / '.cursor/rules/00-core.mdc').write_text('CORE\n', encoding='utf-8')
        (self.root / '.cursor/skills/work/references/program.md').write_text('## Purpose\nCore purpose\n\n## Quality Check\nCore QC\n', encoding='utf-8')
        (self.root / 'sdlc/templates/core/program-spec.md').write_text('## 본문\nCore body {{term}}\n\n## 다음 작업\nCore next\n', encoding='utf-8')
        (self.root / 'sdlc/custom/project/rules/time.mdc').write_text('PROJECT RULE\n', encoding='utf-8')
        (self.root / 'sdlc/custom/project/overlay.json').write_text(json.dumps({
            'schema_version': 1,
            'name': 'project',
            'rule_fragments': ['rules/time.mdc'],
            'templates': {'program-spec.md': {'replace_tokens': {'{{term}}': 'PROJECT'}, 'append_sections': {'## 본문': 'Project section'}}},
            'skills': {'work/references/program.md': {'append_sections': {'## Quality Check': 'Project QC'}}}
        }, ensure_ascii=False), encoding='utf-8')
        (self.root / 'sdlc/custom/domain/time/overlay.json').write_text(json.dumps({
            'schema_version': 1,
            'name': 'time',
            'templates': {'program-spec.md': {'replace_tokens': {'PROJECT': 'DOMAIN'}, 'append_sections': {'## 본문': 'Domain section'}}}
        }, ensure_ascii=False), encoding='utf-8')
        (self.root / 'sdlc/config/overlay-resolution.example.json').write_text(json.dumps({
            'schema_version': 1,
            'project_overlay': 'sdlc/custom/project/overlay.json',
            'domain_overlays': ['sdlc/custom/domain/time/overlay.json']
        }), encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def materialize(self):
        return mod.materialize(self.root, self.root/'sdlc/config/overlay-resolution.example.json', self.root/'sdlc/runtime/effective')

    def test_project_then_domain_precedence(self):
        self.materialize()
        text = (self.root/'sdlc/runtime/effective/templates/program-spec.md').read_text(encoding='utf-8')
        self.assertIn('Core body DOMAIN', text)
        self.assertLess(text.index('Project section'), text.index('Domain section'))

    def test_skill_section_append_preserves_core(self):
        self.materialize()
        text = (self.root/'sdlc/runtime/effective/skills/work/references/program.md').read_text(encoding='utf-8')
        self.assertIn('Core QC', text)
        self.assertIn('Project QC', text)

    def test_rule_fragment_materialized_without_mutating_core(self):
        self.materialize()
        rules = list((self.root/'sdlc/runtime/effective/rules').glob('*time.mdc'))
        self.assertEqual(1, len(rules))
        self.assertEqual('CORE\n', (self.root/'sdlc/runtime/effective/rules/00-core.mdc').read_text(encoding='utf-8'))

    def test_manifest_records_provenance(self):
        manifest = self.materialize()
        self.assertEqual(['core', 'project_overlay', 'domain_overlay'], manifest['resolution_order'])
        self.assertTrue(manifest['applied_files'])

    def test_missing_section_fails_closed(self):
        overlay = json.loads((self.root/'sdlc/custom/project/overlay.json').read_text(encoding='utf-8'))
        overlay['templates']['program-spec.md']['append_sections'] = {'## 없는절': 'bad'}
        (self.root/'sdlc/custom/project/overlay.json').write_text(json.dumps(overlay, ensure_ascii=False), encoding='utf-8')
        with self.assertRaises(ValueError):
            self.materialize()

    def test_path_traversal_is_rejected(self):
        overlay = json.loads((self.root/'sdlc/custom/project/overlay.json').read_text(encoding='utf-8'))
        overlay['templates']['../secret.md'] = {'replace_tokens': {'x': 'y'}}
        (self.root/'sdlc/custom/project/overlay.json').write_text(json.dumps(overlay), encoding='utf-8')
        with self.assertRaises(ValueError):
            self.materialize()


if __name__ == '__main__':
    unittest.main()
