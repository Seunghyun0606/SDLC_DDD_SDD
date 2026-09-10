from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "sdlc/scripts"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


INTERACTIVE = load("primary_set_interactive_scope", "interactive_work.py")


class PrimarySetInteractiveWriteScopeV110Test(unittest.TestCase):
    def _fixture(self, root: Path) -> tuple[Path, str, str, dict]:
        primary = "docs/10_engineering/RQ-001/02_작업지시서.md"
        secondary = "docs/10_engineering/RQ-001/01_업무정의서.md"
        for rel in [primary, secondary]:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {Path(rel).name}\n", encoding="utf-8")

        run_dir = root / "sdlc/runtime/work-runs/RQ-001-DESIGN"
        run_dir.mkdir(parents=True, exist_ok=True)
        plan = {
            "target": {"id": "RQ-001"},
            "selection": {"stage": "DESIGN", "artifact_path": primary},
            "canonical": {"base_revision": 1, "allowed_existing_entity_ids": ["RQ-001"]},
            "guards": {"allow_business_truth_change": False},
            "source_policy": {"allowed_write_roots": []},
            "required_projection_targets": [
                {"id": "business_definition", "output_path": secondary},
                {"id": "work_instruction", "output_path": primary},
            ],
            "next_stage_candidate": "PROGRAM",
        }
        context = {
            **plan,
            "interactive_baseline": {
                "git": {
                    "available": True,
                    "head": "abc123",
                    "branch": "SDLC_DESIGN_SESSION_FIRST/test",
                },
                "dirty_paths": [],
                "dirty_fingerprints": {},
                "canonical_revision": 1,
            },
            "interactive_output": {
                "artifact_path": primary,
                "stage_result_path": "sdlc/runtime/work-runs/RQ-001-DESIGN/stage-result.json",
            },
        }
        (run_dir / "work-context.json").write_text(
            json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (run_dir / "stage-result.json").write_text(
            json.dumps(
                {
                    "stage": "DESIGN",
                    "artifact_path": primary,
                    "canonical_delta": {
                        "schema_version": 1,
                        "delta_id": "TEST-PRIMARY-SET",
                        "base_revision": 1,
                        "stage": "DESIGN",
                        "source_artifact": primary,
                        "operations": [],
                        "no_change_reason": "projection-only regression fixture",
                    },
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return run_dir, primary, secondary, plan

    def _common_patches(self, changed: set[str]):
        git = {
            "available": True,
            "head": "abc123",
            "branch": "SDLC_DESIGN_SESSION_FIRST/test",
        }
        return [
            mock.patch.object(INTERACTIVE, "_agent_runtime", return_value={}),
            mock.patch.object(INTERACTIVE, "_changed_since_prepare", return_value=changed),
            mock.patch.object(INTERACTIVE.WORK, "git_metadata", return_value=git),
            mock.patch.object(INTERACTIVE.WORK.APPLY, "load_store", return_value={
                "schema_version": 1,
                "revision": 1,
                "entities": {"RQ-001": {"entity_type": "RQ", "fields": {}}},
                "relations": [],
                "applied_deltas": [],
            }),
            mock.patch.object(INTERACTIVE.WORK.CONFIG, "source_roots", return_value=[]),
        ]

    def test_hris_primary_set_allows_both_required_projection_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run_dir, primary, secondary, _ = self._fixture(root)
            patches = self._common_patches({primary, secondary})
            patches += [
                mock.patch.object(INTERACTIVE.WORK, "validate_fast_path_prewrite_analysis", return_value=[]),
                mock.patch.object(INTERACTIVE.WORK, "validate_target_scope", return_value=[]),
                mock.patch.object(
                    INTERACTIVE.WORK.VALIDATOR,
                    "validate_stage_result",
                    return_value={"status": "PASS", "executable": True, "canonical_check": {"status": "PASS"}},
                ),
                mock.patch.object(
                    INTERACTIVE.WORK.APPLY,
                    "apply_delta_to_store",
                    return_value=({"status": "NO_CHANGE"}, {"revision": 1}),
                ),
            ]
            with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], patches[8]:
                result = INTERACTIVE.finalize(
                    root,
                    target="RQ-001",
                    store_path=root / "sdlc/canonical/store.json",
                    source_profile={},
                    run_dir_raw=str(run_dir),
                )

            self.assertEqual("NO_CHANGE", result["status"])
            self.assertNotIn("outside_write_scope", result)
            self.assertCountEqual([primary, secondary], result["interactive_changed_files"])

    def test_primary_set_still_blocks_unrelated_engineering_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run_dir, primary, secondary, _ = self._fixture(root)
            unrelated = "docs/10_engineering/RQ-001/99_임의문서.md"
            path = root / unrelated
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("unexpected\n", encoding="utf-8")
            patches = self._common_patches({primary, secondary, unrelated})
            with patches[0], patches[1], patches[2], patches[3], patches[4]:
                result = INTERACTIVE.finalize(
                    root,
                    target="RQ-001",
                    store_path=root / "sdlc/canonical/store.json",
                    source_profile={},
                    run_dir_raw=str(run_dir),
                )

            self.assertEqual("FAIL_INTERACTIVE_WRITE_SCOPE", result["status"])
            self.assertEqual([unrelated], result["outside_write_scope"])
            self.assertCountEqual([primary, secondary], result["allowed_projection_files"])


if __name__ == "__main__":
    unittest.main()
