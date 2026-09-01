import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sdlc/scripts/validate_agent_stage_result.py"
SPEC = importlib.util.spec_from_file_location("validate_agent_stage_result", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)


def delta(artifact_path="docs/req.md", *, base_revision=0, delta_id="DELTA-001", stage="DECOMPOSE"):
    return {
        "schema_version": 1,
        "delta_id": delta_id,
        "base_revision": base_revision,
        "stage": stage,
        "source_artifact": artifact_path,
        "operations": [{
            "op": "UPSERT_ENTITY",
            "id": "RQ-001",
            "entity_type": "RQ",
            "fields": {"name": "근무계획 자동 설정"},
            "evidence_class": "GIVEN",
            "truth_status": "CANDIDATE",
        }],
    }


def stage_result(artifact_path="docs/req.md", *, stage="DECOMPOSE", quality="PASS"):
    return {
        "schema_version": 1,
        "stage": stage,
        "artifact_path": artifact_path,
        "canonical_delta": delta(artifact_path, stage=stage),
        "quality_gate": {"status": quality, "failures": [], "checked_at": "2026-09-02T01:00:00+09:00"},
        "alerts": [],
        "uncertainty": [],
        "generated_at": "2026-09-02T01:00:00+09:00",
    }


def artifact_text(*, generated_at="2026-09-02T01:00:00+09:00", body="근무계획을 자동 설정한다."):
    return f'''---\nstage: DECOMPOSE\ngenerated_at: {generated_at}\n---\n# 요구사항\n\n## 한눈에 보기\n{body}\n\n## 관련 ID 및 추적성\nRQ-001\n'''


class AgentStageResultBehaviorTest(unittest.TestCase):
    def _fixture(self, root: Path, path="docs/req.md", text=None):
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text or artifact_text(), encoding="utf-8")
        return target

    def test_valid_result_is_executable_against_empty_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            store = root / "canonical/store.json"
            validation = MOD.validate_stage_result(stage_result(), root, store_path=store)
            self.assertEqual("PASS", validation["status"])
            self.assertTrue(validation["executable"])
            self.assertEqual("APPLIED", validation["canonical_check"]["status"])
            self.assertTrue(validation["semantic_fingerprint"].startswith("sha256:"))
            self.assertFalse(store.exists())

    def test_missing_canonical_delta_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            result = stage_result()
            result.pop("canonical_delta")
            validation = MOD.validate_stage_result(result, root)
            self.assertEqual("FAIL", validation["status"])
            self.assertIn("MISSING_CANONICAL_DELTA", [x["code"] for x in validation["errors"]])

    def test_stage_and_delta_stage_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            result = stage_result()
            result["canonical_delta"]["stage"] = "DESIGN"
            validation = MOD.validate_stage_result(result, root)
            self.assertIn("STAGE_DELTA_MISMATCH", [x["code"] for x in validation["errors"]])

    def test_artifact_and_delta_source_must_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            result = stage_result()
            result["canonical_delta"]["source_artifact"] = "docs/other.md"
            validation = MOD.validate_stage_result(result, root)
            self.assertIn("ARTIFACT_DELTA_SOURCE_MISMATCH", [x["code"] for x in validation["errors"]])

    def test_unresolved_template_placeholder_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root, text=artifact_text(body="{{summary}}"))
            validation = MOD.validate_stage_result(stage_result(), root)
            self.assertIn("UNRESOLVED_TEMPLATE_PLACEHOLDER", [x["code"] for x in validation["errors"]])

    def test_artifact_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = stage_result("../outside.md")
            validation = MOD.validate_stage_result(result, root)
            self.assertIn("ARTIFACT_PATH_TRAVERSAL", [x["code"] for x in validation["errors"]])

    def test_quality_fail_is_valid_but_not_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            validation = MOD.validate_stage_result(stage_result(quality="FAIL"), root)
            self.assertEqual("PASS", validation["status"])
            self.assertFalse(validation["executable"])
            self.assertIn("QUALITY_GATE_FAILED", [x["code"] for x in validation["warnings"]])

    def test_semantic_fingerprint_ignores_volatile_timestamps(self):
        first = stage_result()
        second = copy.deepcopy(first)
        second["generated_at"] = "2026-09-02T02:00:00+09:00"
        second["quality_gate"]["checked_at"] = "2026-09-02T02:00:00+09:00"
        comparison = MOD.compare_stage_results(
            first,
            artifact_text(generated_at="2026-09-02T01:00:00+09:00"),
            second,
            artifact_text(generated_at="2026-09-02T02:00:00+09:00"),
        )
        self.assertEqual("MATCH", comparison["status"])

    def test_semantic_change_is_detected_across_repeated_runs(self):
        result = stage_result()
        comparison = MOD.compare_stage_results(
            result,
            artifact_text(body="근무계획을 자동 설정한다."),
            copy.deepcopy(result),
            artifact_text(body="근무계획을 수동 설정한다."),
        )
        self.assertEqual("MISMATCH", comparison["status"])

    def test_stale_canonical_revision_makes_result_not_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            store_path = root / "canonical/store.json"
            store_path.parent.mkdir(parents=True, exist_ok=True)
            store = MOD.APPLY.empty_store()
            applied, next_store = MOD.APPLY.apply_delta(store, delta())
            self.assertEqual("APPLIED", applied["status"])
            MOD.APPLY.save_store(store_path, next_store)

            stale = stage_result()
            stale["canonical_delta"]["delta_id"] = "DELTA-002"
            stale["canonical_delta"]["base_revision"] = 0
            validation = MOD.validate_stage_result(stale, root, store_path=store_path)
            self.assertEqual("FAIL", validation["status"])
            self.assertFalse(validation["executable"])
            self.assertIn("CANONICAL_APPLY_NOT_EXECUTABLE", [x["code"] for x in validation["errors"]])
            self.assertEqual(1, json.loads(store_path.read_text(encoding="utf-8"))["revision"])

    def test_idempotent_canonical_replay_is_executable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._fixture(root)
            store_path = root / "canonical/store.json"
            store_path.parent.mkdir(parents=True, exist_ok=True)
            _, next_store = MOD.APPLY.apply_delta(MOD.APPLY.empty_store(), delta())
            MOD.APPLY.save_store(store_path, next_store)
            validation = MOD.validate_stage_result(stage_result(), root, store_path=store_path)
            self.assertEqual("PASS", validation["status"])
            self.assertTrue(validation["executable"])
            self.assertEqual("IDEMPOTENT", validation["canonical_check"]["status"])


if __name__ == "__main__":
    unittest.main()
