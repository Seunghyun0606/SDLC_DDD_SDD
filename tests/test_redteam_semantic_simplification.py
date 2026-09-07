import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


EXEC = load("redteam_exec", "sdlc/scripts/change_execution_runtime.py")
PROGRAM = load("redteam_program", "sdlc/scripts/validate_program_spec.py")
COMPONENT = load("redteam_component", "sdlc/scripts/component_state_runtime.py")
IMPACT = load("redteam_impact", "sdlc/scripts/impact_learning_runtime.py")
DISCOVERY = load("redteam_discovery", "sdlc/scripts/unexpected_discovery_runtime.py")
PROJECTION = load("redteam_projection", "sdlc/scripts/projection_lifecycle_runtime.py")
DELIVERY = load("redteam_delivery", "sdlc/scripts/delivery_status_runtime.py")
ARCH = load("redteam_arch", "sdlc/scripts/architecture_check.py")
SCAFFOLD = load("redteam_scaffold", "sdlc/scripts/build_project_scaffold.py")
METRICS = load("redteam_metrics", "sdlc/scripts/sdlc_metrics_runtime.py")


class RedTeamSemanticSimplificationTest(unittest.TestCase):
    def test_l1_is_real_semantic_fast_path_not_all_stage_chain(self):
        state = {
            "effective_change_level": "L1",
            "typed_facts": {
                "HAS_INTERFACE": "NO", "HAS_BATCH": "NO", "IMPACT_COVERAGE": "COMPLETE",
                "CROSS_DOMAIN_COUNT": 0, "PROCESS_COMPLEXITY": "LOW",
            },
        }
        plan = EXEC.resolve_execution_plan(ROOT, state)
        self.assertTrue(plan["fast_path"])
        self.assertEqual("DEVELOPMENT", plan["default_entry_stage"])
        self.assertEqual(
            [
                "INTENT_DECOMPOSITION",
                "AS_IS_SOURCE_ANALYSIS",
                "IMPACT_SANITY_CHECK",
                "IMPLEMENTATION_DELTA",
                "SOURCE_CHANGE",
                "TEST",
                "RECONCILE",
            ],
            plan["required_semantic_work"],
        )
        self.assertEqual(
            ["INTENT_DECOMPOSED", "AS_IS_SOURCE_ANALYZED", "IMPACT_CHECKED"],
            plan["source_write_preconditions"],
        )
        for heavy in ["DECOMPOSE", "CLARIFY", "PROCESS", "DISCOVERY", "DESIGN", "PROGRAM"]:
            self.assertNotIn(heavy, plan["required_semantic_work"])
        self.assertEqual("CORE_ONLY", plan["program_spec_mode"])
        self.assertEqual("OFF", plan["bpmn_policy"])

    def test_free_text_security_negation_is_candidate_only_not_level_fact(self):
        store = {
            "entities": {
                "RQ-001": {
                    "entity_type": "RQ",
                    "fields": {
                        "description": "라벨 변경. 보안 영향 없음.",
                        "change_facts": {"HAS_INTERFACE": "NO", "HAS_BATCH": "NO", "IMPACT_COVERAGE": "COMPLETE"},
                    },
                }
            },
            "relations": [],
        }
        evidence = EXEC.derive_typed_facts(store, "RQ-001", {})
        result = EXEC.classify_typed_facts(evidence)
        self.assertEqual("L1", result["level"])
        self.assertEqual("NONE", result["typed_facts"]["SECURITY_IMPACT"])
        self.assertFalse(result["free_text_used_for_final_level"])
        self.assertIn("SECURITY_IMPACT:NEGATED_TEXT_CANDIDATE", result["candidate_hints"])

        evidence["facts"]["SECURITY_IMPACT"] = "MATERIAL"
        elevated = EXEC.classify_typed_facts(evidence)
        self.assertIn(elevated["level"], {"L4", "L5"})

    def test_unknown_critical_facts_cannot_be_auto_l1(self):
        result = EXEC.classify_typed_facts({"facts": dict(EXEC.FACT_DEFAULTS), "evidence_refs": []})
        self.assertEqual("L2", result["level"])
        self.assertTrue(set(result["uncertainty"]) & {"HAS_INTERFACE", "HAS_BATCH", "IMPACT_COVERAGE"})
        self.assertTrue(any("SAFETY_FLOOR" in x for x in result["classification_reason"]))

    def test_program_spec_is_six_core_plus_only_triggered_risks(self):
        cfg = json.loads((ROOT / "sdlc/config/program-spec-readiness.json").read_text(encoding="utf-8"))
        core = PROGRAM.required_fields(cfg, "STANDARD", "L1", {"HAS_INTERFACE": "NO", "TRANSACTION_IMPACT": "NONE"})
        self.assertEqual(6, len(core))
        ids = {x["id"] for x in core}
        self.assertNotIn("transaction", ids)
        self.assertNotIn("integration", ids)
        triggered = PROGRAM.required_fields(cfg, "STANDARD", "L2", {"HAS_INTERFACE": "YES", "TRANSACTION_IMPACT": "MATERIAL", "SECURITY_IMPACT": "MATERIAL"})
        triggered_ids = {x["id"] for x in triggered}
        self.assertTrue({"transaction", "integration", "security"} <= triggered_ids)
        legacy = PROGRAM.required_fields(cfg, "LEGACY_FULL_17", "L3", {})
        self.assertEqual(17, len(legacy))

    def test_component_baseline_accepted_deltas_release_and_conflict_reconstruct_current(self):
        data = {"schema_version": 1, "backend": "JSON", "components": {}, "releases": {}}
        COMPONENT.register_release(data, "R1", 1)
        COMPONENT.register_release(data, "R2", 2)
        COMPONENT.register_baseline(data, "PGM-A", 1, {"rule": {"minutes": 60}, "label": "A"})
        first = COMPONENT.append_delta(data, "PGM-A", change_id="CR-001", base_revision=1, operations=[{"op":"SET","path":"rule.minutes","value":30}], release="R1")
        self.assertEqual("DELTA_RECORDED", first["status"])
        second = COMPONENT.append_delta(data, "PGM-A", change_id="CR-017", base_revision=2, operations=[{"op":"SET","path":"label","value":"B"}], release="R2")
        self.assertEqual("DELTA_RECORDED", second["status"])
        current = COMPONENT.reconstruct(data, "PGM-A", "R2")
        self.assertEqual(30, current["state"]["rule"]["minutes"])
        self.assertEqual("B", current["state"]["label"])
        self.assertEqual(["CR-001", "CR-017"], current["applied_changes"])
        self.assertFalse(current["business_truth_authority"])
        conflict = COMPONENT.append_delta(data, "PGM-A", change_id="CR-CONCURRENT", base_revision=1, operations=[{"op":"SET","path":"label","value":"C"}], release="R2")
        self.assertEqual("CONFLICT", conflict["status"])
        self.assertTrue(conflict["current_state_preserved"])
        before = COMPONENT.reconstruct(data, "PGM-A", "R2")["state"]
        compacted = COMPONENT.compact(data, "PGM-A", "R2")
        self.assertEqual("COMPACTED", compacted["status"])
        self.assertEqual(before, COMPONENT.reconstruct(data, "PGM-A", "R2")["state"])

    def test_historical_unexpected_discovery_is_future_candidate_not_truth(self):
        store = {"schema_version": 1, "records": []}
        row = IMPACT.record_change(
            store, change_id="RQ-041", target_id="RQ-041", keys=["OVERTIME_MIN_UNIT"],
            predicted=["TAM3100", "TAM3200"], actual=["TAM3100", "TAM3200", "ATT_CLOSE_BATCH"],
        )
        self.assertEqual(["ATT_CLOSE_BATCH"], row["unexpected_discovery"])
        m = IMPACT.metrics(row)
        self.assertLess(m["impact_recall"], 1.0)
        candidates = IMPACT.recommend(store, ["OVERTIME_MIN_UNIT"], limit=100)
        batch = next(x for x in candidates if x["component_id"] == "ATT_CLOSE_BATCH")
        self.assertEqual("HISTORICAL_IMPACT_CANDIDATE", batch["status"])
        self.assertFalse(batch["confirmed_current_impact"])
        self.assertTrue(batch["requires_current_evidence"])
        self.assertLessEqual(len(candidates), 10)

    def test_one_discovery_action_expands_scope_escalates_and_marks_reconcile_required(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store_path = root / "sdlc/canonical/store.json"
            store_path.parent.mkdir(parents=True, exist_ok=True)
            store_path.write_text(json.dumps({"revision":1,"entities":{"RQ-041":{"entity_type":"RQ","fields":{"change_facts":{"HAS_INTERFACE":"NO","HAS_BATCH":"NO","IMPACT_COVERAGE":"COMPLETE"}}}},"relations":[]}), encoding="utf-8")
            proj = PROJECTION.register_generated(root, target="RQ-041", artifact_id="A02", artifact_path="docs/A02.md", audience="CUSTOMER")
            self.assertEqual("PENDING_REVIEW", proj["lifecycle"])
            result = DISCOVERY.capture(root, target="RQ-041", component="ATT_CLOSE_BATCH", keys=["OVERTIME_MIN_UNIT"])
            self.assertEqual("UNEXPECTED_DISCOVERY_REFRESHED", result["status"])
            self.assertTrue(result["execution_policy"]["change_level"] in {"L2","L3","L4","L5"})
            self.assertEqual(1, result["projection_stale_count"])
            test_scope = json.loads((root / result["test_scope"]).read_text(encoding="utf-8"))
            self.assertIn("ATT_CLOSE_BATCH", test_scope["components"])
            self.assertTrue(test_scope["regression_expansion_required"])
            reconcile = json.loads((root / result["reconciliation"]).read_text(encoding="utf-8"))
            self.assertEqual("CHECK_REQUIRED", reconcile["status"])
            self.assertFalse(reconcile["business_truth_auto_rewritten"])
            self.assertFalse(result["canonical_business_truth_mutated"])
            self.assertFalse(result["as_built_mutated"])

    def test_customer_projection_lifecycle_is_stale_regenerate_review_current(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); store_path = root / "sdlc/canonical/store.json"; store_path.parent.mkdir(parents=True, exist_ok=True)
            store_path.write_text(json.dumps({"revision":1,"entities":{},"relations":[]}), encoding="utf-8")
            PROJECTION.register_generated(root, target="RQ-1", artifact_id="A01", artifact_path="docs/A01.md", audience="CUSTOMER")
            self.assertEqual("PENDING_REVIEW", PROJECTION.affected(root, "RQ-1")[0]["state"])
            store_path.write_text(json.dumps({"revision":2,"entities":{},"relations":[]}), encoding="utf-8")
            self.assertEqual("STALE_VIEW", PROJECTION.affected(root, "RQ-1")[0]["state"])
            stale_review = PROJECTION.review(root, target="RQ-1", artifact_id="A01", reviewer="CUST-01", accepted=True)
            self.assertEqual("STALE_VIEW", stale_review["status"])
            PROJECTION.register_generated(root, target="RQ-1", artifact_id="A01", artifact_path="docs/A01.md", audience="CUSTOMER")
            decision = PROJECTION.review(root, target="RQ-1", artifact_id="A01", reviewer="CUST-01", accepted=False, business_policy_edit="업무 정책 수정 제안")
            self.assertEqual("DECISION_REQUIRED", decision["status"])
            self.assertFalse(decision["canonical_mutated"])
            PROJECTION.register_generated(root, target="RQ-1", artifact_id="A01", artifact_path="docs/A01.md", audience="CUSTOMER")
            accepted = PROJECTION.review(root, target="RQ-1", artifact_id="A01", reviewer="CUST-01", accepted=True)
            self.assertEqual("CURRENT", accepted["status"])

    def test_delivery_status_never_infers_customer_acceptance_from_technical_verify(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            DELIVERY.record(root, "RQ-1", "DEVELOPMENT_STARTED", None)
            DELIVERY.record(root, "RQ-1", "TECHNICAL_VERIFICATION_PASSED", "verify:run-1")
            snap = DELIVERY.snapshot(root, "RQ-1")
            self.assertTrue(snap["technical_verification_passed"])
            self.assertEqual("PENDING", snap["customer_acceptance"])
            DELIVERY.record(root, "RQ-1", "CUSTOMER_ACCEPTED", "acceptance:decision-1")
            self.assertEqual("ACCEPTED", DELIVERY.snapshot(root, "RQ-1")["customer_acceptance"])

    def test_architecture_rule_poc_detects_direct_mail_usage(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); bad = root / "src/main/java/app/MailJob.java"; bad.parent.mkdir(parents=True, exist_ok=True); bad.write_text("class MailJob { JavaMailSender sender; }", encoding="utf-8")
            cfg = json.loads((ROOT / "sdlc/config/architecture-rules.json").read_text(encoding="utf-8"))
            result = ARCH.check(root, cfg, ["src/main/java"])
            self.assertEqual("ARCH_VIOLATION", result["status"])
            self.assertTrue(any(x["rule_id"] == "COMMON_MAIL_ONLY" for x in result["violations"]))
            self.assertFalse(result["business_truth_mutated"])

    def test_project_scaffold_excludes_framework_dev_and_legacy_full_by_default(self):
        files = SCAFFOLD.select_files(ROOT)
        self.assertIn("sdlc/scripts/change_execution_runtime.py", files)
        self.assertIn("sdlc/config/change-execution-policy.json", files)
        self.assertNotIn("sdlc/tailoring/standard/STAGE_ORIENTED_FULL.yaml", files)
        forbidden = ["docs/99_파일럿/", "sdlc/validation/", "sdlc/samples/", "tests/", ".github/"]
        self.assertFalse(any(any(x.startswith(prefix) for prefix in forbidden) for x in files))
        legacy = SCAFFOLD.select_files(ROOT, include_legacy_compatibility=True)
        self.assertIn("sdlc/tailoring/standard/STAGE_ORIENTED_FULL.yaml", legacy)

    def test_roi_metrics_never_claim_pass_without_observations(self):
        incomplete = METRICS.summarize({"run_id":"A","case":"CASE_A_L1_LOCAL","target":"RQ-1","metrics":{}})
        self.assertEqual("INSUFFICIENT_EVIDENCE", incomplete["measurement_status"])
        self.assertIsNone(incomplete["empirical_pass"])
        complete = METRICS.summarize({
            "run_id":"A","case":"CASE_A_L1_LOCAL","target":"RQ-1","metrics":{
                "total_elapsed_minutes":11,"baseline_elapsed_minutes":10,"framework_command_count":1,"generated_artifact_count":1,
                "human_review_minutes":1,"human_edit_minutes":0.5,"coding_start_latency_minutes":1,"unsupported_ai_fact_count":0
            }
        })
        self.assertEqual("COMPLETE", complete["measurement_status"])
        self.assertAlmostEqual(0.1, complete["framework_overhead_ratio"])
        self.assertIsNone(complete["empirical_pass"])


if __name__ == "__main__": unittest.main()
