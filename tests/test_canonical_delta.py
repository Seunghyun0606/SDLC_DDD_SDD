import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "sdlc/scripts/apply_canonical_delta.py"
SPEC = importlib.util.spec_from_file_location("apply_canonical_delta", SCRIPT)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MOD)


def entity_op(entity_id="RQ-001", *, entity_type="RQ", fields=None, evidence="GIVEN", truth="CANDIDATE"):
    return {
        "op": "UPSERT_ENTITY",
        "id": entity_id,
        "entity_type": entity_type,
        "fields": fields or {"name": "요구사항"},
        "evidence_class": evidence,
        "truth_status": truth,
    }


def delta(delta_id="DELTA-001", *, base_revision=0, stage="DECOMPOSE", operations=None):
    return {
        "schema_version": 1,
        "delta_id": delta_id,
        "base_revision": base_revision,
        "stage": stage,
        "source_artifact": "docs/example.md",
        "operations": operations or [entity_op()],
    }


class CanonicalDeltaBehaviorTest(unittest.TestCase):
    def test_first_delta_creates_store_revision_and_entity(self):
        result, store = MOD.apply_delta(MOD.empty_store(), delta())
        self.assertEqual("APPLIED", result["status"])
        self.assertEqual(1, store["revision"])
        self.assertEqual("요구사항", store["entities"]["RQ-001"]["fields"]["name"])
        self.assertEqual("DELTA-001", store["applied_deltas"][0]["delta_id"])

    def test_same_delta_id_is_idempotent_even_after_revision_changes(self):
        _, store = MOD.apply_delta(MOD.empty_store(), delta())
        before = copy.deepcopy(store)
        replay = delta(base_revision=0)
        result, after = MOD.apply_delta(store, replay)
        self.assertEqual("IDEMPOTENT", result["status"])
        self.assertEqual(before, after)

    def test_stale_base_revision_conflicts_without_mutation(self):
        _, store = MOD.apply_delta(MOD.empty_store(), delta())
        before = copy.deepcopy(store)
        result, after = MOD.apply_delta(store, delta("DELTA-002", base_revision=0))
        self.assertEqual("CONFLICT", result["status"])
        self.assertEqual("STALE_BASE_REVISION", result["conflicts"][0]["code"])
        self.assertEqual(before, after)

    def test_relation_can_precede_entity_operations_in_delta(self):
        ops = [
            {"op":"UPSERT_RELATION","from":"RQ-001","kind":"DECOMPOSES_TO","to":"FR-001","evidence_class":"GIVEN"},
            entity_op("FR-001", entity_type="FR", fields={"name":"기능"}),
            entity_op("RQ-001"),
        ]
        result, store = MOD.apply_delta(MOD.empty_store(), delta(operations=ops))
        self.assertEqual("APPLIED", result["status"])
        self.assertEqual(1, len(store["relations"]))
        self.assertEqual(("RQ-001","DECOMPOSES_TO","FR-001"), MOD._relation_key(store["relations"][0]))

    def test_missing_relation_endpoint_fails_all_or_nothing(self):
        ops = [
            entity_op("RQ-001"),
            {"op":"UPSERT_RELATION","from":"RQ-001","kind":"DECOMPOSES_TO","to":"FR-MISSING","evidence_class":"GIVEN"},
        ]
        original = MOD.empty_store()
        result, store = MOD.apply_delta(original, delta(operations=ops))
        self.assertEqual("CONFLICT", result["status"])
        self.assertEqual("MISSING_RELATION_ENDPOINT", result["conflicts"][0]["code"])
        self.assertEqual(original, store)
        self.assertNotIn("RQ-001", store["entities"])

    def test_entity_type_mismatch_fails_without_partial_update(self):
        _, store = MOD.apply_delta(MOD.empty_store(), delta())
        before = copy.deepcopy(store)
        bad = delta("DELTA-002", base_revision=1, operations=[entity_op("RQ-001", entity_type="FR")])
        result, after = MOD.apply_delta(store, bad)
        self.assertEqual("CONFLICT", result["status"])
        self.assertEqual("ENTITY_TYPE_MISMATCH", result["conflicts"][0]["code"])
        self.assertEqual(before, after)

    def test_source_evidence_cannot_overwrite_confirmed_business_fields(self):
        confirmed = delta(operations=[entity_op(
            "BR-001", entity_type="BR", fields={"rule":"승인 후 저장"}, evidence="CONFIRMED", truth="CONFIRMED_BUSINESS"
        )])
        _, store = MOD.apply_delta(MOD.empty_store(), confirmed)
        observed = delta("DELTA-002", base_revision=1, stage="DISCOVERY", operations=[entity_op(
            "BR-001", entity_type="BR", fields={"rule":"즉시 저장"}, evidence="OBSERVED", truth="OBSERVED_AS_IS"
        )])
        result, after = MOD.apply_delta(store, observed)
        self.assertEqual("CONFLICT", result["status"])
        self.assertEqual("BUSINESS_TRUTH_OVERWRITE_BLOCKED", result["conflicts"][0]["code"])
        self.assertEqual("승인 후 저장", after["entities"]["BR-001"]["fields"]["rule"])
        self.assertEqual("CONFIRMED_BUSINESS", after["entities"]["BR-001"]["truth_status"])

    def test_source_evidence_cannot_downgrade_confirmed_business_status_only(self):
        confirmed = delta(operations=[entity_op(
            "BR-001", entity_type="BR", fields={"rule":"승인 후 저장"}, evidence="CONFIRMED", truth="CONFIRMED_BUSINESS"
        )])
        _, store = MOD.apply_delta(MOD.empty_store(), confirmed)
        observed_same_value = delta("DELTA-002", base_revision=1, stage="DISCOVERY", operations=[entity_op(
            "BR-001", entity_type="BR", fields={"rule":"승인 후 저장"}, evidence="OBSERVED", truth="OBSERVED_AS_IS"
        )])
        result, after = MOD.apply_delta(store, observed_same_value)
        self.assertEqual("CONFLICT", result["status"])
        self.assertEqual("BUSINESS_TRUTH_STATUS_DOWNGRADE_BLOCKED", result["conflicts"][0]["code"])
        self.assertEqual("CONFIRMED_BUSINESS", after["entities"]["BR-001"]["truth_status"])

    def test_add_provenance_can_attach_observation_without_changing_business_truth(self):
        confirmed = delta(operations=[entity_op(
            "BR-001", entity_type="BR", fields={"rule":"승인 후 저장"}, evidence="CONFIRMED", truth="CONFIRMED_BUSINESS"
        )])
        _, store = MOD.apply_delta(MOD.empty_store(), confirmed)
        provenance = delta("DELTA-002", base_revision=1, stage="DISCOVERY", operations=[{
            "op":"ADD_PROVENANCE",
            "id":"BR-001",
            "evidence_class":"OBSERVED",
            "locator":"src/RuleService.java#save",
            "source_hash":"sha256:abc",
            "note":"현행 Source에서 관찰됨",
        }])
        result, after = MOD.apply_delta(store, provenance)
        self.assertEqual("APPLIED", result["status"])
        entity = after["entities"]["BR-001"]
        self.assertEqual("CONFIRMED_BUSINESS", entity["truth_status"])
        self.assertEqual("승인 후 저장", entity["fields"]["rule"])
        self.assertEqual(2, len(entity["provenance"]))

    def test_confirmed_business_requires_confirmed_evidence(self):
        bad = delta(operations=[entity_op(
            "BR-001", entity_type="BR", evidence="OBSERVED", truth="CONFIRMED_BUSINESS"
        )])
        result, store = MOD.apply_delta(MOD.empty_store(), bad)
        self.assertEqual("INVALID_DELTA", result["status"])
        self.assertEqual("BUSINESS_CONFIRMATION_REQUIRES_CONFIRMED_EVIDENCE", result["errors"][0]["code"])
        self.assertEqual(MOD.empty_store(), store)

    def test_delete_is_intentionally_unsupported(self):
        bad = delta(operations=[{
            "op":"DELETE_ENTITY","id":"RQ-001","evidence_class":"CONFIRMED"
        }])
        result, store = MOD.apply_delta(MOD.empty_store(), bad)
        self.assertEqual("INVALID_DELTA", result["status"])
        self.assertEqual("UNSUPPORTED_OPERATION", result["errors"][0]["code"])
        self.assertEqual(MOD.empty_store(), store)

    def test_cli_dry_run_does_not_write_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            delta_path = root / "delta.json"
            store_path = root / "store.json"
            result_path = root / "result.json"
            delta_path.write_text(json.dumps(delta(), ensure_ascii=False), encoding="utf-8")
            rc = MOD.main([
                "--store", str(store_path),
                "--delta", str(delta_path),
                "--result-out", str(result_path),
                "--dry-run",
            ])
            self.assertEqual(0, rc)
            self.assertFalse(store_path.exists())
            result = json.loads(result_path.read_text(encoding="utf-8"))
            self.assertTrue(result["dry_run"])
            self.assertFalse(result["store_written"])


if __name__ == "__main__":
    unittest.main()
