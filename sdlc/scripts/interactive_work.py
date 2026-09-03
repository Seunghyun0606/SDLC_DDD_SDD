#!/usr/bin/env python3
"""Guarded INTERACTIVE /work runtime for IDE/CLI Agents.

INTERACTIVE means the Agent that is already running in Cursor, Codex, Claude Code, or another
repository-capable host performs the Stage work. Harness therefore must not launch a second Agent
process and must not claim Provider execution success.

The flow is deliberately two-phase:

1. prepare (default)
   - build the same canonical Target/Stage/Artifact plan as headless /work
   - capture Git/Canonical/dirty-file fingerprints
   - write ``work-context.json``
   - return ``INTERACTIVE_HANDOFF_READY``
2. the current Agent writes the selected Artifact and ``stage-result.json``
3. finalize (``--finalize``)
   - verify the baseline and write scope
   - validate Stage Result / Target Graph / Business Truth guards
   - run DEVELOPMENT build/test checks when applicable
   - apply Canonical Delta only after validation passes

Validation and Canonical apply reuse ``run_work.py`` so INTERACTIVE and HEADLESS share the same
semantic safety boundary. Interactive failures never auto-rollback user/Agent edits; they fail
closed and report ``manual_recovery_required`` instead.
"""
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


WORK = _load("interactive_guarded_work", "run_work.py")
HANDOFF = _load("interactive_work_handoff", "work_handoff.py")
SUCCESS = {"APPLIED", "IDEMPOTENT", "NO_CHANGE", "DRY_RUN_VALIDATED"}


def _repo_rel(root: Path, path: Path) -> str | None:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def _fingerprints(root: Path, paths: set[str]) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for rel in sorted(paths):
        try:
            path, safe_rel = WORK.safe_repo_path(root, rel)
        except ValueError:
            continue
        result[safe_rel] = WORK._hash_file(path)
    return result


def _changed_since_prepare(root: Path, baseline: dict[str, Any]) -> set[str]:
    before_paths = set(str(x) for x in baseline.get("dirty_paths", []) if str(x))
    after_paths = WORK.git_changed_paths(root)
    changed = after_paths - before_paths
    before_hashes = baseline.get("dirty_fingerprints") or {}
    for rel in before_paths | set(before_hashes):
        try:
            path, safe_rel = WORK.safe_repo_path(root, rel)
        except ValueError:
            continue
        if before_hashes.get(safe_rel) != WORK._hash_file(path):
            changed.add(safe_rel)
    return changed


def _run_dir(root: Path, target: str, stage: str, raw: str | None) -> Path:
    if raw:
        path = Path(raw)
        return path.resolve() if path.is_absolute() else (root / path).resolve()
    safe_target = HANDOFF._safe_name(target, "TARGET")
    return root / "sdlc/runtime/work-runs" / f"{safe_target}-{stage}"


def _agent_runtime(root: Path) -> dict[str, Any]:
    resolved = WORK.CONFIG.resolve_runtime_config(root)
    legacy_path = root / WORK.CONFIG.DEFAULT_PROVIDER_CONFIG_PATH
    legacy = WORK.CONFIG.load_config(legacy_path) if legacy_path.is_file() else {}
    runtime = WORK.CONFIG.resolve_agent_runtime(resolved["project"], legacy_provider=legacy)
    if runtime["execution_mode"] != "INTERACTIVE":
        raise ValueError(
            f"interactive_work.py requires agent.execution INTERACTIVE; resolved {runtime['execution_mode']}"
        )
    return runtime


def _prepare_plan(
    root: Path, *, target: str, store_path: Path, project_profile: dict[str, Any],
    source_profile: dict[str, Any], stage: str | None, artifact: str | None,
    max_hops: int | None, allow_business_truth_change: bool,
) -> dict[str, Any]:
    policy = WORK.CONFIG.delivery_policy(project_profile) if project_profile else None
    hops = max_hops if max_hops is not None else int(policy.get("graph_hops", 4) if policy else 4)
    plan = WORK.build_plan(
        root,
        target_id=target,
        store_path=store_path,
        stage=stage,
        artifact=artifact,
        max_hops=hops,
        allow_business_truth_change=allow_business_truth_change,
        project_profile=project_profile,
        source_profile=source_profile,
    )
    plan["_root"] = str(root)
    if not artifact:
        current = str((plan.get("selection") or {}).get("artifact_path") or "")
        if (plan.get("selection") or {}).get("artifact_reason") == "NEW_STAGE_ARTIFACT" or current.startswith("sdlc/runtime/work/"):
            rel = HANDOFF.default_document_path(plan)
            artifact_abs, rel = WORK.safe_repo_path(root, rel)
            plan["selection"].update({
                "artifact_path": rel,
                "artifact_reason": "USER_DOCUMENT_DEFAULT",
                "artifact_override": False,
                "artifact_existed_at_plan_time": artifact_abs.is_file(),
                "artifact_hash_at_plan_time": WORK._hash_file(artifact_abs),
            })
    plan["human_handoff_policy"] = HANDOFF._provider_policy()
    plan["agent_execution"] = {
        "mode": "INTERACTIVE",
        "stage_agent": "CURRENT_HOST_AGENT",
        "host_vendor": "UNSPECIFIED",
        "core_skill": "sdlc/agent/skills/work/SKILL.md",
        "provider_subprocess": False,
    }
    return plan


def prepare(
    root: Path, *, target: str, store_path: Path, project_profile: dict[str, Any],
    source_profile: dict[str, Any], stage: str | None = None, artifact: str | None = None,
    run_dir_raw: str | None = None, max_hops: int | None = None,
    allow_business_truth_change: bool = False, plan_out: Path | None = None,
) -> dict[str, Any]:
    runtime = _agent_runtime(root)
    plan = _prepare_plan(
        root,
        target=target,
        store_path=store_path,
        project_profile=project_profile,
        source_profile=source_profile,
        stage=stage,
        artifact=artifact,
        max_hops=max_hops,
        allow_business_truth_change=allow_business_truth_change,
    )
    selected_stage = plan["selection"]["stage"]
    run_dir = _run_dir(root, target, selected_stage, run_dir_raw)
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

    allowed_source_roots = WORK.CONFIG.source_roots(source_profile) or list(plan.get("source_policy", {}).get("allowed_write_roots", []))
    if selected_stage == "DEVELOPMENT" and git.get("available") and not allowed_source_roots:
        return {
            "status": "FAIL_SOURCE_WRITE_POLICY_MISSING",
            "execution_mode": "INTERACTIVE",
            "canonical_applied": False,
            "executable": False,
        }

    dirty = WORK.git_changed_paths(root) if git.get("available") else set()
    baseline = {
        "git": git,
        "dirty_paths": sorted(dirty),
        "dirty_fingerprints": _fingerprints(root, dirty),
        "canonical_revision": plan["canonical"]["base_revision"],
        "artifact_hash": WORK._hash_file(artifact_abs),
    }
    context = dict(plan)
    context["interactive_baseline"] = baseline
    context["interactive_output"] = {
        "artifact_path": artifact_rel,
        "stage_result_path": _repo_rel(root, result_path) or str(result_path),
    }
    WORK.save_json(context_path, context)
    if plan_out:
        WORK.save_json(plan_out, plan)

    return {
        "status": "INTERACTIVE_HANDOFF_READY",
        "execution_mode": "INTERACTIVE",
        "canonical_applied": False,
        "executable": False,
        "target": target,
        "stage": selected_stage,
        "artifact_path": artifact_rel,
        "context_path": _repo_rel(root, context_path) or str(context_path),
        "result_path": _repo_rel(root, result_path) or str(result_path),
        "core_skill": "sdlc/agent/skills/work/SKILL.md",
        "reference_path": plan["selection"].get("reference_path"),
        "template_path": plan["selection"].get("template_path"),
        "instruction": "현재 Agent가 Core Skill과 work-context.json을 근거로 Artifact와 stage-result.json을 작성한 뒤 finalize를 실행한다.",
        "finalize_command": f"python sdlc/scripts/harness.py work --root {root} --target {target} --finalize --run-dir {run_dir}",
        "plan": plan,
    }


def _failure(status: str, **extra: Any) -> dict[str, Any]:
    return {
        "status": status,
        "execution_mode": "INTERACTIVE",
        "canonical_applied": False,
        "executable": False,
        "manual_recovery_required": True,
        **extra,
    }


def finalize(
    root: Path, *, target: str, store_path: Path, source_profile: dict[str, Any],
    run_dir_raw: str | None, dry_run: bool = False,
) -> dict[str, Any]:
    _agent_runtime(root)
    if run_dir_raw:
        run_dir = Path(run_dir_raw)
        run_dir = run_dir.resolve() if run_dir.is_absolute() else (root / run_dir).resolve()
        candidates = [run_dir]
    else:
        base = root / "sdlc/runtime/work-runs"
        prefix = HANDOFF._safe_name(target, "TARGET") + "-"
        candidates = sorted(
            (p for p in base.glob(prefix + "*") if p.is_dir()),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ) if base.is_dir() else []
        if not candidates:
            return _failure("FAIL_INTERACTIVE_CONTEXT_MISSING", target=target)
        run_dir = candidates[0]

    context_path = run_dir / "work-context.json"
    result_path = run_dir / "stage-result.json"
    if not context_path.is_file():
        return _failure("FAIL_INTERACTIVE_CONTEXT_MISSING", context_path=str(context_path))
    if not result_path.is_file():
        return _failure("FAIL_INTERACTIVE_STAGE_RESULT_MISSING", result_path=str(result_path))

    context = WORK.load_json(context_path)
    plan = {key: value for key, value in context.items() if key not in {"interactive_baseline", "interactive_output"}}
    baseline = context.get("interactive_baseline") or {}
    if str((plan.get("target") or {}).get("id")) != target:
        return _failure("FAIL_INTERACTIVE_TARGET_MISMATCH", expected=target, actual=(plan.get("target") or {}).get("id"))

    stage = str((plan.get("selection") or {}).get("stage") or "")
    artifact_rel = str((plan.get("selection") or {}).get("artifact_path") or "")
    artifact_abs, artifact_rel = WORK.safe_repo_path(root, artifact_rel)
    git_before = baseline.get("git") or {}
    git_now = WORK.git_metadata(root)
    if git_before.get("available"):
        if not git_now.get("available") or git_now.get("head") != git_before.get("head"):
            return _failure("FAIL_STALE_GIT_HEAD", git_baseline=git_before, current_git=git_now)
        if git_now.get("branch") != git_before.get("branch"):
            return _failure("FAIL_GIT_BRANCH_CHANGED", git_baseline=git_before, current_git=git_now)

    store = WORK.APPLY.load_store(store_path)
    planned_revision = int(plan["canonical"]["base_revision"])
    if store["revision"] != planned_revision:
        return _failure(
            "FAIL_PLAN_STALE_CANONICAL_REVISION",
            planned_revision=planned_revision,
            current_revision=store["revision"],
        )

    interactive_changes = _changed_since_prepare(root, baseline) if git_now.get("available") else set()
    allowed_source_roots = WORK.CONFIG.source_roots(source_profile) or list(plan.get("source_policy", {}).get("allowed_write_roots", []))
    run_rel = _repo_rel(root, run_dir)
    exact = {artifact_rel}
    prefixes = ([run_rel] if run_rel else []) + (["sdlc/runtime"] if stage != "DEVELOPMENT" else ["sdlc/runtime", *allowed_source_roots])
    outside = sorted(path for path in interactive_changes if not WORK._path_allowed(path, prefixes, exact))
    if outside:
        return _failure(
            "FAIL_INTERACTIVE_WRITE_SCOPE",
            interactive_changed_files=sorted(interactive_changes),
            outside_write_scope=outside,
        )

    stage_result = WORK.load_json(result_path)
    if stage_result.get("stage") != stage:
        return _failure("FAIL_SELECTED_STAGE_MISMATCH", selected_stage=stage, actual_stage=stage_result.get("stage"))
    if stage_result.get("artifact_path") != artifact_rel:
        return _failure(
            "FAIL_SELECTED_ARTIFACT_MISMATCH",
            selected_artifact=artifact_rel,
            actual_artifact=stage_result.get("artifact_path"),
        )
    if not artifact_abs.is_file():
        return _failure("FAIL_SELECTED_ARTIFACT_MISSING", artifact_path=artifact_rel)

    delta = stage_result.get("canonical_delta") if isinstance(stage_result.get("canonical_delta"), dict) else {}
    if git_now.get("available") and delta.get("operations"):
        for op in delta["operations"]:
            if isinstance(op, dict):
                op.setdefault("git_commit", git_before.get("head"))
                op.setdefault("canonical_revision", planned_revision)
        stage_result["execution_baseline"] = {
            "execution_mode": "INTERACTIVE",
            "git_commit": git_before.get("head"),
            "git_branch": git_before.get("branch"),
            "canonical_revision": planned_revision,
            "changed_files": sorted(interactive_changes),
        }
        WORK.save_json(result_path, stage_result)

    scope_errors = WORK.validate_target_scope(plan, delta, store)
    if scope_errors:
        return _failure("FAIL_TARGET_SCOPE_GUARD", scope_errors=scope_errors, interactive_changed_files=sorted(interactive_changes))

    validation = WORK.VALIDATOR.validate_stage_result(stage_result, root, store_path=store_path)
    if validation["status"] != "PASS" or not validation["executable"]:
        return _failure(
            "FAIL_STAGE_RESULT_VALIDATION",
            validation=validation,
            interactive_changed_files=sorted(interactive_changes),
        )

    verification: list[dict[str, Any]] = []
    if stage == "DEVELOPMENT" and not dry_run:
        build_commands = WORK.CONFIG.command_list(WORK.CONFIG.nested(source_profile, "build", "commands", default=[]))
        test_commands = WORK.CONFIG.command_list(WORK.CONFIG.nested(source_profile, "test", "commands", default=[]))
        if not build_commands and not test_commands:
            return _failure("FAIL_BUILD_TEST_COMMANDS_MISSING", validation=validation)
        if build_commands:
            verification.extend(WORK._run_commands(root, build_commands, "build"))
        if not verification or verification[-1]["exit_code"] == 0:
            if test_commands:
                verification.extend(WORK._run_commands(root, test_commands, "test"))
        if verification and verification[-1]["exit_code"] != 0:
            return _failure("FAIL_BUILD_OR_TEST", validation=validation, source_verification=verification)

    canonical_check = validation.get("canonical_check") or {}
    execution: dict[str, Any] = {
        "execution_mode": "INTERACTIVE",
        "provider_id": "CURRENT_INTERACTIVE_AGENT",
        "context_path": str(context_path),
        "result_path": str(result_path),
        "interactive_changed_files": sorted(interactive_changes),
        "validation": validation,
        "source_verification": verification,
        "canonical_applied": False,
        "executable": True,
    }
    if dry_run:
        execution["status"] = "DRY_RUN_VALIDATED"
        execution["canonical_status"] = canonical_check.get("status")
        execution["next_stage_candidate"] = plan.get("next_stage_candidate")
        return execution

    try:
        apply_result, _ = WORK.APPLY.apply_delta_to_store(store_path, delta, lock_timeout_seconds=10)
    except TimeoutError as exc:
        return _failure("FAIL_CANONICAL_LOCK_TIMEOUT", error=str(exc), validation=validation)
    execution["canonical_result"] = apply_result
    if apply_result["status"] == "APPLIED":
        execution["canonical_applied"] = True
        execution["status"] = "APPLIED"
    elif apply_result["status"] in {"IDEMPOTENT", "NO_CHANGE"}:
        execution["status"] = apply_result["status"]
    else:
        return _failure("FAIL_CANONICAL_APPLY", canonical_result=apply_result, validation=validation)
    execution["next_stage_candidate"] = plan.get("next_stage_candidate")
    return execution


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare/finalize one vendor-neutral interactive /work Stage.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--target", required=True)
    parser.add_argument("--stage")
    parser.add_argument("--artifact")
    parser.add_argument("--store", default="sdlc/canonical/store.json")
    parser.add_argument("--project-profile", default="sdlc/config/project-profile.yaml")
    parser.add_argument("--source-profile", default="sdlc/config/source-profile.yaml")
    parser.add_argument("--run-dir")
    parser.add_argument("--plan-out")
    parser.add_argument("--result-out")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-hops", type=int)
    parser.add_argument("--allow-business-truth-change", action="store_true")
    parser.add_argument("--finalize", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    store_path = Path(args.store) if Path(args.store).is_absolute() else root / args.store
    project_path = Path(args.project_profile) if Path(args.project_profile).is_absolute() else root / args.project_profile
    source_path = Path(args.source_profile) if Path(args.source_profile).is_absolute() else root / args.source_profile
    project_profile = WORK.CONFIG.load_config(project_path)
    source_profile = WORK.CONFIG.load_config(source_path)

    try:
        if args.finalize:
            result = finalize(
                root,
                target=args.target,
                store_path=store_path,
                source_profile=source_profile,
                run_dir_raw=args.run_dir,
                dry_run=args.dry_run,
            )
            plan = None
            context_raw = result.get("context_path")
            if context_raw:
                context_path = Path(str(context_raw))
                if context_path.is_file():
                    context = WORK.load_json(context_path)
                    plan = {key: value for key, value in context.items() if key not in {"interactive_baseline", "interactive_output"}}
            if plan and result.get("status") in SUCCESS:
                handoff = HANDOFF.build_user_handoff(args.target, plan, result)
                handoff_path = HANDOFF._write_handoff(root, args.target, plan, result, handoff)
                result["user_handoff"] = handoff
                result["handoff_path"] = handoff_path.relative_to(root).as_posix()
        else:
            plan_out = None
            if args.plan_out:
                plan_out = Path(args.plan_out)
                if not plan_out.is_absolute():
                    plan_out = root / plan_out
            result = prepare(
                root,
                target=args.target,
                store_path=store_path,
                project_profile=project_profile,
                source_profile=source_profile,
                stage=args.stage,
                artifact=args.artifact,
                run_dir_raw=args.run_dir,
                max_hops=args.max_hops,
                allow_business_truth_change=args.allow_business_truth_change,
                plan_out=plan_out,
            )
            if args.plan_only and result.get("status") == "INTERACTIVE_HANDOFF_READY":
                result["status"] = "PLAN_READY"
                result["instruction"] = "Plan만 생성했습니다. Artifact/Stage Result는 작성하지 않았습니다."
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {
            "status": "INTERACTIVE_WORK_FAILED",
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
    if result.get("status") in SUCCESS | {"INTERACTIVE_HANDOFF_READY", "PLAN_READY"}:
        return 0
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
