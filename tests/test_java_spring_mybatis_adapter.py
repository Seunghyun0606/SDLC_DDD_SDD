import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sdlc/custom/project/adapters/impact/java_spring_mybatis.py"
FIXTURE = ROOT / "sdlc/validation/pilot/source-fixture/as-is"
CONTRACT = json.loads((ROOT / "sdlc/design/contracts/brownfield-impact-contract.json").read_text(encoding="utf-8"))
SPEC = importlib.util.spec_from_file_location("java_spring_mybatis", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)


class JavaSpringMyBatisAdapterPilotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = MOD.analyze(FIXTURE)
        cls.nodes = {row["id"]: row for row in cls.result["nodes"]}
        cls.edges = {(row["from"], row["type"], row["to"]): row for row in cls.result["edges"]}

    def test_output_satisfies_core_adapter_required_shape(self):
        result = self.result
        required = CONTRACT["adapter_output_contract"]["required"]
        self.assertTrue(set(required).issubset(result))
        for node in result["nodes"]:
            self.assertTrue(set(CONTRACT["adapter_output_contract"]["node_required"]).issubset(node))
        for edge in result["edges"]:
            self.assertTrue(set(CONTRACT["adapter_output_contract"]["edge_required"]).issubset(edge))
        for coverage in result["coverage"]:
            self.assertTrue(set(CONTRACT["adapter_output_contract"]["coverage_required"]).issubset(coverage))

    def test_controller_methods_are_entry_candidates_not_confirmed_spring_mappings(self):
        for method in ["getPlan", "savePlan"]:
            node = self.nodes[f"entry:com.acme.tm.FlexibleWorkPlanController#{method}"]
            self.assertEqual("ENTRY_POINT", node["type"])
            self.assertEqual("MEDIUM", node["confidence"])
            self.assertEqual("CHECK_REQUIRED", node["status"])
        gaps = {row["code"] for row in self.result["coverage_gaps"]}
        self.assertIn("SPRING_MAPPING_ANNOTATION_NOT_FOUND", gaps)

    def test_java_direct_calls_link_controller_service_and_mapper(self):
        expected = [
            (
                "symbol:com.acme.tm.FlexibleWorkPlanController#getPlan",
                "CALLEE",
                "symbol:com.acme.tm.FlexibleWorkPlanService#getPlan",
            ),
            (
                "symbol:com.acme.tm.FlexibleWorkPlanController#savePlan",
                "CALLEE",
                "symbol:com.acme.tm.FlexibleWorkPlanService#savePlan",
            ),
            (
                "symbol:com.acme.tm.FlexibleWorkPlanService#getPlan",
                "CALLEE",
                "mybatis:com.acme.tm.FlexibleWorkPlanMapper#selectPlan",
            ),
            (
                "symbol:com.acme.tm.FlexibleWorkPlanService#savePlan",
                "CALLEE",
                "mybatis:com.acme.tm.FlexibleWorkPlanMapper#upsertPlan",
            ),
        ]
        for key in expected:
            self.assertIn(key, self.edges)
            reverse = (key[2], "CALLER", key[0])
            self.assertIn(reverse, self.edges)

    def test_mybatis_select_and_merge_produce_table_lineage(self):
        self.assertIn("data:TB_TM_FLEX_PLAN", self.nodes)
        self.assertIn("data:TB_TM_DEFAULT_SCHEDULE", self.nodes)
        self.assertIn((
            "mybatis:com.acme.tm.FlexibleWorkPlanMapper#selectPlan",
            "READS",
            "data:TB_TM_FLEX_PLAN",
        ), self.edges)
        self.assertIn((
            "mybatis:com.acme.tm.FlexibleWorkPlanMapper#selectDefaultSchedule",
            "READS",
            "data:TB_TM_DEFAULT_SCHEDULE",
        ), self.edges)
        merge = "mybatis:com.acme.tm.FlexibleWorkPlanMapper#upsertPlan"
        self.assertIn((merge, "READS", "data:TB_TM_FLEX_PLAN"), self.edges)
        self.assertIn((merge, "WRITES", "data:TB_TM_FLEX_PLAN"), self.edges)
        self.assertNotIn("data:DUAL", self.nodes)

    def test_schema_assets_use_schema_locator_when_available(self):
        flex = self.nodes["data:TB_TM_FLEX_PLAN"]
        default = self.nodes["data:TB_TM_DEFAULT_SCHEDULE"]
        self.assertTrue(flex["locator"].startswith("db/schema.sql#"))
        self.assertTrue(default["locator"].startswith("db/schema.sql#"))
        self.assertEqual("HIGH", flex["confidence"])
        self.assertEqual("OBSERVED", flex["status"])

    def test_all_core_coverage_dimensions_are_reported(self):
        dimensions = [row["dimension"] for row in self.result["coverage"]]
        self.assertEqual(CONTRACT["core_responsibility"]["coverage_dimensions"], dimensions)
        by_dimension = {row["dimension"]: row for row in self.result["coverage"]}
        self.assertEqual("PARTIAL", by_dimension["ENTRY_POINT"]["status"])
        self.assertEqual("COVERED", by_dimension["CALLER"]["status"])
        self.assertEqual("COVERED", by_dimension["CALLEE"]["status"])
        self.assertEqual("COVERED", by_dimension["DATA_READ_WRITE"]["status"])
        self.assertEqual("GAP", by_dimension["DYNAMIC_RUNTIME_GAP"]["status"])

    def test_adapter_never_claims_complete_or_business_confirmation_on_fixture(self):
        self.assertEqual("PARTIAL_COVERAGE_GAPS", self.result["completion_status"])
        self.assertFalse(self.result["business_impact_confirmed"])
        gap_dimensions = {row["dimension"] for row in self.result["coverage_gaps"]}
        for dimension in ["TRANSACTION", "EXTERNAL_INTERFACE", "EVENT", "CONFIG_FEATURE_FLAG", "DYNAMIC_RUNTIME_GAP"]:
            self.assertIn(dimension, gap_dimensions)
        unsupported = {row["pattern"] for row in self.result["unsupported_patterns"]}
        self.assertIn("reflection_dynamic_dispatch", unsupported)
        self.assertIn("spring_proxy_runtime_wiring", unsupported)

    def test_output_is_deterministic_for_same_source_tree(self):
        second = MOD.analyze(FIXTURE)
        self.assertEqual(self.result, second)

    def test_explicit_mapping_annotation_promotes_entry_point_to_observed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "src/main/java/com/acme/DemoController.java"
            src.parent.mkdir(parents=True)
            src.write_text(
                "package com.acme;\n"
                "public class DemoController {\n"
                "  @GetMapping(\"/demo\")\n"
                "  public String getDemo() { return \"ok\"; }\n"
                "}\n",
                encoding="utf-8",
            )
            result = MOD.analyze(root)
            nodes = {row["id"]: row for row in result["nodes"]}
            entry = nodes["entry:com.acme.DemoController#getDemo"]
            self.assertEqual("HIGH", entry["confidence"])
            self.assertEqual("OBSERVED", entry["status"])
            coverage = {row["dimension"]: row for row in result["coverage"]}
            self.assertEqual("COVERED", coverage["ENTRY_POINT"]["status"])

    def test_cli_writes_adapter_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "impact.json"
            rc = MOD.main(["--source-root", str(FIXTURE), "--out", str(out)])
            self.assertEqual(0, rc)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(MOD.ADAPTER_ID, payload["adapter_id"])
            self.assertEqual("PARTIAL_COVERAGE_GAPS", payload["completion_status"])


if __name__ == "__main__":
    unittest.main()
