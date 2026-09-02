#!/usr/bin/env python3
"""Execute one AI-SDLC /work stage with fail-closed provider and version guards.

Target identity and Stage/document selection remain independent. P0/P1 hardening adds:
- FAST/STANDARD/FULL delivery policy consumption from the project profile
- Provider unavailable is NOT a successful execution
- Git HEAD/branch/dirty-worktree/write-scope guards
- a repository write lock around Provider source/document mutation
- configured build/test commands for DEVELOPMENT before Canonical commit
- rollback of Provider changes when validation/build/test/Canonical commit fails
- locked atomic Canonical apply through apply_canonical_delta.apply_delta_to_store
- Git baseline + Canonical revision in the work context and Canonical provenance

The runtime does not auto-commit Source and does not auto-merge branches.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import time
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


APPLY = _load_module("work_apply_canonical", SCRIPT_DIR / "apply_canonical_delta.py")
VALIDATOR = _load_module("work_stage_validator", SCRIPT_DIR / "validate_agent_stage_result.py")
CONFIG = _load_module("work_runtime_config", SCRIPT_DIR / "runtime_config.py")

STAGES = [
    "INTAKE", "DECOMPOSE", "CLARIFY", "PROCESS", "DISCOVERY", "IMPACT",
    "DESIGN", "PROGRAM", "DEVELOPMENT", "TEST", "VERIFY", "KNOWLEDGE_PROMOTION",
]
STAGE_INDEX = {stage: i for i, stage in enumerate(STAGES)}
TYPE_DEFAULT_STAGE = {
    "RQ": "DECOMPOSE", "FR": "DESIGN", "BR": "CLARIFY", "SCN": "PROCESS",
    "PROC": "PROCESS", "PGM": "PROGRAM", "TASK": "DEVELOPMENT", "AC": "TEST", "TC": "TEST",
}
STAGE_ARTIFACT_NAMES = {
    "INTAKE": "requirement.md", "DECOMPOSE": "requirement.md", "CLARIFY": "interview-questions.md",
    "PROCESS": "process-analysis.md", "DISCOVERY": "impact-analysis.md", "IMPACT": "impact-analysis.md",
    "DESIGN": "functional-design.md", "PROGRAM": "program-spec.md", "DEVELOPMENT": "implementation-result.md",
    "TEST": "test-scenario.md", "VERIFY": "verification-result.md", "KNOWLEDGE_PROMOTION": "operations-knowledge.md",
}
FRONTMATTER_STAGE_RE = re.compile(r"^stage:\s*[\"']?([A-Z_]+)", re.M)
GENERATED_BY_STAGE_RE = re.compile(r"^\s*stage:\s*([A-Z_]+)\s*$", re.M)
SAFE_TARGET_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object required: {path}")
    return data


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_repo_path(root: Path, raw: str) -> tuple[Path, str]:
    rel = Path(raw)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"repository-relative safe path required: {raw}")
    root_resolved = root.resolve()
    resolved = (root_resolved / rel).resolve()
    resolved.relative_to(root_resolved)
    return resolved, rel.as_posix()


def infer_artifact_stage(path: Path) -> str | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    frontmatter = text
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end >= 0:
            frontmatter = text[4:end]
    match = FRONTMATTER_STAGE_RE.search(frontmatter) or GENERATED_BY_STAGE_RE.search(frontmatter)
    stage = match.group(1) if match else None
    if stage == "KNOWLEDGE":
        stage = "KNOWLEDGE_PROMOTION"
    return stage if stage in STAGE_INDEX else None


def _next_stage(stage: str, enabled_stages: list[str] | None = None) -> str | None:
    enabled = set(enabled_stages or STAGES)
    for candidate in STAGES[STAGE_INDEX[stage] + 1:]:
        if candidate in enabled:
            return candidate
    return None


def _related_entity_ids(store: dict[str, Any], target_id: str, max_hops: int) -> dict[str, int]:
    if target_id not in store.get("entities", {}):
        return {}
    adjacency: dict[str, set[str]] = {}
    for row in store.get("relations", []):
        left, right = str(row.get("from", "")), str(row.get("to", ""))
        if left and right:
            adjacency.setdefault(left, set()).add(right)
            adjacency.setdefault(right, set()).add(left)
    distances = {target_id: 0}
    queue: deque[tuple[str, int]] = deque([(target_id, 0)])
    while queue:
        node, distance = queue.popleft()
        if distance >= max_hops:
            continue
        for neighbor in sorted(adjacency.get(node, set())):
            if neighbor not in distances:
                distances[neighbor] = distance + 1
                queue.append((neighbor, distance + 1))
    return distances


def _artifact_referenced_entities(path: Path, store: dict[str, Any]) -> set[str]:
    if not path.is_file():
        return set()
    text = path.read_text(encoding="utf-8")
    return {entity_id for entity_id in store.get("entities", {}) if entity_id and entity_id in text}


def _latest_target_stage(entity: dict[str, Any] | None) -> str | None:
    if not entity:
        return None
    stages = []
    for row in entity.get("provenance", []):
        stage = row.get("stage")
        if stage == "KNOWLEDGE":
            stage = "KNOWLEDGE_PROMOTION"
        if stage in STAGE_INDEX:
            stages.append(stage)
    return max(stages, key=lambda x: STAGE_INDEX[x]) if stages else None


def choose_stage(
    store: dict[str, Any], target_id: str, *, explicit_stage: str | None,
    artifact_stage: str | None, enabled_stages: list[str] | None = None,
) -> tuple[str, str]:
    if explicit_stage:
        stage = explicit_stage.upper()
        if stage not in STAGE_INDEX:
            raise ValueError(f"unsupported work stage: {explicit_stage}")
        return stage, "USER_STAGE_OVERRIDE"
    if artifact_stage:
        return artifact_stage, "EXPLICIT_ARTIFACT_STAGE"
    entity = store.get("entities", {}).get(target_id)
    latest = _latest_target_stage(entity)
    if latest:
        next_stage = _next_stage(latest, enabled_stages)
        return (next_stage or latest), "TARGET_PROVENANCE_NEXT_STAGE"
    if entity:
        default = TYPE_DEFAULT_STAGE.get(str(entity.get("entity_type") or "").upper())
        if default:
            if enabled_stages and default not in enabled_stages:
                next_enabled = next((x for x in STAGES[STAGE_INDEX[default]:] if x in enabled_stages), None)
                if next_enabled:
                    return next_enabled, "TARGET_TYPE_PROFILE_ADJUSTED"
            return default, "TARGET_TYPE_DEFAULT"
    raise ValueError(f"target {target_id!r} has no resolvable stage; specify --stage or an existing --artifact with stage metadata")


def _artifact_from_provenance(root: Path, store: dict[str, Any], entity_ids: set[str], stage: str) -> str | None:
    candidates: list[str] = []
    for entity_id in entity_ids:
        for row in store.get("entities", {}).get(entity_id, {}).get("provenance", []):
            if row.get("stage") != stage:
                continue
            raw = str(row.get("source_artifact") or "").strip()
            if not raw:
                continue
            try:
                path, rel = safe_repo_path(root, raw)
            except ValueError:
                continue
            if path.is_file() and rel not in candidates:
                candidates.append(rel)
    return sorted(candidates)[-1] if candidates else None


def _git(root: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        cp = subprocess.run(["git", *args], cwd=str(root), text=True, capture_output=True, check=False, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    return cp


def git_metadata(root: Path) -> dict[str, Any]:
    inside = _git(root, "rev-parse", "--is-inside-work-tree")
    if inside is None or inside.returncode != 0 or inside.stdout.strip() != "true":
        return {"available": False}
    head = _git(root, "rev-parse", "HEAD")
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    return {
        "available": True,
        "head": head.stdout.strip() if head and head.returncode == 0 else None,
        "branch": branch.stdout.strip() if branch and branch.returncode == 0 else None,
    }


def git_changed_paths(root: Path) -> set[str]:
    meta = git_metadata(root)
    if not meta["available"]:
        return set()
    changed: set[str] = set()
    for args in [("diff", "--name-only"), ("diff", "--cached", "--name-only"), ("ls-files", "--others", "--exclude-standard")]:
        cp = _git(root, *args)
        if cp and cp.returncode == 0:
            changed.update(line.strip() for line in cp.stdout.splitlines() if line.strip())
    return changed


def _hash_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


@contextmanager
def repository_write_lock(root: Path, timeout_seconds: float = 10.0):
    meta = git_metadata(root)
    if not meta["available"]:
        yield None
        return
    git_dir_cp = _git(root, "rev-parse", "--git-dir")
    if git_dir_cp is None or git_dir_cp.returncode != 0:
        yield None
        return
    git_dir = (root / git_dir_cp.stdout.strip()).resolve() if not Path(git_dir_cp.stdout.strip()).is_absolute() else Path(git_dir_cp.stdout.strip())
    lock = git_dir / "sdlc-harness-write.lock"
    deadline = time.monotonic() + max(timeout_seconds, 0.1)
    fd = None
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, f"pid={os.getpid()} acquired_at={now()}\n".encode("utf-8"))
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise TimeoutError(f"repository write lock timeout: {lock}")
            time.sleep(0.05)
    try:
        yield lock
    finally:
        if fd is not None:
            os.close(fd)
        lock.unlink(missing_ok=True)


def _path_allowed(path: str, prefixes: list[str], exact: set[str]) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    if normalized in exact:
        return True
    return any(normalized == prefix or normalized.startswith(prefix.rstrip("/") + "/") for prefix in prefixes if prefix)


def _rollback_git_changes(root: Path, paths: set[str]) -> None:
    if not paths or not git_metadata(root)["available"]:
        return
    tracked = []
    untracked = []
    for path in sorted(paths):
        cp = _git(root, "ls-files", "--error-unmatch", "--", path)
        (tracked if cp and cp.returncode == 0 else untracked).append(path)
    if tracked:
        _git(root, "restore", "--staged", "--worktree", "--", *tracked)
    for rel in untracked:
        target = (root / rel).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            continue
        if target.is_file() or target.is_symlink():
            target.unlink(missing_ok=True)
        elif target.is_dir():
            import shutil
            shutil.rmtree(target)


def _run_commands(root: Path, commands: list[list[str]], label: str) -> list[dict[str, Any]]:
    results = []
    for command in commands:
        cp = subprocess.run(command, cwd=str(root), text=True, capture_output=True, timeout=600, check=False)
        row = {
            "label": label,
            "command": command,
            "exit_code": cp.returncode,
            "stdout": cp.stdout[-4000:],
            "stderr": cp.stderr[-4000:],
        }
        results.append(row)
        if cp.returncode != 0:
            break
    return results


def build_plan(
    root: Path, *, target_id: str, store_path: Path, stage: str | None = None,
    artifact: str | None = None, max_hops: int = 4, allow_business_truth_change: bool = False,
    project_profile: dict[str, Any] | None = None, source_profile: dict[str, Any] | None = None,
    resolved_mode: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    store = APPLY.load_store(store_path)
    profile = project_profile or {}
    policy = CONFIG.delivery_policy(profile, resolved_mode=resolved_mode) if profile else None
    enabled_stages = policy.get("enabled_stages") if policy else None
    if policy and max_hops == 4:
        max_hops = int(policy.get("graph_hops", max_hops))

    explicit_artifact_stage = None
    explicit_artifact_rel = None
    if artifact:
        artifact_path, explicit_artifact_rel = safe_repo_path(root, artifact)
        explicit_artifact_stage = infer_artifact_stage(artifact_path)
    selected_stage, stage_reason = choose_stage(
        store, target_id, explicit_stage=stage, artifact_stage=explicit_artifact_stage, enabled_stages=enabled_stages,
    )
    if explicit_artifact_stage and explicit_artifact_stage != selected_stage:
        raise ValueError(f"artifact stage {explicit_artifact_stage} conflicts with selected stage {selected_stage}")

    distances = _related_entity_ids(store, target_id, max_hops)
    allowed_existing = set(distances)
    if artifact:
        artifact_path, _ = safe_repo_path(root, artifact)
        allowed_existing.update(_artifact_referenced_entities(artifact_path, store))

    if explicit_artifact_rel:
        artifact_rel, artifact_reason = explicit_artifact_rel, "USER_ARTIFACT_OVERRIDE"
    else:
        existing = _artifact_from_provenance(root, store, allowed_existing or {target_id}, selected_stage)
        if existing:
            artifact_rel, artifact_reason = existing, "TARGET_GRAPH_EXISTING_ARTIFACT"
        else:
            safe_target = SAFE_TARGET_RE.sub("_", target_id).strip("_") or "TARGET"
            artifact_rel = f"sdlc/runtime/work/{safe_target}/{selected_stage}_{STAGE_ARTIFACT_NAMES[selected_stage]}"
            artifact_reason = "NEW_STAGE_ARTIFACT"

    reference = None
    template = None
    harness_path = root / "sdlc/design/contracts/harness-package-contract.json"
    if harness_path.is_file():
        harness = load_json(harness_path)
        stage_contract = harness.get("stage_contracts", {}).get(selected_stage) or {}
        if stage_contract.get("reference"):
            reference = f".cursor/skills/work/references/{stage_contract['reference']}"
        if stage_contract.get("template"):
            template = f"sdlc/templates/core/{stage_contract['template']}"
    template = template or f"sdlc/templates/core/{STAGE_ARTIFACT_NAMES[selected_stage]}"

    related = []
    for entity_id, distance in sorted(distances.items(), key=lambda item: (item[1], item[0])):
        entity = store["entities"][entity_id]
        related.append({"id": entity_id, "distance": distance, "entity_type": entity.get("entity_type"), "truth_status": entity.get("truth_status"), "fields": entity.get("fields", {})})

    git = git_metadata(root)
    artifact_abs, _ = safe_repo_path(root, artifact_rel)
    explicit_outside_profile = bool(policy and stage and selected_stage not in policy.get("enabled_stages", []))
    return {
        "schema_version": 2,
        "planned_at": now(),
        "target": {"id": target_id, "canonical_found": target_id in store.get("entities", {}), "entity": store.get("entities", {}).get(target_id), "graph_max_hops": max_hops, "related_entities": related},
        "selection": {
            "stage": selected_stage, "stage_reason": stage_reason, "stage_override": bool(stage),
            "artifact_path": artifact_rel, "artifact_reason": artifact_reason, "artifact_override": bool(artifact),
            "artifact_existed_at_plan_time": artifact_abs.is_file(), "artifact_hash_at_plan_time": _hash_file(artifact_abs),
            "reference_path": reference, "template_path": template,
        },
        "delivery": {
            "profile": policy.get("profile") if policy else "LEGACY_FULL_STAGE_SET",
            "mode": policy.get("mode") if policy else resolved_mode,
            "enabled_stages": policy.get("enabled_stages") if policy else list(STAGES),
            "optional_stages": policy.get("optional_stages") if policy else [],
            "program_readiness": policy.get("program_readiness") if policy else "FULL",
            "explicit_stage_outside_profile": explicit_outside_profile,
        },
        "project_context": CONFIG.nested(profile, "project_context", default={}),
        "canonical": {"store_path": str(store_path), "base_revision": store["revision"], "allowed_existing_entity_ids": sorted(allowed_existing)},
        "version_baseline": {
            "git_available": git.get("available", False), "git_commit": git.get("head"), "git_branch": git.get("branch"),
            "dirty_paths": sorted(git_changed_paths(root)), "canonical_revision": store["revision"],
        },
        "source_policy": {"allowed_write_roots": CONFIG.source_roots(source_profile or {})},
        "guards": {
            "outside_target_graph_mutation_forbidden": True,
            "confirmed_business_mutation_requires_explicit_user_authorization": True,
            "allow_business_truth_change": allow_business_truth_change,
            "source_or_stage_override_does_not_authorize_upstream_business_truth_change": True,
            "artifact_only_change_may_use_empty_operations_with_no_change_reason": True,
            "protected_branch_write_forbidden": True,
            "stale_git_head_forbidden": True,
            "dirty_workspace_forbidden_by_default": True,
        },
        "next_stage_candidate": _next_stage(selected_stage, enabled_stages),
    }


def validate_target_scope(plan: dict[str, Any], delta: dict[str, Any], store: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = set(plan["canonical"]["allowed_existing_entity_ids"])
    allow_business = bool(plan["guards"].get("allow_business_truth_change"))
    entities = store.get("entities", {})
    touched: set[str] = set()
    for op in delta.get("operations", []):
        kind = op.get("op")
        if kind in {"UPSERT_ENTITY", "ADD_PROVENANCE"}:
            touched.add(str(op.get("id") or ""))
        elif kind == "UPSERT_RELATION":
            touched.update([str(op.get("from") or ""), str(op.get("to") or "")])
    outside = sorted(entity_id for entity_id in touched if entity_id in entities and entity_id not in allowed)
    if outside:
        errors.append({"code": "OUTSIDE_TARGET_GRAPH_MUTATION", "message": "existing Canonical entities outside the target/document graph cannot be changed", "entity_ids": outside})
    if not allow_business:
        for op in delta.get("operations", []):
            if op.get("op") != "UPSERT_ENTITY":
                continue
            entity_id = str(op.get("id") or "")
            existing = entities.get(entity_id)
            incoming_truth = op.get("truth_status")
            if existing and existing.get("truth_status") == "CONFIRMED_BUSINESS":
                changed = APPLY._changed_fields(existing, op.get("fields", {}))
                status_changed = bool(incoming_truth and incoming_truth != "CONFIRMED_BUSINESS")
                if changed or status_changed:
                    errors.append({"code": "EXPLICIT_BUSINESS_TRUTH_CHANGE_REQUIRED", "message": "stage/document selection does not authorize confirmed Business Truth change", "entity_id": entity_id, "changed_fields": changed})
            elif not existing and incoming_truth == "CONFIRMED_BUSINESS":
                errors.append({"code": "EXPLICIT_BUSINESS_TRUTH_CHANGE_REQUIRED", "message": "creating confirmed Business Truth requires explicit authorization", "entity_id": entity_id})
    return errors


def _format_command(command: list[str], values: dict[str, str]) -> list[str]:
    return [part.format(**values) for part in command]


def _execution_failure(execution: dict[str, Any], status: str, *, root: Path, provider_changes: set[str]) -> dict[str, Any]:
    execution["status"] = status
    if git_metadata(root).get("available") and provider_changes:
        _rollback_git_changes(root, provider_changes)
        execution["provider_changes_rolled_back"] = sorted(provider_changes)
    return execution


def execute_plan(
    root: Path, plan: dict[str, Any], *, provider_config: dict[str, Any], run_dir: Path,
    store_path: Path, dry_run: bool = False, source_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if provider_config.get("schema_version") != 1:
        raise ValueError("provider config schema_version must be 1")
    if not provider_config.get("enabled", False):
        return {"status": "NOT_EXECUTED_PROVIDER_UNAVAILABLE_OR_DISABLED", "provider_id": provider_config.get("provider_id"), "plan": plan, "canonical_applied": False, "executable": False}
    command = provider_config.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
        raise ValueError("enabled provider config requires non-empty command array")

    root = root.resolve()
    run_dir = run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    context_path = run_dir / "work-context.json"
    result_path = run_dir / str(provider_config.get("result_filename") or "stage-result.json")
    artifact_abs, artifact_rel = safe_repo_path(root, plan["selection"]["artifact_path"])
    artifact_abs.parent.mkdir(parents=True, exist_ok=True)

    git_before = git_metadata(root)
    changed_before = git_changed_paths(root)
    execution: dict[str, Any] = {
        "status": "PRECHECK", "provider_id": provider_config.get("provider_id"), "canonical_applied": False,
        "git_baseline": git_before, "canonical_base_revision": plan["canonical"]["base_revision"],
    }
    if git_before.get("available"):
        protected = set(provider_config.get("protected_branches") or ["main", "master"])
        if git_before.get("branch") in protected and not provider_config.get("allow_protected_branch_write", False):
            execution["status"] = "FAIL_PROTECTED_BRANCH_WRITE"
            execution["protected_branch"] = git_before.get("branch")
            return execution
        if changed_before and not provider_config.get("allow_dirty_workspace", False):
            execution["status"] = "FAIL_DIRTY_WORKSPACE"
            execution["dirty_paths"] = sorted(changed_before)
            return execution

    stage = plan["selection"]["stage"]
    source_profile = source_profile or {}
    allowed_source_roots = CONFIG.source_roots(source_profile) or list(plan.get("source_policy", {}).get("allowed_write_roots", []))
    if stage == "DEVELOPMENT" and git_before.get("available") and not allowed_source_roots:
        execution["status"] = "FAIL_SOURCE_WRITE_POLICY_MISSING"
        return execution

    values = {
        "root": str(root), "run_dir": str(run_dir), "context_path": str(context_path), "result_path": str(result_path),
        "artifact_path": str(artifact_abs), "artifact_rel": artifact_rel, "target_id": str(plan["target"]["id"]), "stage": stage,
    }
    provider_changes: set[str] = set()
    try:
        with repository_write_lock(root, timeout_seconds=float(provider_config.get("write_lock_timeout_seconds", 10))):
            if git_before.get("available"):
                current = git_metadata(root)
                if current.get("head") != git_before.get("head"):
                    execution["status"] = "FAIL_STALE_GIT_HEAD"
                    execution["current_git"] = current
                    return execution
            save_json(context_path, plan)
            completed = subprocess.run(
                _format_command(command, values), cwd=str(root), text=True, capture_output=True,
                timeout=int(provider_config.get("timeout_seconds", 120)), check=False,
            )
            execution.update({
                "command_exit_code": completed.returncode, "stdout": completed.stdout[-4000:], "stderr": completed.stderr[-4000:],
                "context_path": str(context_path), "result_path": str(result_path),
            })
            changed_after = git_changed_paths(root)
            provider_changes = changed_after - changed_before
            execution["provider_changed_files"] = sorted(provider_changes)
            if completed.returncode != 0 or not result_path.is_file():
                return _execution_failure(execution, "FAIL_PROVIDER_COMMAND_OR_RESULT_MISSING", root=root, provider_changes=provider_changes)

            if git_before.get("available"):
                current = git_metadata(root)
                if current.get("head") != git_before.get("head"):
                    execution["current_git"] = current
                    return _execution_failure(execution, "FAIL_PROVIDER_CHANGED_GIT_HEAD", root=root, provider_changes=provider_changes)
                exact = {artifact_rel}
                run_rel = None
                try:
                    run_rel = run_dir.relative_to(root).as_posix()
                except ValueError:
                    pass
                prefixes = ([run_rel] if run_rel else []) + (["sdlc/runtime"] if stage != "DEVELOPMENT" else ["sdlc/runtime", *allowed_source_roots])
                outside = sorted(path for path in provider_changes if not _path_allowed(path, prefixes, exact))
                if outside:
                    execution["outside_write_scope"] = outside
                    return _execution_failure(execution, "FAIL_PROVIDER_WRITE_SCOPE", root=root, provider_changes=provider_changes)

            stage_result = load_json(result_path)
            if stage_result.get("stage") != stage:
                execution["selected_stage"], execution["actual_stage"] = stage, stage_result.get("stage")
                return _execution_failure(execution, "FAIL_SELECTED_STAGE_MISMATCH", root=root, provider_changes=provider_changes)
            if stage_result.get("artifact_path") != artifact_rel:
                execution["selected_artifact"], execution["actual_artifact"] = artifact_rel, stage_result.get("artifact_path")
                return _execution_failure(execution, "FAIL_SELECTED_ARTIFACT_MISMATCH", root=root, provider_changes=provider_changes)

            store = APPLY.load_store(store_path)
            if store["revision"] != plan["canonical"]["base_revision"]:
                execution["planned_revision"], execution["current_revision"] = plan["canonical"]["base_revision"], store["revision"]
                return _execution_failure(execution, "FAIL_PLAN_STALE_CANONICAL_REVISION", root=root, provider_changes=provider_changes)

            delta = stage_result.get("canonical_delta") if isinstance(stage_result.get("canonical_delta"), dict) else {}
            if git_before.get("available") and delta.get("operations"):
                for op in delta["operations"]:
                    if isinstance(op, dict):
                        op.setdefault("git_commit", git_before.get("head"))
                        op.setdefault("canonical_revision", plan["canonical"]["base_revision"])
                stage_result["execution_baseline"] = {
                    "git_commit": git_before.get("head"), "git_branch": git_before.get("branch"),
                    "canonical_revision": plan["canonical"]["base_revision"], "changed_files": sorted(provider_changes),
                }
                save_json(result_path, stage_result)

            scope_errors = validate_target_scope(plan, delta, store)
            if scope_errors:
                execution["scope_errors"] = scope_errors
                return _execution_failure(execution, "FAIL_TARGET_SCOPE_GUARD", root=root, provider_changes=provider_changes)

            validation = VALIDATOR.validate_stage_result(stage_result, root, store_path=store_path)
            execution["validation"] = validation
            if validation["status"] != "PASS" or not validation["executable"]:
                return _execution_failure(execution, "FAIL_STAGE_RESULT_VALIDATION", root=root, provider_changes=provider_changes)

            if stage == "DEVELOPMENT" and not dry_run:
                build_commands = CONFIG.command_list(CONFIG.nested(source_profile, "build", "commands", default=[]))
                test_commands = CONFIG.command_list(CONFIG.nested(source_profile, "test", "commands", default=[]))
                if not build_commands and not test_commands and not provider_config.get("allow_unverified_source_write", False):
                    return _execution_failure(execution, "FAIL_BUILD_TEST_COMMANDS_MISSING", root=root, provider_changes=provider_changes)
                verification = []
                if build_commands:
                    verification.extend(_run_commands(root, build_commands, "build"))
                if not verification or verification[-1]["exit_code"] == 0:
                    if test_commands:
                        verification.extend(_run_commands(root, test_commands, "test"))
                execution["source_verification"] = verification
                if verification and verification[-1]["exit_code"] != 0:
                    return _execution_failure(execution, "FAIL_BUILD_OR_TEST", root=root, provider_changes=provider_changes)

            canonical_check = validation.get("canonical_check") or {}
            if dry_run:
                execution["status"] = "DRY_RUN_VALIDATED"
                execution["canonical_status"] = canonical_check.get("status")
                return execution

            try:
                apply_result, _ = APPLY.apply_delta_to_store(store_path, delta, lock_timeout_seconds=float(provider_config.get("canonical_lock_timeout_seconds", 10)))
            except TimeoutError as exc:
                execution["canonical_error"] = str(exc)
                return _execution_failure(execution, "FAIL_CANONICAL_LOCK_TIMEOUT", root=root, provider_changes=provider_changes)
            execution["canonical_result"] = apply_result
            if apply_result["status"] == "APPLIED":
                execution["canonical_applied"], execution["status"] = True, "APPLIED"
            elif apply_result["status"] in {"IDEMPOTENT", "NO_CHANGE"}:
                execution["status"] = apply_result["status"]
            else:
                return _execution_failure(execution, "FAIL_CANONICAL_APPLY", root=root, provider_changes=provider_changes)
            execution["next_stage_candidate"] = plan.get("next_stage_candidate")
            return execution
    except TimeoutError as exc:
        execution["error"] = str(exc)
        return _execution_failure(execution, "FAIL_REPOSITORY_WRITE_LOCK_TIMEOUT", root=root, provider_changes=provider_changes)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Execute one /work stage with project profile and version guards.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--target", required=True)
    parser.add_argument("--stage")
    parser.add_argument("--artifact")
    parser.add_argument("--store", default="sdlc/canonical/store.json")
    parser.add_argument("--project-profile", default="sdlc/config/project-profile.yaml")
    parser.add_argument("--source-profile", default="sdlc/config/source-profile.yaml")
    parser.add_argument("--provider-config", default="sdlc/config/agent-provider.json")
    parser.add_argument("--run-dir")
    parser.add_argument("--plan-out")
    parser.add_argument("--result-out")
    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-hops", type=int)
    parser.add_argument("--allow-business-truth-change", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    store_path = Path(args.store) if Path(args.store).is_absolute() else root / args.store
    project_path = Path(args.project_profile) if Path(args.project_profile).is_absolute() else root / args.project_profile
    source_path = Path(args.source_profile) if Path(args.source_profile).is_absolute() else root / args.source_profile
    project_profile = CONFIG.load_config(project_path)
    source_profile = CONFIG.load_config(source_path)
    policy = CONFIG.delivery_policy(project_profile) if project_profile else None
    hops = args.max_hops if args.max_hops is not None else int(policy.get("graph_hops", 4) if policy else 4)
    try:
        plan = build_plan(
            root, target_id=args.target, store_path=store_path, stage=args.stage, artifact=args.artifact,
            max_hops=hops, allow_business_truth_change=args.allow_business_truth_change,
            project_profile=project_profile, source_profile=source_profile,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "PLAN_FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    if args.plan_out:
        save_json(Path(args.plan_out), plan)
    if args.plan_only:
        print(json.dumps({"status": "PLAN_READY", "plan": plan}, ensure_ascii=False, indent=2))
        return 0

    provider_path = Path(args.provider_config) if Path(args.provider_config).is_absolute() else root / args.provider_config
    if not provider_path.is_file():
        result = {"status": "NOT_EXECUTED_PROVIDER_CONFIG_MISSING", "provider_config": str(provider_path), "canonical_applied": False, "executable": False}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 4
    provider = load_json(provider_path)
    if args.run_dir:
        run_dir = Path(args.run_dir) if Path(args.run_dir).is_absolute() else root / args.run_dir
    else:
        safe_target = SAFE_TARGET_RE.sub("_", args.target).strip("_") or "TARGET"
        run_dir = root / "sdlc/runtime/work-runs" / f"{safe_target}-{plan['selection']['stage']}"
    try:
        result = execute_plan(root, plan, provider_config=provider, run_dir=run_dir, store_path=store_path, dry_run=args.dry_run, source_profile=source_profile)
    except (OSError, json.JSONDecodeError, ValueError, subprocess.SubprocessError) as exc:
        result = {"status": "EXECUTION_FAILED", "error": str(exc), "canonical_applied": False}
    if args.result_out:
        save_json(Path(args.result_out), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"APPLIED", "IDEMPOTENT", "NO_CHANGE", "DRY_RUN_VALIDATED"} else 3


if __name__ == "__main__":
    raise SystemExit(main())
