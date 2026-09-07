import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def visible_text(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def load_customer_runtime():
    path = ROOT / "sdlc/scripts/customer_projection_runtime.py"
    name = "test_projection_visibility_customer_runtime"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class ProjectionVisibilityHygieneV110Test(unittest.TestCase):
    def test_projection_visibility_contract_separates_machine_and_human_views(self):
        contract = json.loads(read("sdlc/design/contracts/projection-visibility-contract.json"))
        self.assertTrue(contract["principles"]["allowlist_before_sanitize"])
        self.assertTrue(contract["principles"]["stable_block_ids_may_exist_as_hidden_markers"])
        self.assertIn("canonical_entity_id", contract["machine_only_default"])
        self.assertIn("provenance", contract["machine_only_default"])
        self.assertIn("block_id", contract["machine_only_default"])
        self.assertIn("method", contract["engineering_visible"])
        self.assertIn("query", contract["engineering_visible"])
        self.assertIn("business_rule", contract["customer_visible"])
        self.assertEqual(contract["customer_direct_canonical_policy"]["default"], "ALLOWLIST_ONLY")
        self.assertEqual(contract["customer_direct_canonical_policy"]["relation_expansion"], "DENY_BY_DEFAULT")

    def test_human_engineering_templates_hide_framework_taxonomy(self):
        paths = [
            "sdlc/templates/engineering/standard/00_work-map.md",
            "sdlc/templates/engineering/standard/work-unit-sdd.md",
            "sdlc/templates/engineering/standard/program-spec.md",
            "sdlc/custom/project/templates/hris-hunel/01_업무정의서.md",
            "sdlc/custom/project/templates/hris-hunel/02_작업지시서.md",
        ]
        machine_terms = [
            "Canonical Spec",
            "Stage Semantic",
            "CONFIRMED_BUSINESS",
            "SOURCE_BLOCK",
            "ITERATE",
            "ALERT",
            "DIRECT_MODIFY",
            "SCRIPT_OUTPUT",
            "HUMAN_OPERATION",
            "EXECUTION_GUARDED",
            "Human Decision Queue",
            "Queue ID",
            "Recheck At",
            "NEXT_SEMANTIC_WORK",
            "BEFORE_SOURCE_WRITE",
        ]
        for path in paths:
            raw = read(path)
            self.assertIn("<!-- BLOCK_ID:", raw)
            text = visible_text(raw)
            for term in machine_terms:
                self.assertNotIn(term, text, msg=f"{path} leaks machine term: {term}")

    def test_program_projections_keep_implementation_relevant_technical_detail(self):
        standard = visible_text(read("sdlc/templates/engineering/standard/program-spec.md"))
        for term in ["소스 / 심볼", "Query", "Table", "Transaction", "Interface", "Procedure", "Security"]:
            self.assertIn(term, standard)

        hunel = visible_text(read("sdlc/custom/project/templates/hris-hunel/02_작업지시서.md"))
        for term in [
            "JSP",
            "Java",
            "XML SQLResource",
            "ibsheet",
            "CUDSQLManager",
            "chkAuthMenu",
            "chkAuthTrans",
            "Procedure",
        ]:
            self.assertIn(term, hunel)

    def test_customer_profile_hides_internal_and_optional_evidence_detail_by_default(self):
        profile = json.loads(read("sdlc/config/customer-document-profile.json"))
        display = profile["display"]
        self.assertFalse(display["show_internal_ids"])
        self.assertFalse(display["show_source_hash"])
        self.assertFalse(display["show_confidence_status"])

        for doc in ["solution_agreement", "delivery_scope", "acceptance_handover"]:
            override = profile["document_overrides"][doc]
            self.assertIn("기술_상세_부록", override["disable_optional"])
            self.assertIn("근거_상세_부록", override["disable_optional"])

    def test_customer_readme_defines_machine_side_trace_and_allowlist_first(self):
        text = read("sdlc/templates/customer/README.md")
        self.assertIn("Machine-side Mapping", text)
        self.assertIn("Allowlist", text)
        self.assertIn("Sanitizer", text)
        self.assertIn("기술 상세와 근거 상세는 기본 OFF", text)

    def test_customer_direct_canonical_input_is_allowlist_only_and_does_not_expand_relations(self):
        runtime = load_customer_runtime()
        contract = json.loads(read("sdlc/design/contracts/customer-document-contract.json"))
        row = {"sources": {"stages": ["DECOMPOSE", "CLARIFY"]}}
        fake_store = {
            "entities": {
                "RQ-001": {
                    "id": "RQ-001",
                    "type": "RQ",
                    "title": "급여 마감 정책 변경",
                    "summary": "월 마감 이후 재계산 정책을 명확히 한다.",
                    "business_rule": "급여 마감 이후 자동 재계산을 허용하지 않는다.",
                    "revision": 42,
                    "provenance": {"source": "internal-secret"},
                    "confidence": "HIGH",
                    "source_hash": "abc123",
                    "queue_id": "HITL-RQ-001-01",
                    "change_level": "L4",
                    "unrelated_internal_field": "do not expose",
                }
            },
            "relations": [
                {"source": "RQ-001", "target": "BR-009", "type": "HAS_RULE"}
            ],
        }

        original = runtime.TAILOR.load_store
        runtime.TAILOR.load_store = lambda _root: fake_store
        try:
            artifacts = runtime._canonical_artifact(ROOT, "RQ-001", row, contract)
        finally:
            runtime.TAILOR.load_store = original

        self.assertEqual(len(artifacts), 1)
        artifact = artifacts[0]
        self.assertEqual(artifact["visibility_policy"], "ALLOWLIST_ONLY")
        self.assertEqual(artifact["semantic_source"], "CANONICAL_ALLOWLIST")
        fields = artifact["fields"]
        self.assertEqual(fields["summary"], "월 마감 이후 재계산 정책을 명확히 한다.")
        self.assertIn("business_rule", fields)
        for forbidden in [
            "id",
            "type",
            "revision",
            "provenance",
            "confidence",
            "source_hash",
            "queue_id",
            "change_level",
            "unrelated_internal_field",
            "관련 ID 및 추적성",
        ]:
            self.assertNotIn(forbidden, fields)
        serialized = json.dumps(artifact, ensure_ascii=False)
        self.assertNotIn("BR-009", serialized)
        self.assertNotIn("HAS_RULE", serialized)


if __name__ == "__main__":
    unittest.main()
