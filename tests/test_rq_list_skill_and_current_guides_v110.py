from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RqListSkillAndCurrentGuidesV110Test(unittest.TestCase):
    def read(self, rel: str) -> str:
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_rq_list_core_skill_exists_and_keeps_pm_outside_business_truth(self):
        rel = "sdlc/agent/skills/rq-list/SKILL.md"
        self.assertTrue((ROOT / rel).is_file())
        text = self.read(rel)
        for marker in [
            "python sdlc/scripts/harness.py rq-list",
            "rq-list export",
            "rq-list import",
            "rq-list assign",
            "업무 기준 정보를 변경하지 않는다",
            "harness.py rq-add",
            "harness.py intake",
            "Excel/CSV",
        ]:
            self.assertIn(marker, text, marker)
        self.assertIn("한두 건", text)
        self.assertIn("대량", text)

    def test_cursor_rq_list_adapter_points_to_core_skill(self):
        rel = ".cursor/skills/rq-list/SKILL.md"
        self.assertTrue((ROOT / rel).is_file())
        text = self.read(rel)
        self.assertIn("@sdlc/agent/skills/rq-list/SKILL.md", text)
        self.assertIn("/rq-list", text)
        self.assertIn("python sdlc/scripts/harness.py rq-list", text)

    def test_customer_view_core_skill_is_lifecycle_first_and_profile_driven(self):
        rel = "sdlc/agent/skills/customer-view/SKILL.md"
        self.assertTrue((ROOT / rel).is_file())
        text = self.read(rel)
        for marker in [
            "python sdlc/scripts/harness.py customer-view",
            "python sdlc/scripts/harness.py projection status",
            "Customer Profile의 `artifacts`",
            "1/3/5/8/13/N종",
            "FINAL_REVIEW",
            "MANUAL_EDIT_DETECTED",
            "자동 덮어쓰기 금지",
            "Source/DB/Program 현행을 다시 조사해야 함 → `/work`",
            "Requirement/Business Rule/Scope/TO-BE 변경 → `/change`",
        ]:
            self.assertIn(marker, text, marker)

    def test_customer_view_skill_requires_plain_customer_sentences_and_glossary(self):
        skill = self.read("sdlc/agent/skills/customer-view/SKILL.md")
        for marker in [
            "br-input/glossary.csv",
            "고객 문장 작성 단계 — 필수",
            "누가 / 어떤 조건에서 / 무엇을 하고 / 결과가 무엇인지",
            "그 파일을 그대로 완료 결과로 제시하지 않는다",
            "Java Class/Method",
            "Table/Column",
            "알 수 없으면 추측하지 않는다",
            "projection generated",
            "고객문서 hash/lifecycle을 갱신할 뿐",
        ]:
            self.assertIn(marker, skill, marker)

    def test_cursor_customer_view_adapter_points_to_core_skill(self):
        rel = ".cursor/skills/customer-view/SKILL.md"
        self.assertTrue((ROOT / rel).is_file())
        text = self.read(rel)
        self.assertIn("@sdlc/agent/skills/customer-view/SKILL.md", text)
        self.assertIn("/customer-view", text)
        self.assertIn("projection status --target <RQ>", text)
        self.assertIn("customer-view --target <RQ> --type <customer-artifact-id>", text)
        self.assertIn("br-input/glossary.csv", text)
        self.assertIn("고객 관점의 짧고 자연스러운 한국어 문장", text)
        self.assertIn("projection generated", text)

    def test_project_scaffold_distributes_pm_customer_and_current_guides(self):
        contract = json.loads(self.read("sdlc/design/contracts/project-scaffold-contract.json"))
        required = set(contract["add_required_files"])
        for rel in [
            "sdlc/agent/skills/rq-list/SKILL.md",
            ".cursor/skills/rq-list/SKILL.md",
            "sdlc/agent/skills/customer-view/SKILL.md",
            ".cursor/skills/customer-view/SKILL.md",
            "docs/00_시작/14_한글_인코딩_및_외부명령_가이드.md",
            "docs/00_시작/15_고객문서_미리보기_가이드.md",
            "docs/00_시작/18_HARNESS_CLI_기능_참조가이드.md",
        ]:
            self.assertIn(rel, required, rel)
            self.assertTrue((ROOT / rel).is_file(), rel)
        self.assertIn(
            "Customer Projection runtime, continuous customer-view skill and customer document guide",
            contract["distribution_boundary"]["PROJECT_REQUIRED"],
        )

    def test_start_here_exposes_customer_preview_refresh_without_machine_states(self):
        start = self.read("docs/00_시작/START_HERE.md")
        for marker in [
            "customer-view --target RQ-001 --type solution_agreement",
            "customer-view --target RQ-001 --type delivery_scope",
            "customer-view --target RQ-001 --type acceptance_handover",
            "/customer-view refresh RQ-001",
            "14_한글_인코딩_및_외부명령_가이드.md",
            "15_고객문서_미리보기_가이드.md",
            "18_HARNESS_CLI_기능_참조가이드.md",
        ]:
            self.assertIn(marker, start, marker)
        for machine_term in ["FINAL_REVIEW", "MANUAL_EDIT_DETECTED"]:
            self.assertNotIn(machine_term, start)

    def test_customer_preview_guide_matches_customer_standard_3_and_continuous_refresh_policy(self):
        guide = self.read("docs/00_시작/15_고객문서_미리보기_가이드.md")
        profile = self.read("sdlc/tailoring/standard/CUSTOMER_STANDARD_3.yaml")
        for artifact_id in ["solution_agreement", "delivery_scope", "acceptance_handover"]:
            self.assertIn(artifact_id, guide)
            self.assertIn(artifact_id + ":", profile)
        for marker in [
            "/customer-view refresh RQ-001",
            "/customer-view status RQ-001",
            "projection status --target RQ-001",
            "Project Custom Profile",
            "자동 덮어쓰기 금지",
            "br-input/glossary.csv",
            "고객이 읽기 쉬운 한국어",
            "Java Method/Table/Query",
        ]:
            self.assertIn(marker, guide, marker)
        for machine_term in ["FINAL_REVIEW", "MANUAL_EDIT_DETECTED"]:
            self.assertNotIn(machine_term, guide)
        self.assertIn("docs/20_고객/{target}", profile)
        self.assertIn("docs/20_고객/RQ-001", guide)

    def test_project_glossary_location_matches_input_guide_and_template(self):
        guide = self.read("docs/00_시작/11_INPUT_자료_준비가이드.md")
        glossary = self.read("sdlc/templates/br-intake/glossary.example.csv")
        self.assertIn("br-input/glossary.csv", guide)
        self.assertIn("프로젝트/고객 용어집", guide)
        self.assertTrue(glossary.startswith("term,meaning,alias_or_abbreviation,scope,note"))

    def test_encoding_guide_matches_lossless_process_policy(self):
        guide = self.read("docs/00_시작/14_한글_인코딩_및_외부명령_가이드.md")
        process_contract = json.loads(self.read("sdlc/design/contracts/process-execution-contract.json"))
        doc_contract = json.loads(self.read("sdlc/design/contracts/br-document-extraction-contract.json"))
        for marker in ["CP949", "UTF-16", "CMD", "PowerShell", "stdout/stderr", "errors=\"replace\""]:
            self.assertIn(marker, guide, marker)
        self.assertEqual("BYTES_FIRST", process_contract["capture_policy"]["capture_mode"])
        self.assertTrue(process_contract["capture_policy"]["text_true_for_captured_output_forbidden"])
        text_encoding = doc_contract["text_encoding_contract"]
        self.assertEqual("LOSSLESS_STRICT_ONLY", text_encoding["decode_policy"])
        self.assertTrue(text_encoding["replacement_decode_for_evidence_forbidden"])


if __name__ == "__main__":
    unittest.main()
