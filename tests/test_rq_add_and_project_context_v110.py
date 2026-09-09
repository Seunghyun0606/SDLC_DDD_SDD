from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


RQ_ADD = load_module("test_rq_add_runtime_v110", "sdlc/scripts/rq_add.py")


class RqAddAndProjectContextV110Test(unittest.TestCase):
    def read(self, rel: str) -> str:
        return (ROOT / rel).read_text(encoding="utf-8")

    def test_prompt_add_creates_candidate_and_preserves_original_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = "승인 완료된 근무계획은 일반 사용자가 수정할 수 없게 해줘."
            result = RQ_ADD.add_requirement(
                root,
                request=request,
                title="근무계획 승인 후 수정 제한",
                refresh_worklist=False,
            )
            self.assertEqual("RQ_ADDED", result["status"])
            self.assertEqual("RQ-001", result["target"])
            store = json.loads((root / "sdlc/canonical/store.json").read_text(encoding="utf-8"))
            entity = store["entities"]["RQ-001"]
            self.assertEqual("RQ", entity["entity_type"])
            self.assertEqual("CANDIDATE", entity["truth_status"])
            self.assertEqual(request, entity["fields"]["original_requirement"])
            self.assertEqual("근무계획 승인 후 수정 제한", entity["fields"]["name"])
            self.assertEqual("OPEN", entity["fields"]["business_rules"])
            self.assertEqual("GIVEN", entity["provenance"][0]["evidence_class"])

    def test_incremental_add_uses_next_rq_id_without_reintake(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = RQ_ADD.add_requirement(root, request="첫 번째 새 요구사항", refresh_worklist=False)
            second = RQ_ADD.add_requirement(root, request="두 번째 새 요구사항", refresh_worklist=False)
            self.assertEqual("RQ-001", first["target"])
            self.assertEqual("RQ-002", second["target"])
            store = json.loads((root / "sdlc/canonical/store.json").read_text(encoding="utf-8"))
            self.assertEqual(2, store["revision"])
            self.assertEqual({"RQ-001", "RQ-002"}, set(store["entities"]))

    def test_exact_direct_prompt_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            request = "퇴직자도 과거 급여명세서를 조회할 수 있어야 해."
            first = RQ_ADD.add_requirement(root, request=request, refresh_worklist=False)
            store_before = (root / "sdlc/canonical/store.json").read_bytes()
            second = RQ_ADD.add_requirement(root, request=request, title="다른 표시 제목", refresh_worklist=False)
            self.assertEqual("RQ-001", first["target"])
            self.assertEqual("RQ_ALREADY_EXISTS", second["status"])
            self.assertEqual("RQ-001", second["target"])
            self.assertEqual(store_before, (root / "sdlc/canonical/store.json").read_bytes())

    def test_duplicate_external_id_fails_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            RQ_ADD.add_requirement(
                root,
                request="첫 요구사항",
                external_id="EXT-101",
                refresh_worklist=False,
            )
            store_before = (root / "sdlc/canonical/store.json").read_bytes()
            with self.assertRaises(ValueError):
                RQ_ADD.add_requirement(
                    root,
                    request="다른 요구사항",
                    external_id="EXT-101",
                    refresh_worklist=False,
                )
            self.assertEqual(store_before, (root / "sdlc/canonical/store.json").read_bytes())

    def test_harness_exposes_rq_add(self):
        harness = self.read("sdlc/scripts/harness.py")
        self.assertIn("setup | intake | rq-add | rq-list", harness)
        self.assertIn('if command == "rq-add"', harness)
        self.assertIn('"rq_add.py"', harness)

    def test_rq_add_skill_routes_new_change_bulk_and_pm_correctly(self):
        core = self.read("sdlc/agent/skills/rq-add/SKILL.md")
        cursor = self.read(".cursor/skills/rq-add/SKILL.md")
        for marker in [
            "original_requirement",
            "CANDIDATE",
            "python sdlc/scripts/harness.py rq-add",
            "기존 `RQ-001`의 정책/범위/요구 내용을 변경 → `/change`",
            "여러 행의 요구사항 목록을 한 번에 추가 → `harness.py intake <requirements.xlsx>`",
            "PM 담당자/일정/우선순위만 변경 → `/rq-list`",
            "유사 문장 자동 병합 금지",
        ]:
            self.assertIn(marker, core, marker)
        self.assertIn("@sdlc/agent/skills/rq-add/SKILL.md", cursor)
        self.assertIn("/rq-add", cursor)

    def test_project_agent_context_is_explicit_and_context_minimized(self):
        reference = self.read("sdlc/agent/skills/work/references/project-development-context.md")
        agents = self.read("AGENTS.md")
        cursor_rule = self.read(".cursor/rules/10-project.mdc")
        for marker in [
            "sdlc/custom/project/rules/",
            "sdlc/custom/project/standards/",
            "sdlc/custom/domain/<domain>/rules/",
            "br-input/glossary.csv",
            "Standards 전체를 매번 선로딩하지 않는다",
        ]:
            self.assertIn(marker, reference, marker)
        self.assertIn("project-development-context.md", agents)
        self.assertIn("Source 수정 전에 반드시 확인", cursor_rule)
        self.assertIn("현재 Stage/기술/변경 범위와 관련된 문서만 읽는다", cursor_rule)

    def test_guides_and_scaffold_include_new_capabilities(self):
        guide = self.read("docs/00_시작/16_프로젝트_개발가이드_Agent_적용가이드.md")
        rq_guide = self.read("docs/00_시작/17_RQ_간편추가_가이드.md")
        self.assertIn("sdlc/custom/project/standards/", guide)
        self.assertIn("sdlc/custom/project/rules/", guide)
        self.assertIn("Agent가 실제로 읽는 순서", guide)
        self.assertIn("python sdlc/scripts/harness.py rq-add", rq_guide)
        self.assertIn("intake", rq_guide)
        self.assertIn("change", rq_guide)
        contract = json.loads(self.read("sdlc/design/contracts/project-scaffold-contract.json"))
        required = set(contract["add_required_files"])
        for rel in [
            "sdlc/scripts/rq_add.py",
            "sdlc/agent/skills/rq-add/SKILL.md",
            ".cursor/skills/rq-add/SKILL.md",
            "sdlc/agent/skills/work/references/project-development-context.md",
            "docs/00_시작/16_프로젝트_개발가이드_Agent_적용가이드.md",
            "docs/00_시작/17_RQ_간편추가_가이드.md",
        ]:
            self.assertIn(rel, required, rel)


if __name__ == "__main__":
    unittest.main()
