from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def load_rq_add():
    path = ROOT / "sdlc/scripts/rq_add.py"
    name = "test_rq_add_v110_runtime"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ProjectDevelopmentContextAndRqAddV110Test(unittest.TestCase):
    def test_project_development_context_is_explicit_for_agents(self):
        reference = read("sdlc/agent/skills/work/references/project-development-context.md")
        cursor_rule = read(".cursor/rules/10-project.mdc")
        agents = read("AGENTS.md")
        claude = read("CLAUDE.md")
        guide = read("docs/00_시작/16_프로젝트_개발가이드_Agent_적용가이드.md")
        for text in [reference, cursor_rule, agents, claude, guide]:
            self.assertIn("sdlc/custom/project/rules/", text)
            self.assertIn("sdlc/custom/project/standards/", text)
        self.assertIn("현재 작업에 관련된", reference)
        self.assertIn("모든 개발가이드를 매번 무조건 선로딩하지 않는다", guide)
        self.assertIn("br-input/originals/", guide)

    def test_rq_add_creates_candidate_with_base_context_and_open_defaults(self):
        mod = load_rq_add()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = mod.add_requirement(
                root,
                title="승인 전 연차신청 취소",
                request="직원이 승인되기 전에는 연차신청을 직접 취소할 수 있게 해줘.",
                background="잘못 신청하면 담당자에게 취소를 요청해야 한다.",
                desired_result="본인이 직접 취소할 수 있다.",
                scope="연차신청",
                refresh_worklist=False,
            )
            self.assertEqual("RQ_ADDED", first["status"])
            self.assertEqual("RQ-001", first["target"])
            self.assertEqual("SINGLE_WRITER_FILE_DERIVED", first["sequence_policy"])
            store = json.loads((root / "sdlc/canonical/store.json").read_text(encoding="utf-8"))
            rq = store["entities"]["RQ-001"]
            self.assertEqual("CANDIDATE", rq["truth_status"])
            self.assertEqual("연차신청", rq["fields"]["scope"])
            self.assertEqual("본인이 직접 취소할 수 있다.", rq["fields"]["desired_result"])
            self.assertEqual("PROMPT_RQ_ADD", rq["fields"]["creation_method"])

            second = mod.add_requirement(
                root,
                title="급여명세서 모바일 조회",
                request="모바일에서도 급여명세서를 조회할 수 있게 해줘.",
                refresh_worklist=False,
            )
            self.assertEqual("RQ-002", second["target"])
            store = json.loads((root / "sdlc/canonical/store.json").read_text(encoding="utf-8"))
            self.assertEqual("OPEN", store["entities"]["RQ-002"]["fields"]["current_problem"])
            self.assertEqual("OPEN", store["entities"]["RQ-002"]["fields"]["desired_result"])
            self.assertEqual("OPEN", store["entities"]["RQ-002"]["fields"]["scope"])

    def test_rq_add_exact_prompt_is_idempotent_without_revision_change(self):
        mod = load_rq_add()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = mod.add_requirement(
                root,
                title="중복 확인",
                request="같은 요청을 중복 등록하지 않는다.",
                refresh_worklist=False,
            )
            store_path = root / "sdlc/canonical/store.json"
            before = json.loads(store_path.read_text(encoding="utf-8"))["revision"]
            result = mod.add_requirement(
                root,
                title="표시 제목이 달라도 같은 원문",
                request="같은 요청을 중복 등록하지 않는다.",
                refresh_worklist=False,
            )
            after = json.loads(store_path.read_text(encoding="utf-8"))["revision"]
            self.assertEqual("RQ_ALREADY_EXISTS", result["status"])
            self.assertEqual(first["target"], result["target"])
            self.assertFalse(result["canonical_mutated"])
            self.assertEqual(before, after)

    def test_rq_add_same_title_different_prompt_requires_review(self):
        mod = load_rq_add()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mod.add_requirement(
                root,
                title="근무계획 수정 제한",
                request="승인 완료 후 일반 사용자는 근무계획을 수정할 수 없게 해줘.",
                refresh_worklist=False,
            )
            store_path = root / "sdlc/canonical/store.json"
            before = json.loads(store_path.read_text(encoding="utf-8"))["revision"]
            result = mod.add_requirement(
                root,
                title="근무계획 수정 제한",
                request="마감 완료 후에는 관리자도 근무계획을 수정하지 못하게 해줘.",
                refresh_worklist=False,
            )
            after = json.loads(store_path.read_text(encoding="utf-8"))["revision"]
            self.assertEqual("RQ_ADD_DUPLICATE_REVIEW_REQUIRED", result["status"])
            self.assertFalse(result["canonical_mutated"])
            self.assertEqual(before, after)

    def test_rq_add_does_not_auto_retry_sequence_conflict(self):
        mod = load_rq_add()
        calls = []
        original = mod.APPLY.apply_delta_to_store

        def conflict(_path, delta):
            calls.append(delta["operations"][0]["id"])
            return ({
                "status": "CONFLICT",
                "conflicts": [{"code": "STALE_BASE_REVISION"}],
            }, {"revision": 1})

        mod.APPLY.apply_delta_to_store = conflict
        try:
            with tempfile.TemporaryDirectory() as td:
                result = mod.add_requirement(
                    Path(td),
                    title="동시 생성 충돌",
                    request="동시에 RQ를 만들지 않는다.",
                    refresh_worklist=False,
                )
        finally:
            mod.APPLY.apply_delta_to_store = original

        self.assertEqual(["RQ-001"], calls)
        self.assertEqual("RQ_ADD_CONFLICT_RETRY_REQUIRED", result["status"])
        self.assertEqual("SINGLE_WRITER_FILE_DERIVED", result["sequence_policy"])
        self.assertFalse(result["canonical_mutated"])

    def test_rq_add_skill_and_guide_define_minimum_input_and_routing(self):
        skill = read("sdlc/agent/skills/rq-add/SKILL.md")
        adapter = read(".cursor/skills/rq-add/SKILL.md")
        guide = read("docs/00_시작/17_RQ_간편추가_가이드.md")
        harness = read("sdlc/scripts/harness.py")
        for marker in ["요구사항명", "요청 내용", "현재 문제/배경", "기대 결과", "적용 범위"]:
            self.assertIn(marker, skill)
            self.assertIn(marker, guide)
        for marker in ["/change", "/rq-list", "/work", "SINGLE_WRITER_FILE_DERIVED"]:
            self.assertIn(marker, skill if marker != "SINGLE_WRITER_FILE_DERIVED" else read("sdlc/scripts/rq_add.py"))
        self.assertIn("@sdlc/agent/skills/rq-add/SKILL.md", adapter)
        self.assertIn('if command == "rq-add"', harness)
        self.assertIn("RQ 생성 담당자를 한 명", guide)

    def test_scaffold_distributes_new_assets_and_framework_todo_keeps_multiwriter_deferred(self):
        contract = json.loads(read("sdlc/design/contracts/project-scaffold-contract.json"))
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
            self.assertTrue((ROOT / rel).is_file(), rel)
        todo = read("framework/design/session/FRAMEWORK_ENHANCEMENT_TODO_V110.md")
        self.assertIn("TODO-4. Multi-writer RQ ID / Sequence Allocation", todo)
        self.assertIn("Multi-writer RQ Sequence/Reservation Runtime 구현", todo)
        self.assertIn("현재 운영은 RQ 생성 담당자 한 명", todo)


if __name__ == "__main__":
    unittest.main()
