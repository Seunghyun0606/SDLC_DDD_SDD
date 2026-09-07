from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "sdlc/scripts"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


EXEC = load("change_level_control_v110_exec", "change_execution_runtime.py")
CONFIG = load("change_level_control_v110_config", "project_config.py")
TAILOR = load("change_level_control_v110_tailor", "tailoring_runtime.py")


def store_with_facts(**facts):
    base = {
        "HAS_INTERFACE": "NO",
        "HAS_BATCH": "NO",
        "IMPACT_COVERAGE": "COMPLETE",
        "SCHEMA_CHANGE": "NONE",
        "SECURITY_IMPACT": "NONE",
        "ARCHITECTURE_IMPACT": "NONE",
        "MIGRATION_IMPACT": "NONE",
    }
    base.update(facts)
    return {
        "revision": 1,
        "entities": {
            "RQ-001": {
                "id": "RQ-001",
                "entity_type": "RQ",
                "fields": {"title": "테스트 요구", "change_facts": base},
            }
        },
        "relations": [],
    }


class ChangeLevelControlPlaneV110Test(unittest.TestCase):
    def test_project_target_override_wins_over_auto_and_history_is_recorded(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            state = EXEC.resolve_change(
                root,
                "RQ-001",
                store_with_facts(),
                {
                    "change": {
                        "level_policy": "AUTO",
                        "target_levels": {
                            "RQ-001": {"level": "L3", "reason": "기능 수준 검토 필요"}
                        },
                    }
                },
            )
            self.assertEqual("L1", state["observed_change_level"])
            self.assertEqual("L3", state["effective_change_level"])
            self.assertEqual("PROJECT_TARGET_OVERRIDE", state["level_source"])
            self.assertEqual("L1", state["safety_floor"])
            self.assertEqual("PROJECT_TARGET_OVERRIDE", state["level_history"][-1]["source"])
            saved = json.loads((root / "sdlc/runtime/change-level/RQ-001.json").read_text(encoding="utf-8"))
            self.assertEqual("L3", saved["effective_change_level"])

    def test_human_explicit_downgrade_is_allowed_with_reason(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = store_with_facts()
            EXEC.resolve_change(root, "RQ-001", store, {"change": {"level_policy": "MANUAL", "default_level": "L4"}})
            state = EXEC.set_human_override(
                root, "RQ-001", "L2", "실제 영향이 국소 변경으로 확인됨",
                store=store, project={"change": {"level_policy": "AUTO"}},
            )
            self.assertEqual("L2", state["effective_change_level"])
            self.assertEqual("HUMAN_OVERRIDE", state["level_source"])
            self.assertEqual("L4", state["level_history"][-1]["from"])
            self.assertEqual("L2", state["level_history"][-1]["to"])

    def test_below_safety_floor_requires_explicit_risk_acceptance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = store_with_facts(ARCHITECTURE_IMPACT="MATERIAL")
            with self.assertRaises(ValueError):
                EXEC.set_human_override(root, "RQ-001", "L2", "특별 승인", store=store, project={})
            state = EXEC.set_human_override(
                root, "RQ-001", "L2", "특별 승인",
                accept_below_safety_floor=True, store=store, project={},
            )
            self.assertEqual("L5", state["safety_floor"])
            self.assertEqual("L2", state["effective_change_level"])
            self.assertTrue(state["level_history"][-1]["risk_accepted"])

    def test_clear_human_override_rebaselines_to_auto(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            store = store_with_facts()
            EXEC.set_human_override(root, "RQ-001", "L4", "한시적 확대 검토", store=store, project={})
            EXEC.clear_human_override(root, "RQ-001", "AUTO로 복귀")
            state = EXEC.resolve_change(root, "RQ-001", store, {"change": {"level_policy": "AUTO"}})
            self.assertEqual("L1", state["effective_change_level"])
            self.assertEqual("AUTO_CLASSIFICATION", state["level_source"])
            self.assertTrue(any(x["source"] == "HUMAN_OVERRIDE_CLEARED" for x in state["level_history"]))

    def test_project_config_accepts_target_levels_and_rejects_unknown_target_key(self):
        valid = {
            "change": {
                "level_policy": "AUTO",
                "minimum_level": "L2",
                "target_levels": {
                    "RQ-001": {"level": "L3", "reason": "기능 검토"}
                },
            }
        }
        CONFIG._validate_control_plane(valid)
        classified = CONFIG.classify_project_config(valid)
        self.assertEqual([], classified["dead"])
        self.assertIn("change.target_levels.RQ-001.level", classified["runtime"])

        invalid = {
            "change": {
                "level_policy": "AUTO",
                "target_levels": {"RQ-001": {"level": "L3", "unexpected": True}},
            }
        }
        with self.assertRaises(ValueError):
            CONFIG._validate_control_plane(invalid)

    def test_hris_profile_primary_set_keeps_both_documents_at_l1_development(self):
        project = CONFIG.normalize_document_profiles(
            {
                "documents": {
                    "engineering": {"profile": "CUSTOM_HRIS_HUNEL_ENGINEERING"},
                    "customer": {"profile": "CUSTOMER_STANDARD_3"},
                    "pm": {"profile": "PM_STANDARD"},
                }
            }
        )
        result = TAILOR.resolve_artifacts(
            ROOT, project=project, target="RQ-001", stage="DEVELOPMENT", change_level="L1",
            store=store_with_facts(),
        )
        self.assertEqual("PROFILE_PRIMARY_SET", result["projection_topologies"]["internal"])
        self.assertTrue(result["change_level_controls_projection_detail_not_profile_primary_existence"])
        ids = [x["id"] for x in result["required_engineering_artifacts"]]
        self.assertEqual(["business_definition", "work_instruction"], ids)
        self.assertEqual("work_instruction", result["primary_work_artifact"]["id"])
        self.assertEqual("CONCISE", result["primary_work_artifact"]["projection_detail"])
        by_id = {x["id"]: x for x in result["required_engineering_artifacts"]}
        self.assertFalse(by_id["business_definition"]["stage_match"])
        self.assertTrue(by_id["work_instruction"]["stage_match"])

    def test_hris_profile_primary_set_keeps_both_documents_at_l4_process(self):
        project = CONFIG.normalize_document_profiles(
            {
                "documents": {
                    "engineering": {"profile": "CUSTOM_HRIS_HUNEL_ENGINEERING"},
                    "customer": {"profile": "CUSTOMER_STANDARD_3"},
                    "pm": {"profile": "PM_STANDARD"},
                }
            }
        )
        result = TAILOR.resolve_artifacts(
            ROOT, project=project, target="RQ-001", stage="PROCESS", change_level="L4",
            store=store_with_facts(),
        )
        self.assertEqual(["business_definition", "work_instruction"], [x["id"] for x in result["required_engineering_artifacts"]])
        self.assertEqual("business_definition", result["primary_work_artifact"]["id"])
        self.assertEqual("STANDARD", result["primary_work_artifact"]["projection_detail"])

    def test_standard_profiles_remain_stage_matched_by_default(self):
        profile, _ = TAILOR.load_profile(ROOT, "ENGINEERING_SDD_COMPACT")
        self.assertEqual("STAGE_MATCHED", str(profile.get("projection_topology") or "STAGE_MATCHED"))


if __name__ == "__main__":
    unittest.main()
