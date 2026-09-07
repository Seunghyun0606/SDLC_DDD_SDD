from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUIDE_ROOT = ROOT / "docs" / "00_시작"


class GuideConsistencyV110Test(unittest.TestCase):
    def read(self, rel: str) -> str:
        return (ROOT / rel).read_text(encoding="utf-8")

    def json(self, rel: str) -> dict:
        return json.loads(self.read(rel))

    def test_start_here_links_current_active_guides(self):
        start = self.read("docs/00_시작/START_HERE.md")
        for name in [
            "11_INPUT_자료_준비가이드.md",
            "02_PROJECT_설정가이드.md",
            "03_TAILORING_설정가이드.md",
            "04_TEMPLATE_및_산출물_가이드.md",
            "05_이해관계자별_작업가이드.md",
            "07_BROWNFIELD_SSOT_현행화가이드.md",
        ]:
            self.assertIn(name, start, name)
            self.assertTrue((GUIDE_ROOT / name).is_file(), name)

    def test_active_guides_use_current_template_and_projection_terminology(self):
        active = [
            "START_HERE.md",
            "02_PROJECT_설정가이드.md",
            "03_TAILORING_설정가이드.md",
            "04_TEMPLATE_및_산출물_가이드.md",
            "05_이해관계자별_작업가이드.md",
            "07_BROWNFIELD_SSOT_현행화가이드.md",
            "11_INPUT_자료_준비가이드.md",
        ]
        removed_stage_template_path = "sdlc/templates/" + "core"
        for name in active:
            text = (GUIDE_ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn(removed_stage_template_path, text, name)
            self.assertNotIn("sdlc/guides/", text, name)

        stakeholder = (GUIDE_ROOT / "05_이해관계자별_작업가이드.md").read_text(encoding="utf-8")
        self.assertIn("engineering:", stakeholder)
        self.assertIn("ENGINEERING_SDD_COMPACT", stakeholder)
        self.assertIn("Engineering Projection", stakeholder)
        self.assertNotIn("documents:\n  internal:", stakeholder)
        self.assertNotIn("BA/설계/개발 → INTERNAL_IT", stakeholder)

    def test_start_here_does_not_tell_distributed_project_to_self_scaffold(self):
        start = self.read("docs/00_시작/START_HERE.md")
        scaffold = self.json("sdlc/design/contracts/project-scaffold-contract.json")
        self.assertIn("Framework Repository에서만", start)
        self.assertIn("생성된 Project Scaffold 안에는 포함되지 않는다", start)
        self.assertIn("sdlc/scripts/build_project_scaffold.py", scaffold["framework_distribution_tools"])
        self.assertIn("sdlc/design/contracts/project-scaffold-contract.json", scaffold["framework_distribution_tools"])

    def test_brownfield_guide_labels_reverse_tools_as_extension(self):
        guide = self.read("docs/00_시작/07_BROWNFIELD_SSOT_현행화가이드.md")
        package = self.json("sdlc/design/contracts/harness-package-contract.json")
        self.assertIn("Brownfield Extension", guide)
        self.assertIn("기본 Minimum Executable Core가 아니라", guide)
        for rel in [
            "sdlc/scripts/build_reverse_inputs.py",
            "sdlc/scripts/detect_source_drift.py",
            "sdlc/scripts/run_source_reverse_check.py",
            "sdlc/scripts/generate_program_spec_reverse_candidate.py",
        ]:
            self.assertIn(rel, package["deployment_sets"]["BROWNFIELD_EXTENSION"])
            self.assertIn(rel, guide)

    def test_compatibility_notice_guides_are_not_distributed(self):
        scaffold = self.json("sdlc/design/contracts/project-scaffold-contract.json")
        for rel in [
            "docs/00_시작/01_STANDARD_SCAFFOLD_사용가이드.md",
            "docs/00_시작/06_CUSTOM_SCAFFOLD_적용가이드.md",
        ]:
            self.assertIn(rel, scaffold["exclude_exact"])
        start = self.read("docs/00_시작/START_HERE.md")
        self.assertIn("Compatibility Notice", start)
        self.assertIn("신규 Project Scaffold에는 배포되지 않는다", start)

    def test_template_guide_explains_semantic_vs_projection_vs_profile(self):
        guide = self.read("docs/00_시작/04_TEMPLATE_및_산출물_가이드.md")
        for marker in [
            "sdlc/templates/semantic/",
            "sdlc/templates/engineering/",
            "sdlc/templates/customer/",
            "sdlc/templates/tailoring/standard/",
            "sdlc/tailoring/standard/*.yaml",
        ]:
            self.assertIn(marker, guide, marker)


if __name__ == "__main__":
    unittest.main()
