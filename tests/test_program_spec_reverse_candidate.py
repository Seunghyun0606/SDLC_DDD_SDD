import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "sdlc/custom/project/adapters/impact/java_spring_mybatis.py"
REVERSE_PATH = ROOT / "sdlc/scripts/generate_program_spec_reverse_candidate.py"
AS_IS = ROOT / "sdlc/validation/pilot/source-fixture/as-is"
TO_BE = ROOT / "sdlc/validation/pilot/source-fixture/to-be"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


ADAPTER = load_module("impact_adapter_reverse_test", ADAPTER_PATH)
REVERSE = load_module("program_spec_reverse_candidate", REVERSE_PATH)


class ProgramSpecReverseCandidateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = ADAPTER.analyze(AS_IS)
        cls.after = ADAPTER.analyze(TO_BE)
        cls.bindings = {
            "schema_version": 1,
            "programs": [
                {
                    "program_id": "PGM-FLEX-PLAN",
                    "artifact_path": "docs/program/PGM-FLEX-PLAN.md",
                    "functional_design_ref": "FD-FLEX-PLAN",
                    "source_node_ids": ["symbol:com.acme.tm.FlexibleWorkPlanService#getPlan"],
                },
                {
                    "program_id": "PGM-UNRELATED",
                    "artifact_path": "docs/program/PGM-UNRELATED.md",
                    "functional_design_ref": "FD-UNRELATED",
                    "source_node_ids": ["symbol:com.acme.OtherService#other"],
                },
            ],
        }
        cls.result = REVERSE.generate(cls.before, cls.after, cls.bindings)

    def test_only_related_program_gets_candidate(self):
        candidates = self.result["program_candidates"]
        self.assertEqual(1, len(candidates))
        self.assertEqual("PGM-FLEX-PLAN", candidates[0]["program_id"])

    def test_new_service_method_is_related_through_existing_mapper(self):
        candidate = self.result["program_candidates"][0]
        related = {row["node_id"]: row["distance"] for row in candidate["implementation_delta"]["related_changed_nodes"]}
        self.assertIn("symbol:com.acme.tm.FlexibleWorkPlanService#initializeFirstPlan", related)
        self.assertLessEqual(related["symbol:com.acme.tm.FlexibleWorkPlanService#initializeFirstPlan"], 3)

    def test_graph_diff_detects_additions_without_fake_mapper_or_data_removal(self):
        delta = self.result["program_candidates"][0]["implementation_delta"]["graph_delta"]
        added_nodes = {row["id"] for row in delta["added_nodes"]}
        self.assertIn("symbol:com.acme.tm.FlexibleWorkPlanController#initializeFirstPlan", added_nodes)
        self.assertIn("symbol:com.acme.tm.FlexibleWorkPlanService#initializeFirstPlan", added_nodes)
        self.assertEqual([], delta["removed_nodes"])
        self.assertEqual([], delta["removed_edges"])
        added_data_nodes = [row for row in delta["added_nodes"] if row["type"] == "DATA_ASSET"]
        self.assertEqual([], added_data_nodes)

    def test_candidate_is_non_destructive_and_business_safe(self):
        candidate = self.result["program_candidates"][0]
        self.assertTrue(candidate["review_required"])
        self.assertFalse(candidate["auto_apply"])
        self.assertFalse(candidate["artifact_file_modified"])
        self.assertFalse(candidate["business_truth_auto_update"])
        self.assertFalse(candidate["functional_design_auto_update"])
        self.assertTrue(self.result["safety"]["candidate_only"])
        self.assertFalse(self.result["safety"]["automatic_rewrite"])

    def test_patch_scope_excludes_functional_and_business_semantics(self):
        scope = self.result["program_candidates"][0]["program_spec_patch_scope"]
        self.assertIn("실제 구현 Target", scope["allowed_sections"])
        self.assertIn("구현 준비도", scope["allowed_sections"])
        self.assertIn("Business Truth", scope["forbidden_semantic_sections"])
        self.assertIn("업무 규칙", scope["forbidden_semantic_sections"])

    def test_same_inputs_produce_same_candidate_id(self):
        again = REVERSE.generate(self.before, self.after, self.bindings)
        self.assertEqual(
            self.result["program_candidates"][0]["candidate_id"],
            again["program_candidates"][0]["candidate_id"],
        )
        self.assertEqual(self.result, again)

    def test_zero_hop_does_not_claim_related_change(self):
        result = REVERSE.generate(self.before, self.after, self.bindings, max_hops=0)
        self.assertEqual([], result["program_candidates"])

    def test_invalid_binding_fails_closed(self):
        broken = {"schema_version": 1, "programs": [{"program_id": "PGM-X"}]}
        with self.assertRaises(ValueError):
            REVERSE.generate(self.before, self.after, broken)

    def test_cli_writes_candidate_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            before = root / "before.json"
            after = root / "after.json"
            bindings = root / "bindings.json"
            output = root / "candidate.json"
            before.write_text(json.dumps(self.before, ensure_ascii=False), encoding="utf-8")
            after.write_text(json.dumps(self.after, ensure_ascii=False), encoding="utf-8")
            bindings.write_text(json.dumps(self.bindings, ensure_ascii=False), encoding="utf-8")
            rc = REVERSE.main([
                "--baseline-impact", str(before),
                "--observed-impact", str(after),
                "--program-bindings", str(bindings),
                "--output", str(output),
            ])
            self.assertEqual(0, rc)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual("PROGRAM_SPEC_SEMANTIC_REVERSE_CANDIDATE", payload["capability"])
            self.assertEqual(1, payload["summary"]["candidate_count"])


if __name__ == "__main__":
    unittest.main()
