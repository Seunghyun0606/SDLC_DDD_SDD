from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "sdlc" / "scripts"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


EXPLAIN = load("test_intake_explainable", "intake_explainable.py")


class RequirementExtractionManifestTest(unittest.TestCase):
    def test_rq_manifest_explains_exact_grouping_and_similarity_review(self):
        data = {
            "source_records": [
                {"source_record_id": "SRCREQ-000001", "source_file": "requirements.xlsx", "source_sheet": "요구사항", "source_row": 4},
                {"source_record_id": "SRCREQ-000002", "source_file": "requirements.xlsx", "source_sheet": "요구사항", "source_row": 5},
                {"source_record_id": "SRCREQ-000003", "source_file": "requirements.xlsx", "source_sheet": "요구사항", "source_row": 8},
            ],
            "rq_candidates": [
                {
                    "candidate_id": "RQ-CAND-0001",
                    "stable_key": "rqgrp:a",
                    "level1": "인사",
                    "level2": "근태",
                    "name": "휴가 취소",
                    "source_record_ids": ["SRCREQ-000001", "SRCREQ-000002"],
                    "external_requirement_ids": ["FL004", "FL005"],
                },
                {
                    "candidate_id": "RQ-CAND-0002",
                    "stable_key": "rqgrp:b",
                    "level1": "인사",
                    "level2": "근태",
                    "name": "휴가 취소 결과",
                    "source_record_ids": ["SRCREQ-000003"],
                    "external_requirement_ids": ["FL007"],
                },
            ],
            "grouping_reviews": [
                {
                    "type": "GROUPING_REVIEW",
                    "candidate_a": "RQ-CAND-0001",
                    "candidate_b": "RQ-CAND-0002",
                    "similarity": 0.9,
                    "auto_merged": False,
                }
            ],
            "canonical": {"rq_target_ids": ["RQ-002", "RQ-022"]},
        }
        manifests = EXPLAIN.build_extraction_manifests(data)
        rq = manifests["RQ-002"]
        self.assertEqual([4, 5], rq["source_rows"])
        self.assertEqual(["FL004", "FL005"], rq["external_requirement_ids"])
        self.assertEqual("EXACT_GROUP_BY", rq["grouping_method"])
        self.assertFalse(rq["auto_merge"])
        self.assertEqual("REVIEW_REQUIRED", rq["human_decision"])
        self.assertEqual(1, len(rq["similarity_candidates"]))

    def test_rq_001_002_022_manifest_targets_remain_distinct(self):
        data = {
            "source_records": [
                {"source_record_id": f"SRCREQ-{i:06d}", "source_file": "requirements.xlsx", "source_sheet": "Sheet1", "source_row": i + 2}
                for i in range(1, 4)
            ],
            "rq_candidates": [
                {"candidate_id": "A", "stable_key": "a", "level1": "L1", "level2": "L2", "name": "A", "source_record_ids": ["SRCREQ-000001"], "external_requirement_ids": ["A1"]},
                {"candidate_id": "B", "stable_key": "b", "level1": "L1", "level2": "L2", "name": "B", "source_record_ids": ["SRCREQ-000002"], "external_requirement_ids": ["B1"]},
                {"candidate_id": "C", "stable_key": "c", "level1": "L1", "level2": "L2", "name": "C", "source_record_ids": ["SRCREQ-000003"], "external_requirement_ids": ["C1"]},
            ],
            "grouping_reviews": [],
            "canonical": {"rq_target_ids": ["RQ-001", "RQ-002", "RQ-022"]},
        }
        manifests = EXPLAIN.build_extraction_manifests(data)
        self.assertEqual({"RQ-001", "RQ-002", "RQ-022"}, set(manifests))
        self.assertTrue(all(not item["auto_merge"] for item in manifests.values()))


if __name__ == "__main__":
    unittest.main()
