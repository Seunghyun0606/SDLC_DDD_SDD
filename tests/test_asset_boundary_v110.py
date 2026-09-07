import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "sdlc/scripts/build_project_scaffold.py"

spec = importlib.util.spec_from_file_location("asset_boundary_scaffold", SCRIPT)
SCAFFOLD = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = SCAFFOLD
spec.loader.exec_module(SCAFFOLD)


class AssetBoundaryV110Test(unittest.TestCase):
    def test_framework_samples_and_duplicate_guides_are_not_active_project_paths(self):
        self.assertTrue((ROOT / "framework/samples/tailoring/README.md").is_file())
        self.assertTrue((ROOT / "framework/ASSET_INVENTORY_V110.md").is_file())
        self.assertFalse((ROOT / "sdlc/samples/tailoring").exists())
        self.assertFalse((ROOT / "sdlc/guides").exists())
        self.assertFalse((ROOT / "sdlc/design/config-usage-inventory.json").exists())
        self.assertTrue((ROOT / "framework/archive/config-usage-inventory-v19.json").is_file())

    def test_default_scaffold_excludes_framework_and_legacy_assets(self):
        selected = SCAFFOLD.select_files(ROOT)
        self.assertIn("sdlc/tailoring/standard/ENGINEERING_SDD_COMPACT.yaml", selected)
        self.assertIn("sdlc/tailoring/standard/CUSTOMER_STANDARD_3.yaml", selected)
        self.assertIn("sdlc/templates/semantic/requirement.md", selected)
        self.assertIn("sdlc/templates/semantic/program-spec.md", selected)
        self.assertIn("sdlc/templates/README.md", selected)
        self.assertFalse(any(path.startswith("sdlc/templates/core/") for path in selected))
        self.assertNotIn("sdlc/tailoring/standard/STANDARD_3.yaml", selected)
        self.assertNotIn("sdlc/tailoring/standard/STANDARD_5.yaml", selected)
        self.assertNotIn("sdlc/tailoring/standard/STAGE_ORIENTED_FULL.yaml", selected)
        self.assertFalse(any(path.startswith("sdlc/templates/tailoring/standard/") for path in selected))
        self.assertFalse(any(path.startswith("framework/") for path in selected))
        self.assertFalse(any(path.startswith("tests/") for path in selected))
        self.assertFalse(any(path.startswith("docs/99_파일럿/") for path in selected))
        self.assertNotIn("sdlc/scripts/build_project_scaffold.py", selected)
        self.assertNotIn("sdlc/design/contracts/project-scaffold-contract.json", selected)

    def test_legacy_compatibility_is_complete_and_explicit(self):
        selected = SCAFFOLD.select_files(ROOT, include_legacy_compatibility=True)
        for rel in [
            "sdlc/tailoring/standard/STANDARD_3.yaml",
            "sdlc/tailoring/standard/STANDARD_5.yaml",
            "sdlc/tailoring/standard/STAGE_ORIENTED_FULL.yaml",
            "sdlc/templates/tailoring/standard/01_업무정의서.md",
            "sdlc/templates/tailoring/standard/15_테스트인수결과서.md",
        ]:
            self.assertIn(rel, selected)

    def test_materialized_project_has_no_framework_distribution_tooling(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "project"
            result = SCAFFOLD.build(ROOT, output)
            self.assertEqual("PROJECT_SCAFFOLD_BUILT", result["status"])
            self.assertEqual("ENGINEERING_SDD_COMPACT", result["default_engineering_profile"])
            self.assertFalse(result["forbidden_framework_dev_assets_present"])
            self.assertTrue((output / "sdlc/templates/semantic/requirement.md").is_file())
            self.assertTrue((output / "sdlc/templates/semantic/program-spec.md").is_file())
            self.assertTrue((output / "sdlc/templates/core").exists())
            self.assertEqual(
                (output / "sdlc/templates/semantic").resolve(),
                (output / "sdlc/templates/core").resolve(),
            )
            self.assertEqual("sdlc/templates/core", result["compatibility_aliases"][0]["path"])
            self.assertFalse((output / "framework").exists())
            self.assertFalse((output / "tests").exists())
            self.assertFalse((output / "sdlc/scripts/build_project_scaffold.py").exists())
            self.assertFalse((output / "sdlc/design/contracts/project-scaffold-contract.json").exists())
            self.assertFalse((output / "sdlc/tailoring/standard/STANDARD_5.yaml").exists())


if __name__ == "__main__":
    unittest.main()
