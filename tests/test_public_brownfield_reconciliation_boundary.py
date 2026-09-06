import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sdlc/scripts/validate_public_brownfield_pilot.py"
SPEC = importlib.util.spec_from_file_location("public_brownfield_pilot", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)


class FakeAdapter:
    @staticmethod
    def analyze(source_root: Path):
        controller_entry = "entry:com.macro.mall.controller.OmsOrderController#list"
        controller_symbol = "symbol:com.macro.mall.controller.OmsOrderController#list"
        service_impl_symbol = "symbol:com.macro.mall.service.impl.OmsOrderServiceImpl#list"
        mapper_symbol = "mybatis:com.macro.mall.dao.OmsOrderDao#getList"
        order_table = "data:OMS_ORDER"
        return {
            "adapter_id": "FAKE_REAL_REPO_BOUNDARY_TEST",
            "completion_status": "PARTIAL_COVERAGE_GAPS",
            "business_impact_confirmed": False,
            "nodes": [
                {"id": controller_entry},
                {"id": controller_symbol},
                {"id": service_impl_symbol},
                {"id": mapper_symbol},
                {"id": order_table},
            ],
            "edges": [
                {"from": service_impl_symbol, "type": "CALLEE", "to": mapper_symbol},
                {"from": mapper_symbol, "type": "READS", "to": order_table},
            ],
            "coverage_gaps": [
                {"code": "DYNAMIC_DISPATCH_UNSUPPORTED", "dimension": "DYNAMIC_RUNTIME_GAP"}
            ],
        }


class PublicBrownfieldReconciliationBoundaryTest(unittest.TestCase):
    def test_real_source_impact_pass_does_not_become_reconciliation_empirical_pass(self):
        original = MOD._load_adapter
        MOD._load_adapter = lambda: FakeAdapter
        try:
            with tempfile.TemporaryDirectory() as td:
                result = MOD.validate(Path(td), "example/public", "abc123")
        finally:
            MOD._load_adapter = original

        self.assertEqual("PASS_REAL_REPOSITORY_PARTIAL_COVERAGE", result["verdict"])
        self.assertFalse(result["business_impact_confirmed"])
        reconciliation = result["reconciliation"]
        self.assertEqual("NOT_RUN", reconciliation["execution_status"])
        self.assertEqual("WAITING_BUSINESS_AUTHORITY", reconciliation["readiness"])
        self.assertTrue(reconciliation["source_evidence_observed"])
        self.assertEqual("CURRENT_SOURCE_DB_CONFIG_RUNTIME_EVIDENCE", reconciliation["source_evidence_class"])
        self.assertFalse(reconciliation["confirmed_human_business_truth_present"])
        self.assertFalse(reconciliation["reviewer_decision_present"])
        self.assertFalse(reconciliation["business_truth_auto_rewritten"])
        self.assertFalse(reconciliation["empirical_reconciliation_pass"])
        self.assertIn("CONFIRMED_HUMAN_BUSINESS_TRUTH", reconciliation["required_next_evidence"])
        self.assertFalse(result["safety"]["public_source_only_is_reconciliation_pass"])


if __name__ == "__main__":
    unittest.main()
