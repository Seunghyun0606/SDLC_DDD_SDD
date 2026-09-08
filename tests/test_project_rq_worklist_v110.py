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


WORKLIST = load("project_rq_worklist_test_runtime", "rq_worklist.py")


PROJECT_YAML = """schema_version: 1
project:
  name: rq-list-test
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


def entity(rq_id: str, name: str, external: str):
    return {
        "id": rq_id,
        "entity_type": "RQ",
        "fields": {"name": name, "external_requirement_ids": [external]},
        "truth_status": "CANDIDATE",
        "provenance": [],
    }


class ProjectRqWorklistV110Test(unittest.TestCase):
    def make_project(self, root: Path):
        (root / ".sdlc").mkdir(parents=True)
        (root / ".sdlc/project.yaml").write_text(PROJECT_YAML, encoding="utf-8")
        store = root / "sdlc/canonical/store.json"
        store.parent.mkdir(parents=True)
        store.write_text(json.dumps({
            "schema_version": 1,
            "revision": 1,
            "updated_at": None,
            "entities": {"RQ-001": entity("RQ-001", "근무계획 개선", "REQ-001")},
            "relations": [],
            "applied_deltas": [],
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return store

    def test_refresh_materializes_project_management_view_from_canonical(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_project(root)
            result = WORKLIST.refresh(root)
            self.assertEqual("RQ_WORKLIST_REFRESHED", result["status"])
            self.assertEqual(1, result["rq_count"])
            view = root / "docs/00_관리/RQ_작업목록.md"
            text = view.read_text(encoding="utf-8")
            self.assertIn("RQ-001", text)
            self.assertIn("근무계획 개선", text)
            self.assertIn("외부 요구ID", text)
            self.assertIn("현재 상태", text)
            self.assertIn("다음 작업", text)

    def test_assignment_changes_only_pm_planning_and_preserves_canonical(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = self.make_project(root)
            before = store.read_bytes()
            result = WORKLIST.assign(root, "RQ-001", {
                "engineering_owner": "박개발",
                "test_owner": "최QA",
                "priority": "HIGH",
                **{key: None for key in WORKLIST.PLANNING_FIELDS if key not in {"engineering_owner", "test_owner", "priority"}},
            })
            self.assertEqual("RQ_ASSIGNMENT_UPDATED", result["status"])
            self.assertEqual(before, store.read_bytes())
            planning = json.loads((root / WORKLIST.PLANNING_PATH).read_text(encoding="utf-8"))
            self.assertEqual("박개발", planning["requirements"]["RQ-001"]["engineering_owner"])
            self.assertEqual("최QA", planning["requirements"]["RQ-001"]["test_owner"])
            self.assertEqual("HIGH", planning["requirements"]["RQ-001"]["priority"])

    def test_incremental_rq_refresh_adds_new_rq_and_preserves_existing_assignment(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store_path = self.make_project(root)
            WORKLIST.assign(root, "RQ-001", {
                "engineering_owner": "기존담당",
                **{key: None for key in WORKLIST.PLANNING_FIELDS if key != "engineering_owner"},
            })
            store = json.loads(store_path.read_text(encoding="utf-8"))
            store["revision"] = 2
            store["entities"]["RQ-002"] = entity("RQ-002", "추가 운영 요구", "REQ-002")
            store_path.write_text(json.dumps(store, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result = WORKLIST.refresh(root)
            self.assertEqual(2, result["rq_count"])
            runtime = json.loads((root / WORKLIST.RUNTIME_PATH).read_text(encoding="utf-8"))
            rows = {row["rq_id"]: row for row in runtime["rows"]}
            self.assertEqual("기존담당", rows["RQ-001"]["engineering_owner"])
            self.assertEqual("", rows["RQ-002"]["engineering_owner"])

    def test_contract_separates_planning_from_derived_status(self):
        contract = json.loads((ROOT / "sdlc/design/contracts/project-rq-worklist-contract.json").read_text(encoding="utf-8"))
        self.assertNotIn("working_state", contract["planning_fields"])
        self.assertIn("working_state", contract["derived_columns"])
        self.assertIn("change_level", contract["derived_columns"])
        self.assertEqual("sdlc/canonical/store.json", contract["authority"]["business_truth"])


if __name__ == "__main__":
    unittest.main()
