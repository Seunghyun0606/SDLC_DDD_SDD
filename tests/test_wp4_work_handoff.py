from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


HANDOFF = load("test_wp4_handoff", ROOT / "sdlc/scripts/work_handoff.py")
REVIEW = load("test_wp4_review", ROOT / "sdlc/scripts/review_work.py")
HARNESS = load("test_wp4_harness", ROOT / "sdlc/scripts/harness.py")


class WP4WorkHandoffTest(unittest.TestCase):
    def seed_project(self, root: Path) -> Path:
        store = root / "sdlc/canonical/store.json"
        store.parent.mkdir(parents=True, exist_ok=True)
        store.write_text(json.dumps({
            "schema_version": 1,
            "revision": 0,
            "updated_at": None,
            "entities": {
                "RQ-001": {
                    "entity_type": "RQ",
                    "truth_status": "CANDIDATE",
                    "fields": {
                        "name": "탄력근로제 근무계획 저장",
                        "current_problem": "OPEN",
                        "business_rules": "OPEN"
                    },
                    "provenance": []
                }
            },
            "relations": [],
            "applied_deltas": []
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return store

    def provider(self, root: Path) -> Path:
        path = root / "provider.json"
        path.write_text(json.dumps({
            "schema_version": 1,
            "provider_id": "WP4_VALIDATION_FIXTURE",
            "provider_class": "VALIDATION_FIXTURE",
            "enabled": True,
            "timeout_seconds": 30,
            "result_filename": "stage-result.json",
            "allow_dirty_workspace": True,
            "command": [
                sys.executable,
                str(ROOT / "sdlc/validation/providers/deterministic_stage_provider.py"),
                "--context", "{context_path}", "--result", "{result_path}"
            ]
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path

    def test_official_harness_plan_defaults_to_user_document_not_runtime_document(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.seed_project(root)
            config = root / ".sdlc/project.yaml"
            config.parent.mkdir(parents=True, exist_ok=True)
            config.write_text(
                "schema_version: 1\nproject:\n  name: wp4-test\n  mode: GREENFIELD\ndelivery:\n  profile: STANDARD\n",
                encoding="utf-8",
            )
            out = StringIO()
            with redirect_stdout(out):
                code = HARNESS.main(["work", "--root", str(root), "--target", "RQ-001", "--plan-only"])
            self.assertEqual(code, 0)
            result = json.loads(out.getvalue())
            self.assertEqual(result["status"], "PLAN_READY")
            artifact = result["plan"]["selection"]["artifact_path"]
            self.assertTrue(artifact.startswith("docs/10_산출물/"), artifact)
            self.assertNotIn("sdlc/runtime/work/", artifact)
            self.assertIn("BUSINESS_POLICY", result["plan"]["human_handoff_policy"]["human_decision_categories"])
            self.assertIn("Provider 연결 시 Agent", result["user_handoff"]["message"])

    def test_execution_separates_human_document_from_machine_runtime(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.seed_project(root)
            provider = self.provider(root)
            out = StringIO()
            with redirect_stdout(out):
                code = HANDOFF.main([
                    "--root", str(root), "--target", "RQ-001", "--provider-config", str(provider)
                ])
            self.assertEqual(code, 0, out.getvalue())
            result = json.loads(out.getvalue())
            self.assertIn(result["status"], {"NO_CHANGE", "IDEMPOTENT", "APPLIED"})
            document = root / result["user_handoff"]["document"]
            self.assertTrue(document.is_file())
            self.assertTrue(result["user_handoff"]["document"].startswith("docs/10_산출물/"))
            self.assertTrue(str(result["context_path"]).startswith(str(root / "sdlc/runtime/work-runs")))
            self.assertTrue(str(result["result_path"]).startswith(str(root / "sdlc/runtime/work-runs")))
            handoff = root / result["handoff_path"]
            self.assertTrue(handoff.is_file())
            self.assertTrue(result["handoff_path"].startswith("sdlc/runtime/work-handoff/"))
            context = json.loads(Path(result["context_path"]).read_text(encoding="utf-8"))
            self.assertTrue(context["human_handoff_policy"]["no_invention"])
            self.assertFalse(result["user_handoff"]["review_required"])

    def test_explicit_artifact_is_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.seed_project(root)
            out = StringIO()
            with redirect_stdout(out):
                code = HANDOFF.main([
                    "--root", str(root), "--target", "RQ-001", "--artifact", "docs/custom/requirement.md", "--plan-only"
                ])
            self.assertEqual(code, 0)
            result = json.loads(out.getvalue())
            self.assertEqual(result["plan"]["selection"]["artifact_path"], "docs/custom/requirement.md")
            self.assertEqual(result["plan"]["selection"]["artifact_reason"], "USER_ARTIFACT_OVERRIDE")

    def test_only_explicit_authority_uncertainty_is_sent_to_human(self):
        result = {
            "uncertainty": [
                {"state": "OPEN", "category": "BUSINESS_POLICY", "requires_human_decision": True, "question": "승인 주체는 누구인가?"},
                {"state": "CHECK_REQUIRED", "category": "SOURCE_EVIDENCE", "requires_human_decision": False, "question": "기존 API를 더 조사한다"},
                {"state": "OPEN", "category": "SCOPE", "question": "적용 법인은?"},
                "기존 Source를 추가 조사해야 함"
            ]
        }
        review, agent_open = HANDOFF.partition_uncertainty(result)
        self.assertEqual(len(review), 1)
        self.assertEqual(review[0]["category"], "BUSINESS_POLICY")
        self.assertEqual(len(agent_open), 3)

    def test_review_answer_records_confirmed_provenance_without_business_field_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = self.seed_project(root)
            document = root / "docs/10_산출물/RQ-001_요구사항정의.md"
            document.parent.mkdir(parents=True, exist_ok=True)
            document.write_text("# 요구사항 정의\n", encoding="utf-8")
            handoff = root / "sdlc/runtime/work-handoff/RQ-001.json"
            handoff.parent.mkdir(parents=True, exist_ok=True)
            handoff.write_text(json.dumps({
                "schema_version": 1, "target": "RQ-001", "document": "docs/10_산출물/RQ-001_요구사항정의.md",
                "review_required": True, "review_items": [{"category": "APPROVAL", "question": "승인 주체는?"}]
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            before = json.loads(store.read_text(encoding="utf-8"))["entities"]["RQ-001"]["fields"].copy()
            out = StringIO()
            with redirect_stdout(out):
                code = REVIEW.main([
                    "--root", str(root), "--target", "RQ-001", "--by", "업무담당자",
                    "--answer", "승인 주체는 팀장으로 한다", "--store", str(store)
                ])
            self.assertEqual(code, 0, out.getvalue())
            result = json.loads(out.getvalue())
            self.assertEqual(result["status"], "REVIEW_RECORDED")
            self.assertFalse(result["business_fields_auto_changed"])
            after_store = json.loads(store.read_text(encoding="utf-8"))
            self.assertEqual(after_store["entities"]["RQ-001"]["fields"], before)
            provenance = after_store["entities"]["RQ-001"]["provenance"][-1]
            self.assertEqual(provenance["evidence_class"], "CONFIRMED")
            self.assertIn("승인 주체는 팀장", provenance["note"])
            self.assertIn("harness.py work --target RQ-001", result["next_command"])

    def test_completed_requirement_example_is_not_placeholder_form(self):
        text = (ROOT / "sdlc/guides/요구사항_정의_완성예시.md").read_text(encoding="utf-8")
        self.assertNotIn("{{", text)
        self.assertIn("REQ_TM_FL001", text)
        self.assertIn("탄력근로제 근무계획 저장", text)
        self.assertIn("OPEN", text)
        self.assertIn("발명하지", text)


if __name__ == "__main__":
    unittest.main()
