import json
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
            "Human Decision Queue",
            "DEFERRED",
            "Recheck At",
            "신규 질문보다 먼저",
        ]:
            self.assertIn(marker, text)

    def test_deferred_queue_reuses_existing_open_resolution_contract(self):
        contract = json.loads(read("sdlc/design/contracts/open-resolution-contract.json"))
        self.assertIn("DEFER", contract["resolution_methods"])
        self.assertIn("DEFERRED", contract["resolution_status"])
        self.assertEqual(contract["human_status_mapping"]["DEFERRED"], "보류")
        self.assertIn("non_blocking", contract["resolution_rules"])

        hitl = read("sdlc/agent/skills/work/references/hitl.md")
        self.assertIn("open-resolution-contract.json", hitl)
        self.assertIn("별도의 Question Store", hitl)
        self.assertIn("OPEN/DEFERRED", hitl)

    def test_work_and_change_core_skills_recheck_queue_before_new_questions(self):
        work = read("sdlc/agent/skills/work/SKILL.md")
        change = read("sdlc/agent/skills/change/SKILL.md")
        for text in [work, change]:
            self.assertIn("sdlc/agent/skills/work/references/hitl.md", text)
            self.assertIn("Canonical Delta", text)
            self.assertIn("PROJECTION_ONLY", text)
            self.assertIn("Human Decision Queue", text)
            self.assertIn("DEFERRED", text)
            self.assertIn("Recheck At", text)
            self.assertIn("신규 질문보다 먼저", text)
        self.assertIn("사람에게 Template을 작성시키지 않는다", work)
        self.assertIn("Template을 열고 빈칸을 작성해 달라", change)

    def test_cursor_adapters_expose_same_hitl_queue_ux(self):
        work = read(".cursor/skills/work/SKILL.md")
        change = read(".cursor/skills/change/SKILL.md")
        for text in [work, change]:
            self.assertIn("references/hitl.md", text)
            self.assertIn("[BLOCK:", text)
            self.assertIn("Canonical", text)
            self.assertIn("Human Decision Queue", text)
            self.assertIn("DEFERRED", text)
            self.assertIn("Recheck At", text)

    def test_standard_engineering_templates_have_stable_queue_blocks(self):
        work_map = read("sdlc/templates/engineering/standard/00_work-map.md")
        work_unit = read("sdlc/templates/engineering/standard/work-unit-sdd.md")
        program = read("sdlc/templates/engineering/standard/program-spec.md")

        for marker in [
            "BLOCK_ID: WM-SUMMARY",
            "BLOCK_ID: WM-MAPPING",
            "BLOCK_ID: WM-OPEN",
            "BLOCK_ID: WM-HITL-QUEUE",
        ]:
            self.assertIn(marker, work_map)
        for marker in [
            "BLOCK_ID: WU-INTENT",
            "BLOCK_ID: WU-BUSINESS-RULE",
            "BLOCK_ID: WU-OPEN-GUARD",
            "BLOCK_ID: WU-HITL-QUEUE",
        ]:
            self.assertIn(marker, work_unit)
        for marker in [
            "BLOCK_ID: PGM-TARGET",
            "BLOCK_ID: PGM-SOURCE-EVIDENCE",
            "BLOCK_ID: PGM-READINESS",
            "BLOCK_ID: PGM-HITL-QUEUE",
        ]:
            self.assertIn(marker, program)

        for text in [work_map, work_unit, program]:
            self.assertIn("빈칸을", text)
            self.assertIn("Agent", text)
            self.assertIn("Human Decision Queue", text)
            self.assertIn("Recheck At", text)
            self.assertIn("SOURCE_BLOCK / ITERATE / ALERT", text)

    def test_hris_custom_templates_define_queue_review_blocks(self):
        business = read("sdlc/custom/project/templates/hris-hunel/01_업무정의서.md")
        instruction = read("sdlc/custom/project/templates/hris-hunel/02_작업지시서.md")

        for marker in [
            "BLOCK_ID: HRIS-INTENT",
            "BLOCK_ID: HRIS-BUSINESS-RULE",
            "BLOCK_ID: HRIS-DATA-AUTH",
            "BLOCK_ID: HRIS-OPEN",
            "BLOCK_ID: HRIS-HITL-QUEUE",
        ]:
            self.assertIn(marker, business)

        for marker in [
            "[BLOCK:B-PROC]",
            "[BLOCK:D.1]",
            "B-AUTH",
            "B-MIGRATION",
            "BLOCK_ID: HITL-QUEUE",
        ]:
            self.assertIn(marker, instruction)

        self.assertIn("빈칸을 직접 채우지 않습니다", business)
        self.assertIn("표/빈칸을 직접 작성하지 않습니다", instruction)
        for text in [business, instruction]:
            self.assertIn("Human Decision Queue", text)
            self.assertIn("Recheck At", text)

    def test_user_guides_explain_defer_and_block_round_trip_to_canonical(self):
        template_guide = read("docs/00_시작/04_TEMPLATE_및_산출물_가이드.md")
        stakeholder_guide = read("docs/00_시작/05_이해관계자별_작업가이드.md")
        for text in [template_guide, stakeholder_guide]:
            self.assertIn("[BLOCK:", text)
            self.assertIn("Canonical", text)
            self.assertIn("/change", text)
            self.assertIn("/work", text)
            self.assertIn("Human Decision Queue", text)
            self.assertIn("Recheck At", text)
            self.assertIn("다음", text)
        self.assertIn("Template은 입력 Form이 아니다", template_guide)
        self.assertIn("Reviewer / Decision Maker", template_guide)
        self.assertIn("Template 빈칸을 직접 작성하는 사람이 아니다", stakeholder_guide)
        self.assertIn("지금 바로 답할 수 없을 때", stakeholder_guide)


if __name__ == "__main__":
    unittest.main()
