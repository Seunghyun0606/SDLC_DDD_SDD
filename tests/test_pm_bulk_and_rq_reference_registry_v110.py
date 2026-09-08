import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPT_DIR = ROOT / "sdlc/scripts"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


WORKLIST = load("pm_bulk_worklist_test_runtime", "rq_worklist.py")
REFERENCES = load("rq_reference_registry_test_runtime", "rq_reference_registry.py")

PROJECT_YAML = """schema_version: 1
project:
  name: pm-bulk-test
  mode: BROWNFIELD
delivery:
  profile: STANDARD
change:
  level_policy: AUTO
technology:
  language: Java
  framework: Spring
  build: []
  test: []
source:
  roots:
    - src
  test_roots: []
  resource_roots: []
  excludes: []
git:
  protected_branches:
    - main
documents:
  language: ko-KR
  engineering:
    profile: ENGINEERING_SDD_COMPACT
  customer:
    profile: CUSTOMER_STANDARD_3
  pm:
    profile: PM_STANDARD
  machine:
    visibility: HIDDEN
unresolved: []
"""


def rq(rq_id: str, name: str, external: str):
    return {
        "id": rq_id,
        "entity_type": "RQ",
        "fields": {"name": name, "external_requirement_ids": [external]},
        "truth_status": "CANDIDATE",
        "provenance": [],
    }


class PmBulkAndRqReferenceRegistryV110Test(unittest.TestCase):
    def make_project(self, root: Path):
        (root / ".sdlc").mkdir(parents=True)
        (root / ".sdlc/project.yaml").write_text(PROJECT_YAML, encoding="utf-8")
        store_path = root / "sdlc/canonical/store.json"
        store_path.parent.mkdir(parents=True)
        store_path.write_text(json.dumps({
            "schema_version": 1,
            "revision": 1,
            "entities": {
                "RQ-001": rq("RQ-001", "근무계획 개선", "REQ-001"),
                "RQ-002": rq("RQ-002", "승인 기능 개선", "REQ-002"),
            },
            "relations": [],
            "applied_deltas": [],
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        manifest = root / "br-input/manifest.yaml"
        manifest.parent.mkdir(parents=True)
        manifest.write_text("""schema_version: 1
documents:
  - document_id: DOC-001
    path: originals/근태규정.pdf
    title: 근태규정
    locator_hint: page
  - document_id: DOC-002
    path: originals/운영회의록.docx
    title: 운영회의록
    locator_hint: paragraph
""", encoding="utf-8")
        return store_path

    def test_csv_bulk_import_accepts_arbitrary_pm_columns_without_canonical_mutation(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = self.make_project(root)
            before = store.read_bytes()
            csv_path = root / "pm.csv"
            csv_path.write_text(
                "RQ,요구사항명,외부 요구ID,담당개발자,Sprint,계약WBS,현재 상태\n"
                "RQ-001,근무계획 개선,REQ-001,홍길동,S1,WBS-10,PM확인중\n"
                "RQ-002,승인 기능 개선,REQ-002,김개발,S2,WBS-20,고객협의중\n",
                encoding="utf-8-sig",
            )
            result = WORKLIST.import_planning(root, csv_path)
            self.assertEqual("RQ_PLANNING_IMPORTED", result["status"])
            self.assertFalse(result["canonical_mutated"])
            self.assertEqual(before, store.read_bytes())
            planning = json.loads((root / WORKLIST.PLANNING_PATH).read_text(encoding="utf-8"))
            self.assertIn("custom::담당개발자", planning["column_order"])
            self.assertIn("custom::계약WBS", planning["column_order"])
            self.assertEqual("홍길동", planning["requirements"]["RQ-001"]["custom::담당개발자"])
            view = (root / WORKLIST.VIEW_PATH).read_text(encoding="utf-8")
            self.assertIn("담당개발자", view)
            self.assertIn("PM:현재 상태", view)
            self.assertIn("현재 상태", view)

    def test_xlsx_export_editable_file_roundtrips_through_reader(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root)
            WORKLIST.assign(root, "RQ-001", {"engineering_owner": "박개발", **{k: None for k in WORKLIST.PLANNING_FIELDS if k != "engineering_owner"}})
            out = root / "rq.xlsx"
            result = WORKLIST.export_planning(root, out, "xlsx")
            self.assertEqual("RQ_PLANNING_EXPORTED", result["status"])
            headers, rows = WORKLIST._read_table(out)
            self.assertEqual("RQ", headers[0])
            self.assertIn("설계·개발", headers)
            self.assertEqual(2, len(rows))

    def test_replacing_spreadsheet_columns_removes_deleted_pm_column(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root)
            first = root / "first.csv"
            first.write_text("RQ,A,B\nRQ-001,1,2\nRQ-002,3,4\n", encoding="utf-8-sig")
            WORKLIST.import_planning(root, first)
            second = root / "second.csv"
            second.write_text("RQ,A\nRQ-001,9\nRQ-002,8\n", encoding="utf-8-sig")
            WORKLIST.import_planning(root, second)
            planning = json.loads((root / WORKLIST.PLANNING_PATH).read_text(encoding="utf-8"))
            self.assertEqual(["custom::A"], planning["column_order"])
            self.assertNotIn("custom::B", planning["requirements"]["RQ-001"])

    def test_reference_registry_is_many_to_many_and_noncanonical(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = self.make_project(root)
            before = store.read_bytes()
            REFERENCES.link(root, "RQ-001", "DOC-001", purpose="업무규칙 확인", required=True)
            REFERENCES.link(root, "RQ-002", "DOC-001", purpose="영향 확인")
            REFERENCES.link(root, "RQ-001", "DOC-002", purpose="회의결정 확인")
            self.assertEqual(before, store.read_bytes())
            registry = json.loads((root / REFERENCES.STORE_PATH).read_text(encoding="utf-8"))
            self.assertEqual(3, len(registry["links"]))
            rows, _ = REFERENCES.build_rows(root)
            self.assertEqual(3, len(rows))
            self.assertTrue(all(row["evidence_state"] == "참고 예정" for row in rows))

    def test_reference_bulk_import_validates_manifest_and_rq_before_write(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root)
            valid = root / "refs.csv"
            valid.write_text("RQ,문서ID,사용목적,참고위치,필수여부,비고\nRQ-001,DOC-001,규정 확인,4장,필수,\n", encoding="utf-8-sig")
            result = REFERENCES.import_registry(root, valid)
            self.assertEqual("RQ_REFERENCE_REGISTRY_IMPORTED", result["status"])
            before = (root / REFERENCES.STORE_PATH).read_bytes()
            invalid = root / "invalid.csv"
            invalid.write_text("RQ,문서ID\nRQ-001,DOC-NOT-FOUND\n", encoding="utf-8-sig")
            with self.assertRaises(ValueError):
                REFERENCES.import_registry(root, invalid)
            self.assertEqual(before, (root / REFERENCES.STORE_PATH).read_bytes())

    def test_contracts_keep_pm_and_reference_planning_outside_business_truth(self):
        pm = json.loads((ROOT / "sdlc/design/contracts/project-rq-worklist-contract.json").read_text(encoding="utf-8"))
        ref = json.loads((ROOT / "sdlc/design/contracts/rq-reference-registry-contract.json").read_text(encoding="utf-8"))
        self.assertEqual("ANY_USER_DEFINED_NON_SYSTEM_COLUMN", pm["editable_file"]["planning_column_policy"])
        self.assertFalse(pm["editable_file"]["custom_columns_affect_canonical"])
        self.assertTrue(ref["rules"]["link_does_not_mutate_canonical"])
        self.assertEqual("MANY_TO_MANY", ref["link_cardinality"])


if __name__ == "__main__":
    unittest.main()
