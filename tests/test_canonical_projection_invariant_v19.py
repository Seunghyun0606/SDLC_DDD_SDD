import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "sdlc/scripts/validate_canonical_projection_invariant.py"
FIXTURE = ROOT / "framework/samples/tailoring/comparison-canonical.example.json"

spec = importlib.util.spec_from_file_location("canonical_projection_invariant_tested", SCRIPT)
validator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


class CanonicalProjectionInvariantV110Test(unittest.TestCase):
    def test_change_level_keeps_canonical_and_audience_topologies_are_independent(self):
        store = json.loads(FIXTURE.read_text(encoding="utf-8"))
        before = json.dumps(store, ensure_ascii=False, sort_keys=True)
        result = validator.validate(ROOT, store=store, target="RQ-COMP-001")

        self.assertTrue(result["invariant_pass"])
        self.assertTrue(result["canonical_change_level_invariant"])
        self.assertTrue(result["canonical_store_unchanged_by_projection_resolution"])
        self.assertTrue(result["engineering_topology_independent_from_customer"])
        self.assertTrue(result["customer_topology_independent_from_engineering"])
        self.assertTrue(result["fixed_artifact_count_is_not_an_invariant"])
        self.assertFalse(result["customer_business_truth_authority"])
        self.assertEqual(["L1", "L2", "L3", "L4", "L5"], result["change_levels"])
        self.assertEqual(before, json.dumps(store, ensure_ascii=False, sort_keys=True))

        engineering_counts = {
            row["engineering_layer"]["artifact_count"] for row in result["profile_matrix"]
        }
        customer_counts = {
            row["customer_layer"]["artifact_count"] for row in result["profile_matrix"]
        }
        self.assertGreater(len(engineering_counts), 1)
        self.assertGreater(len(customer_counts), 1)
        self.assertIn(3, customer_counts)
        self.assertIn(8, customer_counts)

        customer_standard_sets = {
            tuple(row["customer_layer"]["artifact_ids"])
            for row in result["profile_matrix"]
            if row["customer_profile"] == "CUSTOMER_STANDARD_3"
        }
        self.assertEqual(1, len(customer_standard_sets))

        engineering_compact_sets = {
            tuple(row["engineering_layer"]["artifact_ids"])
            for row in result["profile_matrix"]
            if row["engineering_profile"] == "ENGINEERING_SDD_COMPACT"
        }
        self.assertEqual(1, len(engineering_compact_sets))

    def test_cli_materializes_independence_report(self):
        with tempfile.TemporaryDirectory() as td:
            out_json = Path(td) / "canonical-projection-invariant.json"
            out_md = Path(td) / "canonical-projection-invariant.md"
            cp = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--root", str(ROOT),
                    "--store", str(FIXTURE),
                    "--target", "RQ-COMP-001",
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
            self.assertTrue(summary["engineering_customer_independent"])
            self.assertTrue(summary["customer_engineering_independent"])

            machine = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertTrue(machine["invariant_pass"])
            human = out_md.read_text(encoding="utf-8")
            self.assertIn("Engineering / Customer Projection 불변성", human)
            self.assertIn("Fixed document count is NOT invariant", human)
            self.assertIn("Business Truth 권위를 갖지 않는다", human)


if __name__ == "__main__":
    unittest.main()
