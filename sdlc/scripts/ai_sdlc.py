#!/usr/bin/env python3
"""Single user-facing façade for AI-SDLC bootstrap, work planning, change capture and status.

This command intentionally orchestrates existing deterministic scripts rather than reimplementing
stage/provider logic. Side-effect provider execution is never implicit.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import yaml


def load(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def dump(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")


def run(script: Path, args: list[str]) -> None:
    cp = subprocess.run([sys.executable, str(script), *args], shell=False, check=False)
    if cp.returncode != 0:
        raise SystemExit(cp.returncode)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def runtime_dir(project_root: Path) -> Path:
    return project_root / ".ai-sdlc"


def cmd_init(a: argparse.Namespace) -> int:
    root = a.project_root.resolve()
    repo = repo_root()
    rt = runtime_dir(root); rt.mkdir(parents=True, exist_ok=True)
    profile = root / a.profile
    if not profile.exists():
        template = repo / "sdlc/templates/project-profile-user.yaml"
        profile_doc = load(template)
        profile_doc.setdefault("project", {})["name"] = root.name
        dump(profile, profile_doc)
        print(f"CREATED: {profile} (project.name={root.name}, mode=AUTO, profile=STANDARD)")
    profile_doc = load(profile)
    providers_cfg = profile_doc.get("providers") or {}
    registry_raw = a.registry or providers_cfg.get("registry") or "sdlc/config/provider-registry.example.yaml"
    registry = Path(str(registry_raw)); registry = registry if registry.is_absolute() else (root / registry); registry = registry.resolve()
    if not registry.exists():
        raise SystemExit(f"provider registry not found: {registry}")
    if a.registry:
        profile_doc.setdefault("providers", {})["registry"] = a.registry
        dump(profile, profile_doc)
    registry_doc = load(registry)
    production_modules = [((p.get("extensions") or {}).get("module")) for p in ((registry_doc.get("registry") or {}).get("providers") or []) if str(((p.get("extensions") or {}).get("module")) or "").startswith("sdlc.adapters.production.") and p.get("enabled") is True]
    adapter_raw = a.adapter_config or providers_cfg.get("adapter_config")
    adapter_config = Path(str(adapter_raw)) if adapter_raw else None
    if adapter_config is not None and not adapter_config.is_absolute(): adapter_config = (root / adapter_config)
    if adapter_config is not None: adapter_config = adapter_config.resolve()
    if a.adapter_config:
        profile_doc = load(profile)
        profile_doc.setdefault("providers", {})["adapter_config"] = a.adapter_config
        dump(profile, profile_doc)
    if production_modules:
        if adapter_config is None or not adapter_config.is_file():
            raise SystemExit("production-candidate registry requires --adapter-config <path>; edit sdlc/config/adapter-config.local.example.yaml first")
        cfg = load(adapter_config).get("adapter_configs") or load(adapter_config)
        source_cfg = cfg.get("git-worktree-source") or {}
        test_cfg = cfg.get("allowlisted-subprocess-test") or {}
        source_root = Path(str(source_cfg.get("root") or ".")); source_root = source_root if source_root.is_absolute() else (root / source_root)
        test_cwd = Path(str(test_cfg.get("cwd") or ".")); test_cwd = test_cwd if test_cwd.is_absolute() else (root / test_cwd)
        if not source_root.resolve().is_dir() or not (source_root.resolve()/".git").exists():
            raise SystemExit(f"git-worktree-source.root must be an existing Git worktree: {source_root}")
        if not test_cwd.resolve().is_dir():
            raise SystemExit(f"allowlisted-subprocess-test.cwd must be a directory: {test_cwd}")
        if not (test_cfg.get("allowed_commands") or []):
            raise SystemExit("allowlisted-subprocess-test.allowed_commands must contain at least one exact argv")
    dump(rt / "runtime-binding.yaml", {"schema_version": 1, "artifact_type": "RUNTIME_BINDING", "runtime_binding": {"provider_registry": str(registry), "adapter_config": str(adapter_config) if adapter_config else None}})
    bootstrap = rt / "project-bootstrap.yaml"
    run(repo / "sdlc/scripts/bootstrap_project.py", [str(root), str(profile), str(registry), "-o", str(bootstrap)])
    run(repo / "sdlc/scripts/resolve_artifact_profile.py", [str(repo / "sdlc/config/artifact-profiles.yaml"), str(profile), "-o", str(rt / "artifact-plan.yaml")])
    run(repo / "sdlc/scripts/build_project_decision_registry.py", [str(bootstrap), str(repo / "sdlc/config/project-decisions.yaml"), "-o", str(rt / "project-decisions.yaml")])
    boot = (load(bootstrap).get("project_bootstrap") or {})
    mode = boot.get("resolved_mode")
    first_prompt = "greenfield-first-prompt.md" if mode == "GREENFIELD" else "brownfield-first-prompt.md"
    print(f"READY: mode={mode} profile={boot.get('artifact_profile')} runtime={rt}")
    print(f"FIRST_PROMPT: {repo / 'sdlc/starter/prompts' / first_prompt}")
    decision_doc = load(rt / "project-decisions.yaml")
    decision_open = ((decision_doc.get("project_decisions") or {}).get("open_items") or [])
    total_open = len(boot.get("open_items") or []) + len(decision_open)
    if total_open:
        print(f"OPEN_ITEMS: {total_open} (Project Decision 포함, OPEN은 자동으로 확정하지 않습니다.)")
    return 0


def source_revision(root: Path, explicit: str | None) -> str:
    if explicit:
        return explicit
    cp = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], shell=False, capture_output=True, text=True, check=False)
    return cp.stdout.strip() if cp.returncode == 0 else "NO_SOURCE"


def cmd_work(a: argparse.Namespace) -> int:
    root = a.project_root.resolve(); repo = repo_root(); rt = runtime_dir(root)
    bootstrap = rt / "project-bootstrap.yaml"
    if not bootstrap.exists():
        raise SystemExit("project bootstrap missing. Run: python sdlc/scripts/ai_sdlc.py init --project-root .")
    stage_pack = Path(a.stage_pack).resolve() if a.stage_pack else rt / f"stage-pack-{a.target_id}.yaml"
    if not stage_pack.exists():
        run(repo / "sdlc/scripts/create_initial_stage_pack.py", [str(bootstrap), a.target_id, source_revision(root, a.source_revision), "-o", str(stage_pack)])
    decision_registry = rt / "project-decisions.yaml"
    if decision_registry.exists():
        stage_doc = load(stage_pack)
        pack_root = stage_doc.get("stage_input_pack") or {}
        existing = list(pack_root.get("open_items") or [])
        existing_ids = {x.get("open_id") for x in existing if isinstance(x, dict)}
        decision_open = ((load(decision_registry).get("project_decisions") or {}).get("open_items") or [])
        for item in decision_open:
            if item.get("open_id") not in existing_ids:
                existing.append(item)
        pack_root["open_items"] = existing
        stage_doc["stage_input_pack"] = pack_root
        dump(stage_pack, stage_doc)
    execution = rt / f"stage-execution-{a.target_id}.yaml"
    artifact_plan = rt / "artifact-plan.yaml"
    args = [str(repo / "sdlc/config/stage-routing.yaml"), str(stage_pack), "-o", str(execution)]
    if artifact_plan.exists():
        args[2:2] = ["--artifact-plan", str(artifact_plan)]
    run(repo / "sdlc/scripts/resolve_stage_execution.py", args)
    execution_doc = load(execution)
    stage_doc = load(stage_pack)
    stage = (((stage_doc.get("stage_input_pack") or {}).get("metadata") or {}).get("stage"))
    registry = load(repo / "sdlc/config/human-artifacts.yaml")
    human = []
    for artifact_id, spec in (registry.get("artifacts") or {}).items():
        if stage in (spec.get("stages") or ([spec.get("stage")] if spec.get("stage") else [])):
            human.append({"artifact_id": artifact_id, "display_name_ko": spec.get("display_name_ko"), "template": spec.get("template")})
    summary = {"schema_version": 1, "artifact_type": "WORK_FACADE_RESULT", "work": {
        "target_id": a.target_id, "stage": stage, "stage_pack": str(stage_pack), "stage_execution": str(execution),
        "human_artifacts_for_stage": human, "side_effects_executed": False,
        "next": "Review stage execution and render/review listed Human Artifact. Provider side effects require explicit execution request."}}
    dump(rt / f"work-{a.target_id}.yaml", summary)
    print(yaml.safe_dump(summary, allow_unicode=True, sort_keys=False), end="")
    return 0


def cmd_change(a: argparse.Namespace) -> int:
    root = a.project_root.resolve(); rt = runtime_dir(root)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    change_id = a.change_id or f"CR-{stamp}"
    path = rt / "changes" / f"{change_id}.yaml"
    doc = {"schema_version": 1, "artifact_type": "CHANGE_REQUEST_CANDIDATE", "change_request": {
        "change_id": change_id, "subject_id": a.target_id, "requested_change": a.text, "truth_state": "GIVEN",
        "status": "PROPOSED", "created_at": datetime.now(timezone.utc).isoformat(),
        "open_items": [], "constraints": {"do_not_auto_confirm_impact": True, "source_write_not_requested": True}}}
    dump(path, doc)
    print(f"CREATED: {path}")
    return 0


def cmd_check(a: argparse.Namespace) -> int:
    root = a.project_root.resolve(); repo = repo_root(); rt = runtime_dir(root)
    ledger = rt / "e2e-ledger.yaml"
    if ledger.exists():
        output = rt / "e2e-status.yaml"
        run(repo / "sdlc/scripts/orchestrate_generic_e2e_status.py", [str(ledger), "-o", str(output)])
        print(output.read_text(encoding="utf-8"), end="")
        return 0
    result: dict[str, Any] = {"schema_version": 1, "artifact_type": "CHECK_FACADE_RESULT", "check": {"runtime_dir": str(rt), "artifacts": {}, "state": "NOT_INITIALIZED"}}
    if not rt.exists():
        print(yaml.safe_dump(result, allow_unicode=True, sort_keys=False), end=""); return 1
    check = result["check"]; check["state"] = "PARTIAL"
    for name in ["project-bootstrap.yaml", "project-decisions.yaml", "artifact-plan.yaml", "worklist-canonical.yaml", "knowledge-registry.yaml", "source-inventory.yaml", "e2e-status.yaml"]:
        check["artifacts"][name] = (rt / name).exists()
    if a.target_id:
        for prefix in ["stage-pack", "stage-execution", "work"]:
            check["artifacts"][f"{prefix}-{a.target_id}.yaml"] = (rt / f"{prefix}-{a.target_id}.yaml").exists()
    check["next"] = "Run work for the target or provide/update e2e-ledger.yaml. Missing runtime evidence is not success."
    print(yaml.safe_dump(result, allow_unicode=True, sort_keys=False), end="")
    return 0


def cmd_sync_worklist(a: argparse.Namespace) -> int:
    root = a.project_root.resolve(); repo = repo_root(); rt = runtime_dir(root)
    run(repo / "sdlc/scripts/sync_worklist.py", [
        "--canonical", str(rt / "worklist-canonical.yaml"),
        "--md", str(root / "docs/00_관리/전체작업목록.md"),
        "--xlsx", str(root / "docs/00_관리/전체작업목록.xlsx"),
        "--columns", str(repo / "sdlc/config/worklist-columns.yaml"),
    ])
    return 0


def cmd_promote_knowledge(a: argparse.Namespace) -> int:
    root = a.project_root.resolve(); repo = repo_root(); rt = runtime_dir(root)
    run(repo / "sdlc/scripts/promote_knowledge.py", [str(a.candidate.resolve()), "--config", str(repo / "sdlc/config/knowledge-promotion.yaml"), "--registry", str(rt / "knowledge-registry.yaml"), "--result", str(rt / "knowledge-promotion-result.yaml")])
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ai-sdlc")
    sub = p.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="bootstrap project and artifact profile")
    init.add_argument("--project-root", type=Path, default=Path(".")); init.add_argument("--profile", default="ai-sdlc.yaml"); init.add_argument("--registry"); init.add_argument("--adapter-config")
    init.set_defaults(func=cmd_init)
    work = sub.add_parser("work", help="resolve next deterministic stage plan for a target")
    work.add_argument("target_id"); work.add_argument("--project-root", type=Path, default=Path(".")); work.add_argument("--source-revision"); work.add_argument("--stage-pack")
    work.set_defaults(func=cmd_work)
    change = sub.add_parser("change", help="capture a GIVEN change request without executing side effects")
    change.add_argument("target_id"); change.add_argument("text"); change.add_argument("--change-id"); change.add_argument("--project-root", type=Path, default=Path("."))
    change.set_defaults(func=cmd_change)
    check = sub.add_parser("check", help="show current runtime/e2e status")
    check.add_argument("target_id", nargs="?"); check.add_argument("--project-root", type=Path, default=Path(".")); check.set_defaults(func=cmd_check)
    sync = sub.add_parser("sync-worklist", help="synchronize Canonical Worklist with MD/XLSX views")
    sync.add_argument("--project-root", type=Path, default=Path(".")); sync.set_defaults(func=cmd_sync_worklist)
    promote = sub.add_parser("promote-knowledge", help="promote one reviewed knowledge candidate into the project registry")
    promote.add_argument("candidate", type=Path); promote.add_argument("--project-root", type=Path, default=Path(".")); promote.set_defaults(func=cmd_promote_knowledge)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
