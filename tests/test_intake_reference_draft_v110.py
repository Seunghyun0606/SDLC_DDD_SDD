from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT_DIR = ROOT / "sdlc/scripts"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


DRAFT = load("intake_reference_draft_v110_test", "intake_reference_draft.py")
REGISTRY = DRAFT.REGISTRY

PROJECT_YAML = """schema_version: 1
project:
  name: intake-reference-draft-test
  mode: BROWNFIELD
delivery:
  profile: STANDARD
change:
  level_policy: AUTO
technology:
  language: Java
  framework: Spring
  build: []
  test: []
source:
  roots:
    - src
  test_roots: []
  resource_roots: []
  excludes: []
git:
  protected_branches:
    - main
documents:
  language: ko-KR
  engineering:
    profile: ENGINEERING_SDD_COMPACT
  customer:
    profile: CUSTOMER_STANDARD_3
  pm:
    profile: PM_STANDARD
  machine:
    visibility: HIDDEN
unresolved: []
"""


def rq(rq_id: str, name: str, external: str):
    return {
        "id": rq_id,
        "entity_type": "RQ",
        "fields": {
            "name": name,
            "original_requirement": f"{name} 요구사항",
            "external_requirement_ids": [external],
        },
        "truth_status": "CANDIDATE",
        "provenance": [],
    }


class IntakeReferenceDraftV110Test(unittest.TestCase):
    def make_project(self, root: Path) -> Path:
        (root / ".sdlc").mkdir(parents=True)
        (root / ".sdlc/project.yaml").write_text(PROJECT_YAML, encoding="utf-8")
        store = root / "sdlc/canonical/store.json"
        store.parent.mkdir(parents=True)
        store.write_text(json.dumps({
            "schema_version": 1,
            "revision": 3,
            "updated_at": None,
            "entities": {
                "RQ-001": rq("RQ-001", "근무계획 개선", "REQ-001"),
                "RQ-002": rq("RQ-002", "승인 기능 개선", "REQ-002"),
            },
            "relations": [],
            "applied_deltas": [],
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return store

    def test_draft_registers_supporting_doc_and_keeps_canonical_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = self.make_project(root)
            before = store.read_bytes()
            support = root / "incoming/근무계획_설명.md"
            support.parent.mkdir(parents=True)
            support.write_text(
                "# 근무계획 개선\n\nREQ-001 근무계획 등록 화면의 근무시간 입력과 저장 방식을 개선한다.\n",
                encoding="utf-8",
            )

            result = DRAFT.draft(root, ["RQ-001", "RQ-002"], [support])

            self.assertEqual("RQ_REFERENCE_DRAFT_CREATED", result["status"])
            self.assertTrue(result["agent_review_required"])
            self.assertFalse(result["canonical_mutated"])
            self.assertEqual(before, store.read_bytes())
            self.assertTrue((root / "br-input/manifest.yaml").is_file())
            self.assertTrue((root / DRAFT.AGENT_CONTEXT_PATH).is_file())
            self.assertTrue((root / DRAFT.REVIEW_MD_PATH).is_file())

            context = json.loads((root / DRAFT.AGENT_CONTEXT_PATH).read_text(encoding="utf-8"))
            self.assertFalse(context["canonical_mutated"])
            self.assertEqual("AGENT_REFERENCE_REVIEW_REQUIRED", context["status"])
            self.assertGreaterEqual(len(context["documents"]), 1)
            self.assertGreaterEqual(len(context["proposals"]), 1)
            self.assertTrue(any(row["rq_id"] == "RQ-001" for row in context["proposals"]))

            registry = json.loads((root / REGISTRY.STORE_PATH).read_text(encoding="utf-8"))
            self.assertTrue(any(row.get("review_status") == "제안" for row in registry["links"]))
            doc_id = next(iter(context["documents"]))
            evidence_file = root / context["documents"][doc_id]["evidence_file"]
            self.assertTrue(evidence_file.is_file())
            evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
            self.assertGreater(evidence.get("chunk_count", 0), 0)

    def test_generated_markdown_is_editable_review_input(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = self.make_project(root)
            before = store.read_bytes()
            support = root / "참고자료.txt"
            support.write_text("승인 기능 개선 REQ-002 팀장 승인 결과와 예외 처리", encoding="utf-8")
            DRAFT.draft(root, ["RQ-002"], [support])

            review = root / DRAFT.REVIEW_MD_PATH
            text = review.read_text(encoding="utf-8")
            self.assertIn("검토상태", text)
            self.assertIn("제안", text)
            review.write_text(text.replace("| 제안 |", "| 확정 |"), encoding="utf-8")

            result = REGISTRY.import_registry(root, review)
            self.assertEqual("RQ_REFERENCE_REGISTRY_IMPORTED", result["status"])
            self.assertEqual(before, store.read_bytes())
            rows = json.loads((root / REGISTRY.STORE_PATH).read_text(encoding="utf-8"))["links"]
            self.assertTrue(rows)
            self.assertTrue(all(row["review_status"] == "확정" for row in rows))

    def test_reference_directory_excludes_primary_requirement_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            package = root / "package"
            package.mkdir()
            requirement = package / "요구사항목록.xlsx"
            requirement.write_bytes(b"requirement-placeholder")
            ppt = package / "기능설명.pptx"
            ppt.write_bytes(b"ppt-placeholder")
            txt = package / "회의내용.txt"
            txt.write_text("회의 참고자료", encoding="utf-8")

            paths = DRAFT.collect_reference_paths(
                root,
                reference_dirs=[str(package)],
                primary_requirement=requirement,
            )
            self.assertNotIn(requirement.resolve(), paths)
            self.assertIn(ppt.resolve(), paths)
            self.assertIn(txt.resolve(), paths)

    def test_contract_requires_agent_review_and_noncanonical_draft(self):
        contract = json.loads((ROOT / "sdlc/design/contracts/rq-reference-registry-contract.json").read_text(encoding="utf-8"))
        draft = contract["intake_draft"]
        self.assertTrue(draft["supporting_documents_may_arrive_in_same_intake_package"])
        self.assertTrue(draft["runtime_prefilter_is_not_semantic_confirmation"])
        self.assertTrue(draft["interactive_agent_must_review_actual_extracted_content"])
        self.assertEqual("제안", draft["initial_review_status"])
        self.assertFalse(draft["canonical_mutation"])
        self.assertTrue(contract["rules"]["human_may_review_by_markdown_excel_or_natural_language"])

    def test_framework_todo_keeps_deferred_enhancements_out_of_current_runtime_claims(self):
        todo = (ROOT / "framework/design/session/FRAMEWORK_ENHANCEMENT_TODO_V110.md").read_text(encoding="utf-8")
        self.assertIn("Work Unit 누적", todo)
        self.assertIn("AS-IS 시스템 분석", todo)
        self.assertIn("E2E", todo)
        self.assertIn("TODO / 후순위", todo)
        self.assertIn("Project Scaffold에는 배포하지 않는다", todo)


if __name__ == "__main__":
    unittest.main()
