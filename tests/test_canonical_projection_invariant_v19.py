import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "sdlc/scripts/validate_canonical_projection_invariant.py"
FIXTURE = ROOT / "sdlc/samples/tailoring/comparison-canonical.example.json"

spec = importlib.util.spec_from_file_location("canonical_projection_invariant_tested", SCRIPT)
validator = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)


class CanonicalProjectionInvariantV19Test(unittest.TestCase):
    def test_l1_to_l5_keep_one_canonical_identity_and_two_projection_layers(self):
        store = json.loads(FIXTURE.read_text(encoding="utf-8"))
        before = json.dumps(store, ensure_ascii=False, sort_keys=True)
        result = validator.validate(ROOT, store=store, target="RQ-COMP-001")

        self.assertTrue(result["invariant_pass"])
        self.assertTrue(result["canonical_change_level_invariant"])
        self.assertTrue(result["canonical_store_unchanged_by_projection_resolution"])
        self.assertTrue(result["developer_projection_topology_invariant"])
        self.assertTrue(result["customer_projection_topology_invariant"])
        self.assertEqual(["L1", "L2", "L3", "L4", "L5"], result["change_levels"])
        self.assertEqual(
            "sha256:53f2b05fff4ca4b2e76c352bfce19cc167b9e1c45692fd340aabeef4059f1154",
            result["canonical_fingerprint"],
        )
        self.assertEqual(before, json.dumps(store, ensure_ascii=False, sort_keys=True))

        developer = result["developer_layer"]
        self.assertEqual("INTERNAL_IT", developer["audience"])
        self.assertEqual(5, developer["artifact_count"])
        self.assertEqual(
            {
                "requirement_definition",
                "process_design",
                "functional_screen_design",
                "program_design",
                "test_acceptance",
            },
            set(developer["artifact_ids"]),
        )
        self.assertEqual(["AGENT_DRAFT_HUMAN_REVIEW"], developer["authoring_modes"])

        customer = result["customer_layer"]
        self.assertEqual("CUSTOMER", customer["audience"])
        self.assertEqual(3, customer["artifact_count"])
        self.assertEqual(
            {"solution_agreement", "delivery_scope", "acceptance_handover"},
            set(customer["artifact_ids"]),
        )
        self.assertEqual(["GENERATED_VIEW"], customer["authoring_modes"])
        self.assertFalse(customer["business_truth_authority"])
        self.assertEqual(
            {"RQ", "FR", "BR", "PROC", "AC", "PGM", "DATA", "TC"},
            set(customer["canonical_selectors"]),
        )

        fingerprints = {row["canonical_fingerprint"] for row in result["levels"]}
        self.assertEqual({result["canonical_fingerprint"]}, fingerprints)
        self.assertEqual(
            {tuple(row["developer_layer"]["artifact_ids"]) for row in result["levels"]},
            {tuple(developer["artifact_ids"])},
        )
        self.assertEqual(
            {tuple(row["customer_layer"]["artifact_ids"]) for row in result["levels"]},
            {tuple(customer["artifact_ids"])},
        )

    def test_cli_materializes_human_readable_layer_report(self):
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
            self.assertEqual(5, summary["developer_artifact_count"])
            self.assertEqual(3, summary["customer_artifact_count"])

            machine = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertTrue(machine["invariant_pass"])
            human = out_md.read_text(encoding="utf-8")
            self.assertIn("Canonical Change Level / Projection 불변성 검증", human)
            self.assertIn("INTERNAL_IT", human)
            self.assertIn("CUSTOMER", human)
            self.assertIn("L1~L5 invariant: `PASS`", human)
            self.assertIn("Business Truth 권위를 갖지 않는다", human)


if __name__ == "__main__":
    unittest.main()
