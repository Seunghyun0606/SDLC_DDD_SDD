import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


APPLY = load_module("p0_apply", ROOT / "sdlc/scripts/apply_canonical_delta.py")
VALIDATOR = load_module("p0_validator", ROOT / "sdlc/scripts/validate_agent_stage_result.py")
WORK = load_module("p0_work", ROOT / "sdlc/scripts/run_work.py")
REVERSE_INPUTS = load_module("p0_reverse_inputs", ROOT / "sdlc/scripts/build_reverse_inputs.py")
GREENFIELD = load_module("p0_greenfield", ROOT / "sdlc/scripts/run_greenfield_e2e_pilot.py")
REPEAT = load_module("p0_repeat", ROOT / "sdlc/scripts/run_work_repeatability_experiment.py")
FIXTURE_PROVIDER = ROOT / "sdlc/validation/providers/deterministic_stage_provider.py"


def entity_op(entity_id="RQ-001", *, entity_type="RQ", fields=None, evidence="GIVEN", truth="CANDIDATE"):
    return {
        "op": "UPSERT_ENTITY",
        "id": entity_id,
        "entity_type": entity_type,
        "fields": fields or {"name": "요구사항"},
        "evidence_class": evidence,
        "truth_status": truth,
    }


def delta(delta_id="DELTA-001", *, base_revision=0, stage="DECOMPOSE", artifact="docs/example.md", operations=None):
    return {
        "schema_version": 1,
        "delta_id": delta_id,
        "base_revision": base_revision,
        "stage": stage,
        "source_artifact": artifact,
        "operations": operations if operations is not None else [entity_op()],
    }


def copy_harness_contract(root: Path):
    target = root / "sdlc/design/contracts/harness-package-contract.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text((ROOT / "sdlc/design/contracts/harness-package-contract.json").read_text(encoding="utf-8"), encoding="utf-8")


def fixture_provider_config():
    return {
        "schema_version": 1,
        "provider_id": "TEST_FIXTURE_PROVIDER",
        "provider_class": "VALIDATION_FIXTURE",
        "enabled": True,
        "timeout_seconds": 30,
        "result_filename": "stage-result.json",
        "command": [
            sys.executable,
            str(FIXTURE_PROVIDER),
            "--context",
            "{context_path}",
            "--result",
            "{result_path}",
        ],
    }


class CanonicalP0HardeningTest(unittest.TestCase):
    def test_given_evidence_cannot_overwrite_confirmed_business(self):
        confirmed = delta(operations=[entity_op(
            "BR-001", entity_type="BR", fields={"rule": "승인 후 저장"}, evidence="CONFIRMED", truth="CONFIRMED_BUSINESS"
        )])
        _, store = APPLY.apply_delta(APPLY.empty_store(), confirmed)
        given_change = delta(
            "DELTA-002",
            base_revision=1,
            operations=[entity_op(
                "BR-001", entity_type="BR", fields={"rule": "즉시 저장"}, evidence="GIVEN", truth="CANDIDATE"
            )],
        )
        result, after = APPLY.apply_delta(store, given_change)
        self.assertEqual("CONFLICT", result["status"])
        self.assertEqual("BUSINESS_TRUTH_OVERWRITE_BLOCKED", result["conflicts"][0]["code"])
        self.assertEqual("승인 후 저장", after["entities"]["BR-001"]["fields"]["rule"])

    def test_same_delta_id_with_different_payload_is_conflict(self):
        _, store = APPLY.apply_delta(APPLY.empty_store(), delta())
        changed = delta()
        changed["operations"][0]["fields"] = {"name": "다른 의미"}
        result, after = APPLY.apply_delta(store, changed)
        self.assertEqual("CONFLICT", result["status"])
        self.assertEqual("DELTA_ID_CONTENT_CONFLICT", result["conflicts"][0]["code"])
        self.assertEqual(store, after)

    def test_same_delta_id_same_semantics_is_idempotent_even_if_base_revision_changes(self):
        original = delta()
        _, store = APPLY.apply_delta(APPLY.empty_store(), original)
        replay = delta(base_revision=999)
        result, after = APPLY.apply_delta(store, replay)
        self.assertEqual("IDEMPOTENT", result["status"])
        self.assertEqual(store, after)

    def test_artifact_only_no_change_is_explicit_and_does_not_increment_revision(self):
        no_change = {
            "schema_version": 1,
            "delta_id": "DOC-ONLY-001",
            "base_revision": 0,
            "stage": "DESIGN",
            "source_artifact": "docs/design.md",
            "operations": [],
            "no_change_reason": "문서 표현만 수정하고 Canonical 의미는 변경하지 않음",
        }
        result, store = APPLY.apply_delta(APPLY.empty_store(), no_change)
        self.assertEqual("NO_CHANGE", result["status"])
        self.assertEqual(0, store["revision"])


class WorkTargetAndStageReentryTest(unittest.TestCase):
    def test_pgm_target_defaults_to_program_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_harness_contract(root)
            store = APPLY.empty_store()
            store["entities"]["PGM-001"] = {
                "id": "PGM-001", "entity_type": "PGM", "fields": {}, "truth_status": "CANDIDATE", "provenance": []
            }
            store_path = root / "canonical.json"
            APPLY.save_store(store_path, store)
            plan = WORK.build_plan(root, target_id="PGM-001", store_path=store_path)
            self.assertEqual("PROGRAM", plan["selection"]["stage"])
            self.assertEqual("TARGET_TYPE_DEFAULT", plan["selection"]["stage_reason"])

    def test_arbitrary_analysis_id_can_use_explicit_design_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_harness_contract(root)
            store_path = root / "canonical.json"
            APPLY.save_store(store_path, APPLY.empty_store())
            plan = WORK.build_plan(root, target_id="ANA001", store_path=store_path, stage="DESIGN")
            self.assertFalse(plan["target"]["canonical_found"])
            self.assertEqual("DESIGN", plan["selection"]["stage"])
            self.assertEqual("USER_STAGE_OVERRIDE", plan["selection"]["stage_reason"])

    def test_rq_target_can_explicitly_reenter_design_document(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_harness_contract(root)
            artifact = root / "docs/design.md"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("---\nstage: DESIGN\n---\n# 기능 설계\nRQ-001\n", encoding="utf-8")
            store = APPLY.empty_store()
            store["entities"]["RQ-001"] = {
                "id": "RQ-001", "entity_type": "RQ", "fields": {}, "truth_status": "CANDIDATE", "provenance": []
            }
            store_path = root / "canonical.json"
            APPLY.save_store(store_path, store)
            plan = WORK.build_plan(
                root,
                target_id="RQ-001",
                store_path=store_path,
                stage="DESIGN",
                artifact="docs/design.md",
            )
            self.assertEqual("DESIGN", plan["selection"]["stage"])
            self.assertEqual("docs/design.md", plan["selection"]["artifact_path"])
            self.assertTrue(plan["selection"]["artifact_override"])

    def test_existing_entities_outside_target_graph_are_blocked(self):
        store = APPLY.empty_store()
        store["entities"]["PGM-001"] = {"id": "PGM-001", "entity_type": "PGM", "fields": {}, "truth_status": "CANDIDATE", "provenance": []}
        store["entities"]["RQ-OTHER"] = {"id": "RQ-OTHER", "entity_type": "RQ", "fields": {}, "truth_status": "CANDIDATE", "provenance": []}
        plan = {
            "canonical": {"allowed_existing_entity_ids": ["PGM-001"]},
            "guards": {"allow_business_truth_change": False},
        }
        errors = WORK.validate_target_scope(plan, delta(operations=[entity_op("RQ-OTHER")]), store)
        self.assertIn("OUTSIDE_TARGET_GRAPH_MUTATION", [row["code"] for row in errors])

    def test_selecting_design_document_does_not_authorize_confirmed_business_change(self):
        store = APPLY.empty_store()
        store["entities"]["BR-001"] = {
            "id": "BR-001",
            "entity_type": "BR",
            "fields": {"rule": "A"},
            "truth_status": "CONFIRMED_BUSINESS",
            "provenance": [],
        }
        plan = {
            "canonical": {"allowed_existing_entity_ids": ["BR-001"]},
            "guards": {"allow_business_truth_change": False},
        }
        change = delta(operations=[entity_op(
            "BR-001", entity_type="BR", fields={"rule": "B"}, evidence="CONFIRMED", truth="CONFIRMED_BUSINESS"
        )])
        errors = WORK.validate_target_scope(plan, change, store)
        self.assertIn("EXPLICIT_BUSINESS_TRUTH_CHANGE_REQUIRED", [row["code"] for row in errors])

    def test_fixture_provider_runs_real_executor_and_no_change_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_harness_contract(root)
            store = APPLY.empty_store()
            store["entities"]["PGM-001"] = {
                "id": "PGM-001",
                "entity_type": "PGM",
                "fields": {"name": "권한 동기화"},
                "truth_status": "CANDIDATE",
                "provenance": [],
            }
            store_path = root / "canonical.json"
            APPLY.save_store(store_path, store)
            plan = WORK.build_plan(
                root,
                target_id="PGM-001",
                store_path=store_path,
                stage="PROGRAM",
                artifact="docs/program.md",
            )
            result = WORK.execute_plan(
                root,
                plan,
                provider_config=fixture_provider_config(),
                run_dir=root / "run",
                store_path=store_path,
            )
            self.assertEqual("NO_CHANGE", result["status"])
            self.assertEqual("PASS", result["validation"]["status"])
            self.assertEqual(0, APPLY.load_store(store_path)["revision"])


class ReverseInputAutomationTest(unittest.TestCase):
    def test_source_manifest_and_artifact_index_are_generated_from_real_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src"
            docs = root / "docs"
            source.mkdir()
            docs.mkdir()
            java = source / "UserPermissionService.java"
            java.write_text("class UserPermissionService {}", encoding="utf-8")
            source_hash = REVERSE_INPUTS._hash_file(java)
            (docs / "program.md").write_text(
                "---\ndocument_type: program_spec\nstage: PROGRAM\nstatus: CURRENT\n---\n"
                f"| src/UserPermissionService.java#save | {source_hash} |\nPGM-001\n",
                encoding="utf-8",
            )
            (docs / "design.md").write_text(
                "---\ndocument_type: functional_design\nstage: DESIGN\nstatus: CURRENT\n---\nPGM-001\n",
                encoding="utf-8",
            )
            store = APPLY.empty_store()
            store["entities"]["PGM-001"] = {
                "id": "PGM-001", "entity_type": "PGM", "fields": {}, "truth_status": "CANDIDATE", "provenance": []
            }
            manifest = REVERSE_INPUTS.build_source_manifest(source, "head")
            index = REVERSE_INPUTS.build_artifact_index(docs, source, store)
            self.assertEqual(1, len(manifest["evidence"]))
            self.assertEqual(2, len(index["artifacts"]))
            self.assertTrue(index["propagation_edges"])
            self.assertEqual("CHECK_REQUIRED", index["propagation_edges"][0]["on_source_drift"])


class ProviderDrivenValidationTest(unittest.TestCase):
    def test_greenfield_e2e_accepts_non_time_domain_without_hardcoded_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_harness_contract(root)
            seed = {
                "schema_version": 1,
                "pilot_id": "SAAS-AUTH-001",
                "mode": "GREENFIELD",
                "external_id": "AUTH-001",
                "requirement_text": "SaaS 사용자 권한 변경 기능이 필요하다.",
            }
            result = GREENFIELD.run(
                root,
                seed,
                fixture_provider_config(),
                runtime_root=root / "runtime/greenfield",
                stages=["DECOMPOSE", "DESIGN", "PROGRAM"],
            )
            self.assertEqual("PASS_EXECUTOR_E2E_FIXTURE_PROVIDER", result["verdict"])
            self.assertFalse(result["actual_agent_provider_executed"])
            self.assertEqual(3, len(result["materialized_artifacts"]))
            combined = "\n".join((root / path).read_text(encoding="utf-8") for path in result["materialized_artifacts"])
            self.assertIn("SaaS 사용자 권한 변경 기능이 필요하다.", combined)
            self.assertNotIn("탄력근로", combined)
            self.assertNotIn("근무계획", combined)

    def test_repeatability_runs_the_real_work_path_but_fixture_never_claims_agent_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            copy_harness_contract(root)
            baseline = APPLY.empty_store()
            baseline["entities"]["RQ-001"] = {
                "id": "RQ-001",
                "entity_type": "RQ",
                "fields": {"original_text": "보험금 청구 심사 기능"},
                "truth_status": "CANDIDATE",
                "provenance": [],
            }
            result = REPEAT.run_experiment(
                root,
                fixture_provider_config(),
                target_id="RQ-001",
                stage="DESIGN",
                artifact="runtime/repeat/design.md",
                baseline_store=baseline,
                run_root=root / "runtime/repeat/runs",
                run_count=3,
            )
            self.assertEqual("PASS_WORK_REPEATABILITY_FIXTURE_PROVIDER", result["verdict"])
            self.assertEqual(1.0, result["semantic_match_rate"])
            self.assertFalse(result["actual_agent_provider_executed"])
            self.assertFalse(result["llm_determinism_proven"])


if __name__ == "__main__":
    unittest.main()
