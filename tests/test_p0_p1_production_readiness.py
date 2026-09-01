import importlib.util
import json
import shutil
import subprocess
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name, rel):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


APPLY = load("rem_apply", "sdlc/scripts/apply_canonical_delta.py")
CONFIG = load("rem_config", "sdlc/scripts/runtime_config.py")
SETUP = load("rem_setup", "sdlc/scripts/bootstrap_project.py")
WORK = load("rem_work", "sdlc/scripts/run_work.py")
CHECK = load("rem_check", "sdlc/scripts/run_check.py")
PROGRAM = load("rem_program", "sdlc/scripts/validate_program_spec.py")
EXTRACT = load("rem_extract", "sdlc/scripts/extract_document_evidence.py")
EXTERNAL = load("rem_external", "sdlc/scripts/normalize_external_evidence.py")
CUSTOMER = load("rem_customer", "sdlc/scripts/capture_customer_decision.py")
KNOWLEDGE = load("rem_knowledge", "sdlc/scripts/run_knowledge_promotion.py")
ENTERPRISE = load("rem_enterprise", "sdlc/custom/project/adapters/impact/java_spring_enterprise.py")


def delta(delta_id, base, entity_id):
    return {
        "schema_version": 1,
        "delta_id": delta_id,
        "base_revision": base,
        "stage": "DECOMPOSE",
        "source_artifact": "docs/req.md",
        "operations": [{
            "op": "UPSERT_ENTITY",
            "id": entity_id,
            "entity_type": "RQ",
            "fields": {"name": entity_id},
            "evidence_class": "GIVEN",
            "truth_status": "CANDIDATE",
        }],
    }


class BootstrapAndProfileTest(unittest.TestCase):
    def test_empty_git_style_project_is_greenfield_not_python_harness(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            detected = SETUP._detect(root)
            self.assertEqual("GREENFIELD", detected["detected_mode"])
            self.assertEqual("OPEN", detected["language"])

    def test_bootstrap_writes_parseable_minimum_profiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = SETUP.bootstrap(root, name="green", mode="GREENFIELD", delivery="FAST", validate=False)
            self.assertEqual("CONFIGURED_PROVIDER_REQUIRED", result["status"])
            project = CONFIG.load_config(root / "sdlc/config/project-profile.yaml")
            source = CONFIG.load_config(root / "sdlc/config/source-profile.yaml")
            self.assertEqual("GREENFIELD", CONFIG.project_mode(project))
            self.assertEqual("FAST", CONFIG.delivery_profile(project))
            self.assertEqual([], CONFIG.source_roots(source))
            provider = json.loads((root / "sdlc/config/agent-provider.json").read_text(encoding="utf-8"))
            self.assertFalse(provider["enabled"])

    def test_fast_standard_full_are_runtime_policies(self):
        project = {"project": {"mode": "BROWNFIELD"}, "delivery": {"profile": "FAST"}}
        fast = CONFIG.delivery_policy(project)
        self.assertEqual("FAST", fast["profile"])
        self.assertIn("IMPACT", fast["enabled_stages"])
        self.assertNotIn("PROCESS", fast["enabled_stages"])
        self.assertEqual(7, len(json.loads((ROOT / "sdlc/config/program-spec-readiness.json").read_text(encoding="utf-8"))["profiles"]["FAST"]["required_field_ids"]))


class CanonicalConcurrencyTest(unittest.TestCase):
    def test_two_writers_on_same_base_cannot_both_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp) / "store.json"
            APPLY.save_store(store, APPLY.empty_store())
            results = []
            barrier = threading.Barrier(2)

            def worker(d):
                barrier.wait()
                result, _ = APPLY.apply_delta_to_store(store, d, lock_timeout_seconds=5)
                results.append(result["status"])

            threads = [
                threading.Thread(target=worker, args=(delta("D-1", 0, "RQ-1"),)),
                threading.Thread(target=worker, args=(delta("D-2", 0, "RQ-2"),)),
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            self.assertEqual(1, results.count("APPLIED"))
            self.assertEqual(1, results.count("CONFLICT"))
            self.assertEqual(1, APPLY.load_store(store)["revision"])
            self.assertFalse(store.with_suffix(".json.lock").exists())


class WorkRuntimeSafetyTest(unittest.TestCase):
    def _store_with_target(self, root):
        store = APPLY.empty_store()
        store["entities"]["RQ-001"] = {
            "id": "RQ-001", "entity_type": "RQ", "fields": {}, "truth_status": "CANDIDATE", "provenance": []
        }
        path = root / "sdlc/canonical/store.json"
        APPLY.save_store(path, store)
        return path

    def test_missing_provider_config_is_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = self._store_with_target(root)
            rc = WORK.main(["--root", str(root), "--target", "RQ-001", "--stage", "DESIGN", "--store", str(store)])
            self.assertEqual(4, rc)

    @unittest.skipUnless(shutil.which("git"), "git executable required")
    def test_protected_branch_is_blocked_before_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-b", "main"], cwd=root, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
            store_path = self._store_with_target(root)
            (root / "README.md").write_text("x\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-m", "base"], cwd=root, check=True, capture_output=True)
            plan = WORK.build_plan(root, target_id="RQ-001", store_path=store_path, stage="DESIGN")
            provider = {"schema_version": 1, "provider_id": "never", "enabled": True, "command": ["python", "-c", "raise SystemExit(99)"]}
            result = WORK.execute_plan(root, plan, provider_config=provider, run_dir=root / "sdlc/runtime/run", store_path=store_path)
            self.assertEqual("FAIL_PROTECTED_BRANCH_WRITE", result["status"])

    def test_check_reports_unconfigured_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            SETUP.bootstrap(root, name="g", mode="GREENFIELD", validate=False)
            result = CHECK.check(root, setup_only=True)
            self.assertEqual("SETUP_OR_PROVIDER_REQUIRED", result["status"])
            self.assertFalse(result["setup"]["provider"]["enabled"])


class FastProgramSpecTest(unittest.TestCase):
    def test_fast_accepts_seven_core_readiness_items_while_standard_does_not(self):
        config = json.loads((ROOT / "sdlc/config/program-spec-readiness.json").read_text(encoding="utf-8"))
        ids = config["profiles"]["FAST"]["required_field_ids"]
        markers = {row["id"]: row["marker"] for row in config["required_fields"]}
        text = "\n".join(markers[i] for i in ids)
        self.assertEqual([], PROGRAM.validate_text(text, config, "FAST"))
        self.assertTrue(PROGRAM.validate_text(text, config, "STANDARD"))


class RawDocumentEvidenceTest(unittest.TestCase):
    def test_minimal_pptx_preserves_slide_locator(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "brief.pptx"
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr("ppt/slides/slide1.xml", '''<?xml version="1.0" encoding="UTF-8"?>
<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>주문 취소 후 환불 상태를 조회한다</a:t></a:r></a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>''')
            result = EXTRACT.extract(path)
            self.assertEqual("EXTRACTED", result["extraction_status"])
            self.assertEqual("slide 1", result["evidence_chunks"][0]["locator"])
            self.assertIn("환불 상태", result["evidence_chunks"][0]["raw_text"])

    def test_minimal_xlsx_preserves_sheet_and_range(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rules.xlsx"
            with zipfile.ZipFile(path, "w") as zf:
                zf.writestr("xl/workbook.xml", '''<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="환불규칙" sheetId="1" r:id="rId1"/></sheets></workbook>''')
                zf.writestr("xl/_rels/workbook.xml.rels", '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"/></Relationships>''')
                zf.writestr("xl/worksheets/sheet1.xml", '''<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>상태</t></is></c><c r="B1" t="inlineStr"><is><t>처리</t></is></c></row><row r="2"><c r="A2" t="inlineStr"><is><t>취소승인</t></is></c><c r="B2" t="inlineStr"><is><t>환불요청</t></is></c></row></sheetData></worksheet>''')
            result = EXTRACT.extract(path)
            self.assertEqual("EXTRACTED", result["extraction_status"])
            chunk = result["evidence_chunks"][0]
            self.assertEqual("환불규칙!A1:B2", chunk["locator"])
            self.assertEqual(["상태", "처리"], chunk["structured_content"]["headers"])


class ExtensionBoundaryTest(unittest.TestCase):
    def test_external_provider_reuses_evidence_chunk(self):
        result = EXTERNAL.normalize({"items": [{"id": "JIRA-1", "summary": "주문 취소 변경", "url": "jira://JIRA-1"}]}, provider="JIRA")
        self.assertEqual(1, result["chunk_count"])
        self.assertEqual("External Provider -> Evidence Chunk -> Canonical/Stage Context", result["boundary"])
        self.assertEqual("JIRA", result["evidence_chunks"][0]["format_context"]["provider"])

    def test_customer_acceptance_records_provenance_without_silent_business_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = APPLY.empty_store()
            store["entities"]["RQ-1"] = {"id": "RQ-1", "entity_type": "RQ", "fields": {"name": "기존"}, "truth_status": "CANDIDATE", "provenance": []}
            store_path = root / "sdlc/canonical/store.json"
            APPLY.save_store(store_path, store)
            decision = {"decision_id": "D-1", "target_id": "RQ-1", "decision": "ACCEPT", "decided_by": "customer", "source_document": "A01.md"}
            result = CUSTOMER.capture(root, decision, store_path=store_path)
            self.assertEqual("APPLIED", result["status"])
            after = APPLY.load_store(store_path)["entities"]["RQ-1"]
            self.assertEqual("기존", after["fields"]["name"])
            self.assertTrue(any("CUSTOMER_DECISION ACCEPT" in p.get("note", "") for p in after["provenance"]))

    def test_knowledge_promotion_is_review_only(self):
        store = APPLY.empty_store()
        store["entities"]["BR-1"] = {
            "id": "BR-1", "entity_type": "BR", "fields": {"rule": "승인 후 환불"}, "truth_status": "CONFIRMED_BUSINESS",
            "provenance": [{"evidence_class": "CONFIRMED", "stage": "CLARIFY", "source_artifact": "a.md"}],
        }
        rows = KNOWLEDGE.candidates(store)
        self.assertEqual(1, len(rows))
        self.assertTrue(rows[0]["review_required"])
        self.assertFalse(rows[0]["auto_apply"])

    def test_enterprise_java_adapter_adds_static_candidates_without_business_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            java = root / "src/main/java/com/acme/OrderService.java"
            java.parent.mkdir(parents=True)
            java.write_text('''package com.acme;
class OrderService {
  @Transactional
  public void cancel() { jdbc.update("UPDATE orders SET status='CANCEL'"); }
  @KafkaListener(topics="refund")
  public void refund() { }
}
@Entity @Table(name="orders") class OrderEntity {}
interface OrderRepository extends JpaRepository<OrderEntity, Long> {}
''', encoding="utf-8")
            result = ENTERPRISE.analyze(root)
            coverage = {row["dimension"]: row["status"] for row in result["coverage"]}
            self.assertEqual("PARTIAL", coverage["TRANSACTION"])
            self.assertEqual("PARTIAL", coverage["EVENT"])
            self.assertFalse(result["business_impact_confirmed"])
            self.assertEqual("PARTIAL_COVERAGE_GAPS", result["completion_status"])

    def test_minimum_core_excludes_optional_customer_and_brownfield_runtime(self):
        harness = json.loads((ROOT / "sdlc/design/contracts/harness-package-contract.json").read_text(encoding="utf-8"))
        core = set(harness["core_required_files"])
        self.assertNotIn("sdlc/scripts/render_customer_document.py", core)
        self.assertNotIn("sdlc/scripts/detect_source_drift.py", core)
        self.assertIn("sdlc/scripts/harness.py", core)
        self.assertEqual(["core", "project_overlay", "local_override"], harness["overlay_precedence"])


if __name__ == "__main__":
    unittest.main()
