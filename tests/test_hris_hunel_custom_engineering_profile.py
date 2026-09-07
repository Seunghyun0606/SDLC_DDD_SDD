import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


class HrisHunelCustomEngineeringProfileTest(unittest.TestCase):
    def test_custom_profile_and_templates_exist(self):
        profile = ROOT / "sdlc/custom/project/tailoring/CUSTOM_HRIS_HUNEL_ENGINEERING.yaml"
        business = ROOT / "sdlc/custom/project/templates/hris-hunel/01_업무정의서.md"
        work = ROOT / "sdlc/custom/project/templates/hris-hunel/02_작업지시서.md"
        self.assertTrue(profile.is_file())
        self.assertTrue(business.is_file())
        self.assertTrue(work.is_file())
        text = profile.read_text(encoding="utf-8")
        self.assertIn('profile_id: CUSTOM_HRIS_HUNEL_ENGINEERING', text)
        self.assertIn('01_업무정의서.md', text)
        self.assertIn('02_작업지시서.md', text)
        self.assertIn('manual_edit_policy: HUMAN_REVIEW', text)

    def test_project_example_selects_engineering_profile_only(self):
        text = (ROOT / "sdlc/custom/project/config/project.hris-hunel.example.yaml").read_text(encoding="utf-8")
        self.assertIn('engineering:', text)
        self.assertIn('profile: "CUSTOM_HRIS_HUNEL_ENGINEERING"', text)
        self.assertNotIn('template_set:', text)
        self.assertNotIn('internal:\n    profile: "CUSTOM_HRIS_HUNEL_ENGINEERING"', text)

    def test_standard_engineering_is_technology_neutral(self):
        standard = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in [
                "sdlc/templates/engineering/standard/00_work-map.md",
                "sdlc/templates/engineering/standard/work-unit-sdd.md",
                "sdlc/templates/engineering/standard/program-spec.md",
            ]
        )
        for term in ["hunelCommonDS", "CUDSQLManager", "chkAuthMenu", "ibsheet", "SQLResource"]:
            self.assertNotIn(term, standard)
        self.assertIn("Work Unit", standard)
        self.assertIn("Coverage Gap", standard)
        self.assertIn("SOURCE_BLOCK", standard)
        self.assertIn("조건부 구현 블록", standard)
        self.assertIn("Source Change Boundary", standard)

    def test_hunel_specifics_are_confined_to_custom_work_instruction(self):
        text = (ROOT / "sdlc/custom/project/templates/hris-hunel/02_작업지시서.md").read_text(encoding="utf-8")
        for term in ["hunel", "ibsheet", "doAction", "chkAuthMenu", "CUDSQLManager", "SQLResource"]:
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
