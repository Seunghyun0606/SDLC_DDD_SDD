import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("detect_source_drift", ROOT / "sdlc/scripts/detect_source_drift.py")
drift_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(drift_mod)

HARNESS = json.loads((ROOT / "sdlc/design/contracts/harness-package-contract.json").read_text(encoding="utf-8"))
AGENT = json.loads((ROOT / "sdlc/design/contracts/agent-execution-contract.json").read_text(encoding="utf-8"))
IMPACT = json.loads((ROOT / "sdlc/design/contracts/brownfield-impact-contract.json").read_text(encoding="utf-8"))
DRIFT = json.loads((ROOT / "sdlc/design/contracts/source-drift-contract.json").read_text(encoding="utf-8"))


class AgentExecutionAndImpactBoundaryTest(unittest.TestCase):
    def test_all_stage_references_have_deterministic_execution_format(self):
        refs = ROOT / ".cursor/skills/work/references"
        for stage, contract in HARNESS["stage_contracts"].items():
            text = (refs / contract["reference"]).read_text(encoding="utf-8")
            self.assertIn("## 실행 계약(Agent Execution Contract)", text, stage)
            for marker in AGENT["execution_contract_required_markers"]:
                self.assertIn(marker, text, f"{stage}:{marker}")

    def test_agent_contract_separates_reference_and_template_roles(self):
        guidance = AGENT["format_guidance"]
        self.assertTrue(guidance["reference_document_is_executable_instruction"])
        self.assertTrue(guidance["template_is_user_facing_output_format"])
        self.assertTrue(guidance["project_specific_retrieval_logic_belongs_to_profile_or_adapter"])

    def test_brownfield_core_only_defines_common_contract(self):
        boundary = IMPACT["project_adapter_boundary"]
        self.assertEqual("CORE_COMMON_CONTRACT_ONLY", IMPACT["scope"])
        self.assertTrue(boundary["adapter_required_for_project_specific_resolution"])
        self.assertTrue(boundary["core_does_not_implement_language_framework_specific_resolution"])

    def test_missing_project_adapter_cannot_claim_complete_impact(self):
        self.assertEqual(
            "PARTIAL_PROJECT_ADAPTER_REQUIRED",
            IMPACT["completion_rules"]["without_project_adapter"],
        )
        self.assertTrue(IMPACT["core_responsibility"]["coverage_gaps_must_be_reported"])
        self.assertTrue(IMPACT["core_responsibility"]["not_found_does_not_mean_no_impact"])

    def test_project_adapter_implementation_location_is_explicit(self):
        readme = (ROOT / "sdlc/custom/project/adapters/impact/README.md").read_text(encoding="utf-8")
        self.assertIn("프로젝트별 별도 구현", readme)
        self.assertIn("Project Custom", readme)


class SourceDriftTest(unittest.TestCase):
    def manifest(self, ref, rows):
        return {"schema_version": 1, "source_ref": ref, "evidence": rows}

    def artifact_index(self, artifacts, edges=None):
        return {"schema_version": 1, "artifacts": artifacts, "propagation_edges": edges or []}

    def artifact(self, artifact_id, source_hash="h1", path="src/A.java", symbol="A#m", artifact_type="PROGRAM_SPEC"):
        return {
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "status": "CURRENT",
            "source_evidence": [{"path": path, "symbol": symbol, "source_hash": source_hash}],
        }

    def test_modified_source_marks_direct_artifact_stale(self):
        before = self.manifest("base", [{"path": "src/A.java", "symbol": "A#m", "hash": "h1"}])
        after = self.manifest("head", [{"path": "src/A.java", "symbol": "A#m", "hash": "h2"}])
        result = drift_mod.analyze(before, after, self.artifact_index([self.artifact("PGM-1")]))
        self.assertEqual("MODIFIED", result["source_drift"][0]["state"])
        self.assertEqual("STALE_SOURCE_EVIDENCE", result["artifact_impacts"][0]["impact_status"])

    def test_deleted_source_marks_direct_artifact_stale(self):
        before = self.manifest("base", [{"path": "src/A.java", "symbol": "A#m", "hash": "h1"}])
        after = self.manifest("head", [])
        result = drift_mod.analyze(before, after, self.artifact_index([self.artifact("PGM-1")]))
        self.assertEqual("DELETED", result["source_drift"][0]["state"])
        self.assertEqual(1, result["summary"]["direct_stale_artifacts"])

    def test_stale_policy_propagates_through_explicit_edges(self):
        before = self.manifest("base", [{"path": "src/A.java", "symbol": "A#m", "hash": "h1"}])
        after = self.manifest("head", [{"path": "src/A.java", "symbol": "A#m", "hash": "h2"}])
        artifacts = [self.artifact("PGM-1"), {"artifact_id": "FD-1", "artifact_type": "FUNCTIONAL_DESIGN", "status": "CURRENT", "source_evidence": []}, {"artifact_id": "IA-1", "artifact_type": "IMPACT", "status": "CURRENT", "source_evidence": []}]
        edges = [
            {"from_artifact": "PGM-1", "to_artifact": "FD-1", "on_source_drift": "STALE", "kind": "REVERSE_DERIVED"},
            {"from_artifact": "FD-1", "to_artifact": "IA-1", "on_source_drift": "STALE", "kind": "REVERSE_DERIVED"},
        ]
        result = drift_mod.analyze(before, after, self.artifact_index(artifacts, edges))
        statuses = {x["artifact_id"]: x["impact_status"] for x in result["artifact_impacts"]}
        self.assertEqual("STALE_SOURCE_EVIDENCE", statuses["PGM-1"])
        self.assertEqual("STALE_PROPAGATED", statuses["FD-1"])
        self.assertEqual("STALE_PROPAGATED", statuses["IA-1"])

    def test_check_required_does_not_propagate_automatically(self):
        before = self.manifest("base", [{"path": "src/A.java", "symbol": "A#m", "hash": "h1"}])
        after = self.manifest("head", [{"path": "src/A.java", "symbol": "A#m", "hash": "h2"}])
        artifacts = [self.artifact("PGM-1"), {"artifact_id": "FR-1", "artifact_type": "FR", "status": "CURRENT", "source_evidence": []}, {"artifact_id": "RQ-1", "artifact_type": "RQ", "status": "CURRENT", "source_evidence": []}]
        edges = [
            {"from_artifact": "PGM-1", "to_artifact": "FR-1", "on_source_drift": "CHECK_REQUIRED"},
            {"from_artifact": "FR-1", "to_artifact": "RQ-1", "on_source_drift": "STALE"},
        ]
        result = drift_mod.analyze(before, after, self.artifact_index(artifacts, edges))
        statuses = {x["artifact_id"]: x["impact_status"] for x in result["artifact_impacts"]}
        self.assertEqual("CHECK_REQUIRED_REVERSE", statuses["FR-1"])
        self.assertNotIn("RQ-1", statuses)

    def test_added_source_does_not_stale_unrelated_artifact(self):
        before = self.manifest("base", [{"path": "src/A.java", "symbol": "A#m", "hash": "h1"}])
        after = self.manifest("head", [{"path": "src/A.java", "symbol": "A#m", "hash": "h1"}, {"path": "src/B.java", "symbol": "B#n", "hash": "b1"}])
        result = drift_mod.analyze(before, after, self.artifact_index([self.artifact("PGM-1")]))
        self.assertEqual([], result["artifact_impacts"])
        self.assertEqual(1, result["summary"]["source_added"])

    def test_artifact_already_regenerated_to_observed_hash_is_not_stale(self):
        before = self.manifest("base", [{"path": "src/A.java", "symbol": "A#m", "hash": "h1"}])
        after = self.manifest("head", [{"path": "src/A.java", "symbol": "A#m", "hash": "h2"}])
        result = drift_mod.analyze(before, after, self.artifact_index([self.artifact("PGM-1", source_hash="h2")]))
        self.assertEqual([], result["artifact_impacts"])

    def test_stale_cycle_is_safe(self):
        before = self.manifest("base", [{"path": "src/A.java", "symbol": "A#m", "hash": "h1"}])
        after = self.manifest("head", [{"path": "src/A.java", "symbol": "A#m", "hash": "h2"}])
        artifacts = [self.artifact("A"), {"artifact_id": "B", "artifact_type": "DESIGN", "status": "CURRENT", "source_evidence": []}]
        edges = [
            {"from_artifact": "A", "to_artifact": "B", "on_source_drift": "STALE"},
            {"from_artifact": "B", "to_artifact": "A", "on_source_drift": "STALE"},
        ]
        result = drift_mod.analyze(before, after, self.artifact_index(artifacts, edges))
        self.assertEqual(2, len(result["artifact_impacts"]))

    def test_reverse_result_never_auto_updates_artifact_or_business_truth(self):
        before = self.manifest("base", [{"path": "src/A.java", "symbol": "A#m", "hash": "h1"}])
        after = self.manifest("head", [{"path": "src/A.java", "symbol": "A#m", "hash": "h2"}])
        result = drift_mod.analyze(before, after, self.artifact_index([self.artifact("PGM-1")]))
        self.assertFalse(result["safety"]["artifact_files_modified"])
        self.assertFalse(result["safety"]["business_truth_modified"])
        self.assertTrue(result["safety"]["reverse_result_is_candidate_only"])
        self.assertFalse(result["reverse_candidates"][0]["auto_apply"])

    def test_invalid_propagation_endpoint_fails_closed(self):
        before = self.manifest("base", [])
        after = self.manifest("head", [])
        index = self.artifact_index(
            [{"artifact_id": "A", "artifact_type": "DESIGN", "status": "CURRENT", "source_evidence": []}],
            [{"from_artifact": "A", "to_artifact": "MISSING", "on_source_drift": "STALE"}],
        )
        with self.assertRaises(ValueError):
            drift_mod.analyze(before, after, index)

    def test_contract_forbids_automatic_reverse_rewrite(self):
        self.assertFalse(DRIFT["rules"]["auto_rewrite_artifact"])
        self.assertFalse(DRIFT["rules"]["auto_update_business_truth"])
        self.assertTrue(DRIFT["rules"]["stale_propagation_requires_explicit_edge"])


if __name__ == "__main__":
    unittest.main()
