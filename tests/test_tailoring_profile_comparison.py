import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "sdlc/scripts/generate_tailoring_profile_comparison.py"
FIXTURE = ROOT / "framework/samples/tailoring/comparison-canonical.example.json"
SAMPLE = ROOT / "framework/samples/tailoring/PROFILE_COMPARISON_3_5_FULL.md"

spec = importlib.util.spec_from_file_location("tailoring_profile_comparison_tested", SCRIPT)
comparison = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = comparison
spec.loader.exec_module(comparison)


class TailoringProfileComparisonTest(unittest.TestCase):
    def test_same_canonical_maps_to_three_five_and_ten_document_families(self):
        store = json.loads(FIXTURE.read_text(encoding="utf-8"))
        result = comparison.compare(ROOT, store=store, target="RQ-COMP-001", change_level="L3")

        self.assertTrue(result["structural_invariant_pass"])
        self.assertEqual(7, result["canonical_revision"])
        self.assertEqual(
            "sha256:7a119831c7e436eba7fdcf7992488bc485f32577493ee9770e0158d6e7ede7bf",
            result["canonical_fingerprint"],
        )
        counts = {key: row["unique_artifact_count"] for key, row in result["profiles"].items()}
        self.assertEqual(
            {"STANDARD_3": 3, "STANDARD_5": 5, "STAGE_ORIENTED_FULL": 10},
            counts,
        )
        fingerprints = {row["canonical_fingerprint"] for row in result["profiles"].values()}
        self.assertEqual({result["canonical_fingerprint"]}, fingerprints)
        for row in result["profiles"].values():
            self.assertTrue(row["stage_preserved"])
            self.assertFalse(row["projection_creates_business_truth"])
            self.assertEqual(result["stage_sequence"], row["stage_sequence"])

        standard3 = {row["stage"]: row for row in result["profiles"]["STANDARD_3"]["stage_map"]}
        self.assertEqual("business_definition", standard3["DECOMPOSE"]["primary_artifact"])
        self.assertEqual("detail_design", standard3["DESIGN"]["primary_artifact"])
        self.assertEqual(
            {"detail_design", "screen_design"},
            {item["id"] for item in standard3["DESIGN"]["artifacts"]},
        )
        self.assertIn("별도 Human/Empirical 검증", result["semantic_claim_boundary"])

    def test_cli_generates_machine_and_human_comparison_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            out_json = Path(td) / "comparison.json"
            out_md = Path(td) / "comparison.md"
            cp = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root", str(ROOT),
                    "--store", str(FIXTURE),
                    "--target", "RQ-COMP-001",
                    "--change-level", "L3",
                    "--out-json", str(out_json),
                    "--out-md", str(out_md),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, cp.returncode, cp.stderr + "\n" + cp.stdout)
            summary = json.loads(cp.stdout)
            self.assertEqual("PASS", summary["status"])
            self.assertEqual(
                {"STANDARD_3": 3, "STANDARD_5": 5, "STAGE_ORIENTED_FULL": 10},
                summary["artifact_counts"],
            )
            generated = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertTrue(generated["structural_invariant_pass"])
            markdown = out_md.read_text(encoding="utf-8")
            self.assertIn("Standard 3 / Standard 5 / Full Tailoring 비교 Sample", markdown)
            self.assertIn("실제 Agent 작성 본문의 의미동등성을 주장하지 않는다", markdown)
            committed = SAMPLE.read_text(encoding="utf-8")
            self.assertIn(generated["canonical_fingerprint"], committed)
            self.assertIn("Standard 3 (`STANDARD_3`) | 3", committed)
            self.assertIn("Standard 5 (`STANDARD_5`) | 5", committed)
            self.assertIn("Full (`STAGE_ORIENTED_FULL`) | 10", committed)


if __name__ == "__main__":
    unittest.main()
