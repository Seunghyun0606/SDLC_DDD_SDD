import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
TEXT_SUFFIXES = {'.py', '.json', '.yaml', '.yml', '.md', '.mdc', '.txt', '.toml', '.ini', '.cfg', '.xml'}
FORBIDDEN_TEMPLATE_TERMS = (
    'sdlc/templates/core',
    'templates_core_is_compatibility_alias',
    'core -> semantic alias',
    'symlink compatibility alias',
)


class TemplateRoleBoundaryV110Test(unittest.TestCase):
    def test_semantic_templates_are_the_only_stage_template_root(self):
        semantic = ROOT / 'sdlc/templates/semantic'
        old_core = ROOT / 'sdlc/templates/core'
        self.assertTrue(semantic.is_dir())
        self.assertFalse(old_core.exists())
        semantic_files = sorted(p.name for p in semantic.glob('*.md'))
        self.assertGreaterEqual(len(semantic_files), 10)

    def test_repository_has_no_old_template_core_terminology(self):
        hits = []
        for path in ROOT.rglob('*'):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            rel = path.relative_to(ROOT).as_posix()
            if rel == 'tests/test_template_role_boundary_v110.py':
                continue
            text = path.read_text(encoding='utf-8', errors='ignore')
            for term in FORBIDDEN_TEMPLATE_TERMS:
                if term in text:
                    hits.append(f'{rel}: {term}')
        self.assertEqual([], hits, '\n'.join(hits))

    def test_run_work_uses_semantic_only(self):
        text = (ROOT / 'sdlc/scripts/run_work.py').read_text(encoding='utf-8')
        self.assertIn('sdlc/templates/semantic', text)
        self.assertNotIn('sdlc/templates/core', text)

    def test_framework_validators_use_semantic_root(self):
        document_check = (ROOT / 'sdlc/scripts/validate_document_experience.py').read_text(encoding='utf-8')
        structure_check = (ROOT / 'sdlc/scripts/validate_harness_structure.py').read_text(encoding='utf-8')
        self.assertIn('sdlc/templates/semantic', document_check)
        self.assertIn('sdlc/templates/semantic', structure_check)
        self.assertNotIn('sdlc/templates/core', document_check + structure_check)

    def test_active_projection_profiles_do_not_use_semantic_as_final_document_template(self):
        engineering = (ROOT / 'sdlc/tailoring/standard/ENGINEERING_SDD_COMPACT.yaml').read_text(encoding='utf-8')
        customer3 = (ROOT / 'sdlc/tailoring/standard/CUSTOMER_STANDARD_3.yaml').read_text(encoding='utf-8')
        customer_full = (ROOT / 'sdlc/tailoring/standard/CUSTOMER_WATERFALL_FULL.yaml').read_text(encoding='utf-8')
        self.assertIn('sdlc/templates/engineering/standard/', engineering)
        self.assertNotIn('sdlc/templates/semantic/', engineering)
        self.assertIn('sdlc/templates/customer/standard/', customer3)
        self.assertIn('sdlc/templates/customer/standard/', customer_full)
        self.assertNotIn('sdlc/templates/semantic/', customer3 + customer_full)

    def test_legacy_profiles_are_explicit_projection_profiles(self):
        standard3 = (ROOT / 'sdlc/tailoring/standard/STANDARD_3.yaml').read_text(encoding='utf-8')
        standard5 = (ROOT / 'sdlc/tailoring/standard/STANDARD_5.yaml').read_text(encoding='utf-8')
        stage_full = (ROOT / 'sdlc/tailoring/standard/STAGE_ORIENTED_FULL.yaml').read_text(encoding='utf-8')
        self.assertIn('sdlc/templates/tailoring/standard/', standard3 + standard5)
        self.assertIn('sdlc/templates/semantic/', stage_full)

    def test_template_readme_explains_roles_without_alias_language(self):
        text = (ROOT / 'sdlc/templates/README.md').read_text(encoding='utf-8')
        for marker in ['semantic/', 'engineering/', 'customer/', 'tailoring/standard/']:
            self.assertIn(marker, text)
        self.assertNotIn('sdlc/templates/core', text)
        self.assertNotIn('symlink compatibility alias', text)


if __name__ == '__main__':
    unittest.main()
