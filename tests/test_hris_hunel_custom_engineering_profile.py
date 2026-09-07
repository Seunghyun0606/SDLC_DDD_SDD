import re
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


def visible_text(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


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

    def test_standard_engineering_is_technology_neutral_and_humanized(self):
        standard = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in [
                "sdlc/templates/engineering/standard/00_work-map.md",
                "sdlc/templates/engineering/standard/work-unit-sdd.md",
                "sdlc/templates/engineering/standard/program-spec.md",
            ]
        )
        text = visible_text(standard)
        for term in ["hunelCommonDS", "CUDSQLManager", "chkAuthMenu", "ibsheet", "SQLResource"]:
            self.assertNotIn(term, text)
        for term in [
            "업무·기능 단위",
            "현재 확인된 동작과 근거",
            "업무 규칙 / 결정사항",
            "개발 지침",
            "프로그램 상세설계",
            "현재 소스 확인",
            "소스 변경 범위",
            "구현 준비도 / 확인 필요사항",
        ]:
            self.assertIn(term, text)
        for machine_term in ["SOURCE_BLOCK", "ITERATE", "ALERT", "Recheck At", "Human Decision Queue"]:
            self.assertNotIn(machine_term, text)

    def test_hunel_business_definition_is_humanized(self):
        raw = (ROOT / "sdlc/custom/project/templates/hris-hunel/01_업무정의서.md").read_text(encoding="utf-8")
        text = visible_text(raw)
        for term in [
            "목적과 업무 / 기능 경계",
            "현재 시스템 확인 / 미확인 영역",
            "업무 규칙 / 상태",
            "인수 기준",
            "결정사항 / 확인 필요사항",
            "개발 인계",
        ]:
            self.assertIn(term, text)
        for machine_term in [
            "Canonical",
            "Stage Semantic",
            "Business Truth",
            "CONFIRMED / OPEN",
            "OBSERVED / CONFIRMED",
            "SOURCE_BLOCK",
            "ITERATE",
            "ALERT",
            "Recheck At",
        ]:
            self.assertNotIn(machine_term, text)

    def test_hunel_specifics_stay_in_custom_work_instruction(self):
        raw = (ROOT / "sdlc/custom/project/templates/hris-hunel/02_작업지시서.md").read_text(encoding="utf-8")
        text = visible_text(raw)
        for term in [
            "hunel",
            "ibsheet",
            "doAction",
            "chkAuthMenu",
            "chkAuthTrans",
            "CUDSQLManager",
            "SQLResource",
            "Procedure",
            "Java Method",
            "XML Query",
            "소스 변경 범위",
            "구현 준비도",
            "직접 수정",
            "개발 전 확인 필요",
        ]:
            self.assertIn(term, text)
        for machine_term in [
            "Canonical",
            "SOURCE_BLOCK",
            "ITERATE",
            "ALERT",
            "DIRECT_MODIFY",
            "SCRIPT_OUTPUT",
            "HUMAN_OPERATION",
            "EXECUTION_GUARDED",
            "Recheck At",
        ]:
            self.assertNotIn(machine_term, text)


if __name__ == "__main__":
    unittest.main()
