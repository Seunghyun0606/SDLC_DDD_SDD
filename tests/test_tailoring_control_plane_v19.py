from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "sdlc" / "scripts"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CONFIG = load("test_v19_config", "runtime_config_v19.py")
TAILOR = load("test_v19_tailoring", "tailoring_runtime.py")
CHECK = load("test_v19_check", "tailored_check.py")


class TailoringControlPlaneV19Test(unittest.TestCase):
    def minimal_project(self, root: Path, *, internal: str = "STANDARD_3") -> dict:
        project = {
            "schema_version": 1,
            "project": {"name": "demo", "mode": "BROWNFIELD"},
            "delivery": {"profile": "STANDARD"},
            "change": {"level_policy": "AUTO"},
            "source": {"roots": [], "test_roots": [], "resource_roots": [], "excludes": []},
            "git": {"protected_branches": ["main"]},
            "documents": {
                "language": "ko-KR",
                "internal": {"profile": internal},
                "customer": {"profile": "CUSTOMER_STANDARD_3"},
                "pm": {"profile": "PM_STANDARD"},
                "machine": {"visibility": "HIDDEN"},
            },
        }
        path = root / ".sdlc" / "project.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "schema_version: 1\n"
            "project:\n  name: demo\n  mode: BROWNFIELD\n"
            "delivery:\n  profile: STANDARD\n"
            "change:\n  level_policy: AUTO\n"
            "source:\n  roots: []\n  test_roots: []\n  resource_roots: []\n  excludes: []\n"
            "git:\n  protected_branches: [main]\n"
            "documents:\n"
            "  language: ko-KR\n"
            f"  internal:\n    profile: {internal}\n"
            "  customer:\n    profile: CUSTOMER_STANDARD_3\n"
            "  pm:\n    profile: PM_STANDARD\n"
            "  machine:\n    visibility: HIDDEN\n",
            encoding="utf-8",
        )
        return project

    def test_project_config_accepts_v19_control_keys_and_rejects_dead_key(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.minimal_project(root)
            resolved = CONFIG.resolve_runtime_config(root)
            self.assertEqual("STANDARD_3", resolved["project"]["documents"]["internal"]["profile"])
            self.assertIn("documents.internal.profile", resolved["usage"]["runtime"])
            self.assertIn("change.level_policy", resolved["usage"]["runtime"])
            project_path = root / ".sdlc" / "project.yaml"
            project_path.write_text(project_path.read_text(encoding="utf-8") + "unknown_switch: true\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unused project config key"):
                CONFIG.resolve_runtime_config(root)

    def test_standard_profiles_are_valid_and_stage_preserving(self):
        for profile_id in ["STANDARD_3", "STANDARD_5", "STAGE_ORIENTED_FULL", "CUSTOMER_STANDARD_3", "PM_STANDARD"]:
            profile, path = TAILOR.load_profile(ROOT, profile_id)
            self.assertEqual(profile_id, profile["profile_id"])
            self.assertTrue(path.is_file())

    def test_change_level_l1_micro(self):
        result = TAILOR.classify_change_level({"changed_component_count": 1, "evidence_refs": ["RQ-001"]})
        self.assertEqual("L1", result["level"])

    def test_change_level_l3_multi_program(self):
        result = TAILOR.classify_change_level({
            "changed_component_count": 3,
            "data_or_schema_change": True,
            "evidence_refs": ["RQ-001", "PGM-1", "PGM-2", "PGM-3"],
        })
        self.assertEqual("L3", result["level"])

    def test_change_level_l4_process_interface_batch(self):
        result = TAILOR.classify_change_level({
            "changed_component_count": 3,
            "business_rule_impact": True,
            "external_interface": True,
            "batch": True,
            "cross_domain": True,
            "evidence_refs": ["RQ-001"],
        })
        self.assertEqual("L4", result["level"])

    def test_unknown_impact_gets_l2_safety_floor_then_discovery_escalates_without_auto_downgrade(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            project = {"change": {"level_policy": "AUTO"}}
            store = {
                "revision": 1,
                "entities": {"RQ-001": {"entity_type": "RQ", "fields": {"name": "local wording"}, "provenance": []}},
                "relations": [],
            }
            first = TAILOR.resolve_change_level(root, "RQ-001", "DECOMPOSE", store, project)
            self.assertEqual("L2", first["provisional_change_level"])
            self.assertTrue(any("L2_SAFETY_FLOOR" in reason for reason in first["classification_reason"]))

            evidence_path = root / "sdlc/runtime/change-level/RQ-001-evidence.json"
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_text(json.dumps({"architecture_change": True, "evidence_refs": ["legacy-discovery"]}), encoding="utf-8")
            escalated = TAILOR.resolve_change_level(root, "RQ-001", "DEVELOPMENT", store, project)
            self.assertEqual("L5", escalated["effective_change_level"])
            self.assertEqual(1, len(escalated["escalation_history"]))

            evidence_path.write_text(json.dumps({"changed_component_count": 1, "architecture_change": False}), encoding="utf-8")
            retained = TAILOR.resolve_change_level(root, "RQ-001", "DEVELOPMENT", store, project)
            self.assertEqual("L5", retained["effective_change_level"])
            self.assertTrue(any("automatic downgrade blocked" in x for x in retained["classification_reason"]))

    def test_same_stage_maps_to_three_five_and_full_without_changing_stage(self):
        store = {
            "revision": 1,
            "entities": {"RQ-001": {"entity_type": "RQ", "fields": {"name": "기능 변경"}, "provenance": []}},
            "relations": [],
        }
        paths = {}
        for profile in ["STANDARD_3", "STANDARD_5", "STAGE_ORIENTED_FULL"]:
            project = {"documents": {"internal": {"profile": profile}, "customer": {"profile": "CUSTOMER_STANDARD_3"}, "pm": {"profile": "PM_STANDARD"}}}
            resolved = TAILOR.resolve_artifacts(ROOT, project=project, target="RQ-001", stage="DESIGN", change_level="L3", store=store)
            self.assertTrue(resolved["stage_preserved"])
            self.assertEqual("DESIGN", resolved["stage"])
            self.assertFalse(resolved["projection_creates_business_truth"])
            self.assertIsNotNone(resolved["primary_work_artifact"])
            paths[profile] = resolved["primary_work_artifact"]["output_path"]
        self.assertEqual(3, len(set(paths.values())))

    def test_customer_is_projection_not_business_truth_authority(self):
        project = {"documents": {"internal": {"profile": "STANDARD_3"}, "customer": {"profile": "CUSTOMER_STANDARD_3"}, "pm": {"profile": "PM_STANDARD"}}}
        store = {"revision": 1, "entities": {"RQ-001": {"entity_type": "RQ", "fields": {}, "provenance": []}}, "relations": []}
        resolved = TAILOR.resolve_artifacts(ROOT, project=project, target="RQ-001", stage="DESIGN", change_level="L3", store=store)
        self.assertFalse(resolved["projection_creates_business_truth"])
        self.assertTrue(all(item["authoring"] == "GENERATED_VIEW" for item in resolved["affected_artifacts"]["customer"]))

    def test_projection_freshness_detects_stale_view(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "sdlc/runtime/projections/RQ-001-view.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({
                "artifact_path": "docs/RQ-001.md",
                "audience": "INTERNAL_IT",
                "generated_from_revision": 2,
            }), encoding="utf-8")
            result = TAILOR.projection_freshness(root, 3)
            self.assertEqual(1, result["stale_count"])
            self.assertEqual("STALE_VIEW", result["views"][0]["freshness"])

    def test_human_check_hides_internal_stage_and_uses_working_software_state(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.minimal_project(root)
            store_path = root / "sdlc/canonical/store.json"
            store_path.parent.mkdir(parents=True, exist_ok=True)
            store_path.write_text(json.dumps({
                "schema_version": 1,
                "revision": 3,
                "entities": {
                    "RQ-001": {
                        "entity_type": "RQ",
                        "truth_status": "CANDIDATE",
                        "fields": {"name": "로그인 개선", "current_conclusion": "OPEN"},
                        "provenance": [{"stage": "DESIGN", "source_artifact": "docs/design.md"}],
                    }
                },
                "relations": [],
                "applied_deltas": [],
            }), encoding="utf-8")
            result = CHECK.check(root, target="RQ-001", setup_only=False, debug_stage=False)
            review = result["rq_review"]
            self.assertTrue(review["internal_stage_hidden"])
            self.assertNotIn("internal_stage_debug", review["summary"])
            self.assertNotIn("user_state", review["summary"])
            self.assertIn("working_state", review["summary"])
            self.assertIn("what_blocks_release", review["summary"])
            self.assertIn("evidence_passed", review["summary"])
            self.assertIn("next", review["summary"])

    def test_brownfield_contract_forbids_source_business_truth_rewrite(self):
        contract = json.loads((ROOT / "sdlc/design/contracts/brownfield-authority-reconciliation-contract.json").read_text(encoding="utf-8"))
        self.assertFalse(contract["rules"]["source_can_auto_rewrite_business_truth"])
        self.assertEqual("CONFLICT", contract["rules"]["source_conflict_with_business_truth_state"])


if __name__ == "__main__":
    unittest.main()
