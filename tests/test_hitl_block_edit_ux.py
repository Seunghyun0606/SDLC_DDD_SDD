import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


class HitlBlockEditUxTest(unittest.TestCase):
    def test_hitl_reference_exists_and_defines_agent_first_questions(self):
        path = ROOT / "sdlc/agent/skills/work/references/hitl.md"
        self.assertTrue(path.is_file())
        text = path.read_text(encoding="utf-8")
        for marker in [
            "문서는 **입력 Form이 아니라 Review Surface**",
            "기술적으로 조사할 수 있는 질문을 사람에게 떠넘기지 않는다",
            "SEMANTIC_CHANGE",
            "EVIDENCE_REFRESH",
            "PROJECTION_ONLY",
            "HITL-<TARGET>-<NN>",
        ]:
            self.assertIn(marker, text)

    def test_work_and_change_core_skills_use_hitl_reference(self):
        work = read("sdlc/agent/skills/work/SKILL.md")
        change = read("sdlc/agent/skills/change/SKILL.md")
        for text in [work, change]:
            self.assertIn("sdlc/agent/skills/work/references/hitl.md", text)
            self.assertIn("Canonical Delta", text)
            self.assertIn("PROJECTION_ONLY", text)
        self.assertIn("사람에게 Template을 작성시키지 않는다", work)
        self.assertIn("Template 전체를 사용자에게 작성시키지 않는다", change)

    def test_cursor_adapters_expose_same_hitl_ux(self):
        work = read(".cursor/skills/work/SKILL.md")
        change = read(".cursor/skills/change/SKILL.md")
        for text in [work, change]:
            self.assertIn("references/hitl.md", text)
            self.assertIn("[BLOCK:", text)
            self.assertIn("Canonical", text)

    def test_standard_engineering_templates_have_stable_block_ids(self):
        work_map = read("sdlc/templates/engineering/standard/00_work-map.md")
        work_unit = read("sdlc/templates/engineering/standard/work-unit-sdd.md")
        program = read("sdlc/templates/engineering/standard/program-spec.md")

        for marker in ["BLOCK_ID: WM-SUMMARY", "BLOCK_ID: WM-MAPPING", "BLOCK_ID: WM-OPEN"]:
            self.assertIn(marker, work_map)
        for marker in ["BLOCK_ID: WU-INTENT", "BLOCK_ID: WU-BUSINESS-RULE", "BLOCK_ID: WU-OPEN-GUARD"]:
            self.assertIn(marker, work_unit)
        for marker in ["BLOCK_ID: PGM-TARGET", "BLOCK_ID: PGM-SOURCE-EVIDENCE", "BLOCK_ID: PGM-READINESS"]:
            self.assertIn(marker, program)

        for text in [work_map, work_unit, program]:
            self.assertIn("빈칸을", text)
            self.assertIn("Agent", text)

    def test_hris_custom_templates_define_review_blocks(self):
        business = read("sdlc/custom/project/templates/hris-hunel/01_업무정의서.md")
        instruction = read("sdlc/custom/project/templates/hris-hunel/02_작업지시서.md")

        for marker in [
            "BLOCK_ID: HRIS-INTENT",
            "BLOCK_ID: HRIS-BUSINESS-RULE",
            "BLOCK_ID: HRIS-DATA-AUTH",
            "BLOCK_ID: HRIS-OPEN",
        ]:
            self.assertIn(marker, business)

        for marker in ["[BLOCK:B-PROC]", "[BLOCK:D.1]", "B-AUTH", "B-MIGRATION"]:
            self.assertIn(marker, instruction)

        self.assertIn("빈칸을 직접 채우지 않습니다", business)
        self.assertIn("표/빈칸을 직접 작성하지 않습니다", instruction)

    def test_user_guides_explain_block_round_trip_to_canonical(self):
        template_guide = read("docs/00_시작/04_TEMPLATE_및_산출물_가이드.md")
        stakeholder_guide = read("docs/00_시작/05_이해관계자별_작업가이드.md")
        for text in [template_guide, stakeholder_guide]:
            self.assertIn("[BLOCK:", text)
            self.assertIn("Canonical", text)
            self.assertIn("/change", text)
            self.assertIn("/work", text)
        self.assertIn("Template은 입력 Form이 아니다", template_guide)
        self.assertIn("Reviewer / Decision Maker", template_guide)
        self.assertIn("Template 빈칸을 직접 작성하는 사람이 아니다", stakeholder_guide)


if __name__ == "__main__":
    unittest.main()
