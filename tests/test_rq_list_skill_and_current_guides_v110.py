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
            "새 요구사항은 먼저 `harness.py intake`",
            "Excel/CSV",
        ]:
            self.assertIn(marker, text, marker)

    def test_cursor_rq_list_adapter_points_to_core_skill(self):
        rel = ".cursor/skills/rq-list/SKILL.md"
        self.assertTrue((ROOT / rel).is_file())
        text = self.read(rel)
        self.assertIn("@sdlc/agent/skills/rq-list/SKILL.md", text)
        self.assertIn("/rq-list", text)
        self.assertIn("python sdlc/scripts/harness.py rq-list", text)

    def test_project_scaffold_distributes_rq_list_skill_and_new_guides(self):
        contract = json.loads(self.read("sdlc/design/contracts/project-scaffold-contract.json"))
        required = set(contract["add_required_files"])
        for rel in [
            "sdlc/agent/skills/rq-list/SKILL.md",
            ".cursor/skills/rq-list/SKILL.md",
            "docs/00_시작/14_한글_인코딩_및_외부명령_가이드.md",
            "docs/00_시작/15_고객문서_미리보기_가이드.md",
        ]:
            self.assertIn(rel, required, rel)
            self.assertTrue((ROOT / rel).is_file(), rel)

    def test_start_here_exposes_customer_preview_and_current_guides(self):
        start = self.read("docs/00_시작/START_HERE.md")
        for marker in [
            "customer-view --target RQ-001 --type solution_agreement",
            "customer-view --target RQ-001 --type delivery_scope",
            "customer-view --target RQ-001 --type acceptance_handover",
            "14_한글_인코딩_및_외부명령_가이드.md",
            "15_고객문서_미리보기_가이드.md",
            "sdlc/agent/skills/rq-list/SKILL.md",
        ]:
            self.assertIn(marker, start, marker)

    def test_customer_preview_guide_matches_customer_standard_3_profile(self):
        guide = self.read("docs/00_시작/15_고객문서_미리보기_가이드.md")
        profile = self.read("sdlc/tailoring/standard/CUSTOMER_STANDARD_3.yaml")
        for artifact_id in ["solution_agreement", "delivery_scope", "acceptance_handover"]:
            self.assertIn(artifact_id, guide)
            self.assertIn(artifact_id + ":", profile)
        self.assertIn("docs/20_고객/{target}", profile)
        self.assertIn("docs/20_고객/RQ-001", guide)

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
