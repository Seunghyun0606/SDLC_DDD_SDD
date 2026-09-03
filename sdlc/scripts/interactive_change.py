#!/usr/bin/env python3
"""Vendor-neutral INTERACTIVE /change handoff using the common guarded finalize boundary."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CHANGE = _load("interactive_change_plan", "run_change.py")
IWORK = _load("interactive_change_guard", "interactive_work.py")
WORK = IWORK.WORK
SUCCESS = {"APPLIED", "IDEMPOTENT", "NO_CHANGE", "DRY_RUN_VALIDATED"}


def _run_dir(root: Path, target: str, raw: str | None) -> Path:
    if raw:
        path = Path(raw)
        return path.resolve() if path.is_absolute() else (root / path).resolve()
    safe = WORK.SAFE_TARGET_RE.sub("_", target).strip("_") or "TARGET"
    return root / "sdlc/runtime/change-runs" / safe


def prepare(
    root: Path, *, target: str, change_text: str, store_path: Path,
    project_profile: dict[str, Any], source_profile: dict[str, Any], artifact: str | None,
    run_dir_raw: str | None, allow_business_truth_change: bool,
) -> dict[str, Any]:
    runtime = IWORK._agent_runtime(root)
    plan = CHANGE.build_change_plan(
        root,
        target_id=target,
        change_text=change_text,
        store_path=store_path,
        artifact=artifact,
        allow_business_truth_change=allow_business_truth_change,
        project_profile=project_profile,
        source_profile=source_profile,
    )
    plan["_root"] = str(root)
    plan["selection"]["reference_path"] = "sdlc/agent/skills/change/SKILL.md"
    plan["agent_execution"] = {
        "mode": "INTERACTIVE",
        "stage_agent": "CURRENT_HOST_AGENT",
        "host_vendor": "UNSPECIFIED",
        "core_skill": "sdlc/agent/skills/change/SKILL.md",
        "provider_subprocess": False,
    }

    run_dir = _run_dir(root, target, run_dir_raw)
    run_dir.mkdir(parents=True, exist_ok=True)
    context_path = run_dir / "work-context.json"
    result_path = run_dir / "stage-result.json"
    artifact_abs, artifact_rel = WORK.safe_repo_path(root, plan["selection"]["artifact_path"])
    artifact_abs.parent.mkdir(parents=True, exist_ok=True)

    git = WORK.git_metadata(root)
    protected = set(runtime["provider_config"].get("protected_branches") or ["main", "master"])
    if git.get("available") and git.get("branch") in protected:
        return {
            "status": "FAIL_PROTECTED_BRANCH_WRITE",
            "execution_mode": "INTERACTIVE",
            "protected_branch": git.get("branch"),
            "canonical_applied": False,
            "executable": False,
        }

    dirty = WORK.git_changed_paths(root) if git.get("available") else set()
    context = dict(plan)
    context["interactive_baseline"] = {
        "git": git,
        "dirty_paths": sorted(dirty),
        "dirty_fingerprints": IWORK._fingerprints(root, dirty),
        "canonical_revision": plan["canonical"]["base_revision"],
        "artifact_hash": WORK._hash_file(artifact_abs),
    }
    context["interactive_output"] = {
        "artifact_path": artifact_rel,
        "stage_result_path": IWORK._repo_rel(root, result_path) or str(result_path),
    }
    WORK.save_json(context_path, context)

    return {
        "status": "INTERACTIVE_CHANGE_HANDOFF_READY",
        "execution_mode": "INTERACTIVE",
        "canonical_applied": False,
        "executable": False,
        "target": target,
        "stage": "CHANGE",
        "artifact_path": artifact_rel,
        "context_path": IWORK._repo_rel(root, context_path) or str(context_path),
        "result_path": IWORK._repo_rel(root, result_path) or str(result_path),
        "core_skill": "sdlc/agent/skills/change/SKILL.md",
        "instruction": "현재 Agent가 Change Core Skill과 context를 근거로 Change Artifact와 stage-result.json을 작성한 뒤 finalize를 실행한다.",
        "finalize_command": f"python sdlc/scripts/harness.py change --root {root} --target {target} --change {json.dumps(change_text, ensure_ascii=False)} --finalize --run-dir {run_dir}",
        "plan": plan,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Prepare/finalize one vendor-neutral interactive /change.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--target", required=True)
    ap.add_argument("--change", required=True)
    ap.add_argument("--artifact")
    ap.add_argument("--store", default="sdlc/canonical/store.json")
    ap.add_argument("--project-profile", default="sdlc/config/project-profile.yaml")
    ap.add_argument("--source-profile", default="sdlc/config/source-profile.yaml")
    ap.add_argument("--run-dir")
    ap.add_argument("--plan-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--allow-business-truth-change", action="store_true")
    ap.add_argument("--finalize", action="store_true")
    ap.add_argument("--result-out")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    store = Path(args.store) if Path(args.store).is_absolute() else root / args.store
    project_path = Path(args.project_profile) if Path(args.project_profile).is_absolute() else root / args.project_profile
    source_path = Path(args.source_profile) if Path(args.source_profile).is_absolute() else root / args.source_profile
    project = WORK.CONFIG.load_config(project_path)
    source = WORK.CONFIG.load_config(source_path)

    try:
        if args.finalize:
            result = IWORK.finalize(
                root,
                target=args.target,
                store_path=store,
                source_profile=source,
                run_dir_raw=args.run_dir,
                dry_run=args.dry_run,
            )
            if result.get("status") in SUCCESS:
                result["change_request"] = args.change
        else:
            result = prepare(
                root,
                target=args.target,
                change_text=args.change,
                store_path=store,
                project_profile=project,
                source_profile=source,
                artifact=args.artifact,
                run_dir_raw=args.run_dir,
                allow_business_truth_change=args.allow_business_truth_change,
            )
            if args.plan_only and result.get("status") == "INTERACTIVE_CHANGE_HANDOFF_READY":
                result["status"] = "PLAN_READY"
                result["instruction"] = "Change Plan만 생성했습니다. Artifact/Canonical은 변경하지 않았습니다."
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {
            "status": "INTERACTIVE_CHANGE_FAILED",
            "execution_mode": "INTERACTIVE",
            "error": str(exc),
            "canonical_applied": False,
            "executable": False,
        }

    if args.result_out:
        out = Path(args.result_out)
        if not out.is_absolute():
            out = root / out
        WORK.save_json(out, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in SUCCESS | {"INTERACTIVE_CHANGE_HANDOFF_READY", "PLAN_READY"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
