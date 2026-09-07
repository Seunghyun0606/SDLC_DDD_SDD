import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class TemplateRoleBoundaryV110Test(unittest.TestCase):
    def test_semantic_templates_are_primary_and_core_is_alias_only(self):
        semantic = ROOT / "sdlc/templates/semantic"
        core = ROOT / "sdlc/templates/core"
        self.assertTrue(semantic.is_dir())
        self.assertTrue(core.is_symlink())
        self.assertEqual(semantic.resolve(), core.resolve())
        semantic_files = sorted(p.name for p in semantic.glob("*.md"))
        self.assertGreaterEqual(len(semantic_files), 10)
        self.assertEqual(semantic_files, sorted(p.name for p in core.glob("*.md")))

    def test_run_work_prefers_semantic_but_keeps_core_fallback(self):
        text = (ROOT / "sdlc/scripts/run_work.py").read_text(encoding="utf-8")
        self.assertIn('semantic_root = "sdlc/templates/semantic"', text)
        self.assertIn('else "sdlc/templates/core"', text)
        self.assertIn('template = f"{semantic_root}/', text)

    def test_framework_validators_use_semantic_root(self):
        document_check = (ROOT / "sdlc/scripts/validate_document_experience.py").read_text(encoding="utf-8")
        structure_check = (ROOT / "sdlc/scripts/validate_harness_structure.py").read_text(encoding="utf-8")
        self.assertIn("sdlc/templates/semantic", document_check)
        self.assertIn("sdlc/templates/semantic", structure_check)
        self.assertNotIn("root/'sdlc/templates/core'", document_check)
        self.assertNotIn("root/'sdlc/templates/core'", structure_check)

    def test_active_projection_profiles_do_not_use_semantic_as_final_document_template(self):
        engineering = (ROOT / "sdlc/tailoring/standard/ENGINEERING_SDD_COMPACT.yaml").read_text(encoding="utf-8")
        customer3 = (ROOT / "sdlc/tailoring/standard/CUSTOMER_STANDARD_3.yaml").read_text(encoding="utf-8")
        customer_full = (ROOT / "sdlc/tailoring/standard/CUSTOMER_WATERFALL_FULL.yaml").read_text(encoding="utf-8")
        self.assertIn("sdlc/templates/engineering/standard/", engineering)
        self.assertNotIn("sdlc/templates/semantic/", engineering)
        self.assertIn("sdlc/templates/customer/standard/", customer3)
        self.assertIn("sdlc/templates/customer/standard/", customer_full)
        self.assertNotIn("sdlc/templates/semantic/", customer3 + customer_full)

    def test_legacy_profiles_are_explicitly_separate_from_semantic_templates(self):
        legacy = "\n".join(
            (ROOT / f"sdlc/tailoring/standard/{name}.yaml").read_text(encoding="utf-8")
            for name in ["STANDARD_3", "STANDARD_5", "STAGE_ORIENTED_FULL"]
        )
        self.assertIn("sdlc/templates/tailoring/standard/", legacy)
        self.assertNotIn("sdlc/templates/semantic/", legacy)

    def test_template_readme_explains_roles(self):
        text = (ROOT / "sdlc/templates/README.md").read_text(encoding="utf-8")
        for marker in ["semantic/", "engineering/", "customer/", "tailoring/standard/", "symlink compatibility alias"]:
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
