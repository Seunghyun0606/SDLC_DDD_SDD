import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SCRIPTS = ROOT / "sdlc/scripts"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CONFIG = load_module("projection_v110_config", "project_config.py")
CUSTOMER = load_module("projection_v110_customer", "customer_projection_runtime.py")
LIFE = load_module("projection_v110_lifecycle", "projection_lifecycle_runtime.py")
SCAFFOLD = load_module("projection_v110_scaffold", "build_project_scaffold.py")


class ProjectionSeparationV110Test(unittest.TestCase):
    def test_engineering_profile_resolution_prefers_new_key_and_preserves_legacy_alias(self):
        defaulted = CONFIG.normalize_document_profiles({"documents": {}})
        self.assertEqual(
            "ENGINEERING_SDD_COMPACT",
            defaulted["documents"]["engineering"]["profile"],
        )
        self.assertEqual(
            defaulted["documents"]["engineering"]["profile"],
            defaulted["documents"]["internal"]["profile"],
        )

        legacy = CONFIG.normalize_document_profiles(
            {"documents": {"internal": {"profile": "STANDARD_5"}}}
        )
        self.assertEqual("STANDARD_5", legacy["documents"]["engineering"]["profile"])

        preferred = CONFIG.normalize_document_profiles(
            {
                "documents": {
                    "engineering": {"profile": "ENGINEERING_SDD_COMPACT"},
                    "internal": {"profile": "STANDARD_5"},
                }
            }
        )
        self.assertEqual(
            "ENGINEERING_SDD_COMPACT",
            preferred["documents"]["engineering"]["profile"],
        )
        self.assertEqual(
            "ENGINEERING_SDD_COMPACT",
            preferred["documents"]["internal"]["profile"],
        )

    def test_customer_settings_do_not_resolve_engineering_profile(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".sdlc").mkdir(parents=True)
            (root / ".sdlc/project.yaml").write_text(
                """schema_version: 1
project:
  name: projection-test
  mode: BROWNFIELD
delivery:
  profile: STANDARD
documents:
  engineering:
    profile: ENGINEERING_PROFILE_THAT_DOES_NOT_EXIST
  customer:
    profile: CUSTOMER_STANDARD_3
  pm:
    profile: PM_STANDARD
  machine:
    visibility: HIDDEN
""",
                encoding="utf-8",
            )

            copies = [
                "sdlc/tailoring/standard/CUSTOMER_STANDARD_3.yaml",
                "sdlc/design/contracts/customer-document-contract.json",
                "sdlc/config/customer-document-profile.example.json",
                "sdlc/templates/customer/standard/A01_요구_업무_기능_합의서.md",
                "sdlc/templates/customer/standard/A02_영향_개발범위_공유서.md",
                "sdlc/templates/customer/standard/A03_테스트_인수_운영_결과서.md",
            ]
            for rel in copies:
                dst = root / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / rel, dst)

            settings = CUSTOMER._project_settings(
                root,
                contract_path=None,
                projection_config_path=None,
                tailoring_profile_id=None,
            )
            self.assertEqual("CUSTOMER_STANDARD_3", settings["customer_profile_id"])
            self.assertNotIn("internal_profile", settings)
            self.assertNotIn("engineering_profile", settings)

    def test_customer_full_profile_splits_semantic_contract_without_engineering_mapping(self):
        profile, _ = CUSTOMER.TAILOR.load_profile(ROOT, "CUSTOMER_WATERFALL_FULL")
        contract = CUSTOMER.RENDER.load(
            ROOT / "sdlc/design/contracts/customer-document-contract.json"
        )
        artifact_id, row, semantic = CUSTOMER._profile_artifact(
            profile, "functional_design", contract
        )
        self.assertEqual("functional_design", artifact_id)
        self.assertEqual("solution_agreement", semantic)
        self.assertEqual("CUSTOMER", row["audience"])

        with self.assertRaises(ValueError):
            CUSTOMER._profile_artifact(profile, "solution_agreement", contract)

    def test_engineering_manual_edit_warning_does_not_mutate_canonical(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = root / "sdlc/canonical/store.json"
            store.parent.mkdir(parents=True)
            canonical = {"revision": 1, "entities": {"RQ-1": {"id": "RQ-1"}}, "relations": []}
            store.write_text(json.dumps(canonical), encoding="utf-8")
            artifact = root / "docs/10_engineering/RQ-1/specs/RQ-1.md"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("generated\n", encoding="utf-8")

            row = LIFE.register_generated(
                root,
                target="RQ-1",
                artifact_id="work_unit_sdd",
                artifact_path="docs/10_engineering/RQ-1/specs/RQ-1.md",
                audience="INTERNAL_IT",
                profile_id="ENGINEERING_SDD_COMPACT",
            )
            self.assertEqual("CURRENT", LIFE.state(root, row))
            artifact.write_text("manual design edit\n", encoding="utf-8")
            self.assertEqual("MANUAL_EDIT_DETECTED", LIFE.state(root, row))
            self.assertEqual(canonical, json.loads(store.read_text(encoding="utf-8")))

    def test_customer_final_review_is_preserved_when_canonical_changes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = root / "sdlc/canonical/store.json"
            store.parent.mkdir(parents=True)
            store.write_text(
                json.dumps({"revision": 1, "entities": {"RQ-1": {}}, "relations": []}),
                encoding="utf-8",
            )
            artifact = root / "docs/20_customer/RQ-1/final.md"
            artifact.parent.mkdir(parents=True)
            artifact.write_text("agent draft\n", encoding="utf-8")
            LIFE.register_generated(
                root,
                target="RQ-1",
                artifact_id="handover",
                artifact_path="docs/20_customer/RQ-1/final.md",
                audience="CUSTOMER",
                profile_id="CUSTOMER_WATERFALL_FULL",
            )

            artifact.write_text("human final wording\n", encoding="utf-8")
            reviewed = LIFE.review(
                root,
                target="RQ-1",
                artifact_id="handover",
                reviewer="reviewer",
                accepted=True,
                final_review=True,
            )
            self.assertEqual("FINAL_REVIEW", reviewed["status"])

            store.write_text(
                json.dumps({"revision": 2, "entities": {"RQ-1": {}}, "relations": []}),
                encoding="utf-8",
            )
            metadata = json.loads(
                LIFE.metadata_path(root, "RQ-1", "handover").read_text(encoding="utf-8")
            )
            self.assertEqual("STALE_VIEW", LIFE.state(root, metadata))
            stale_review = LIFE.review(
                root,
                target="RQ-1",
                artifact_id="handover",
                reviewer="reviewer",
                accepted=True,
                final_review=True,
            )
            self.assertTrue(stale_review["final_human_edit_exists"])
            self.assertFalse(stale_review["automatic_overwrite_allowed"])
            self.assertEqual("human final wording\n", artifact.read_text(encoding="utf-8"))

    def test_project_scaffold_selects_new_runtime_and_excludes_framework_assets(self):
        selected = SCAFFOLD.select_files(ROOT)
        self.assertIn("sdlc/scripts/project_config.py", selected)
        self.assertIn("sdlc/tailoring/standard/ENGINEERING_SDD_COMPACT.yaml", selected)
        self.assertIn("sdlc/tailoring/standard/CUSTOMER_WATERFALL_FULL.yaml", selected)
        self.assertNotIn("sdlc/tailoring/standard/STAGE_ORIENTED_FULL.yaml", selected)
        self.assertFalse(any(path.startswith("tests/") for path in selected))
        self.assertFalse(any(path.startswith("docs/00_관리/") for path in selected))


if __name__ == "__main__":
    unittest.main()
