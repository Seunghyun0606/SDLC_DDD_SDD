#!/usr/bin/env python3
"""JSON Component Baseline + accepted Change Delta = Current AS-BUILT runtime.

This is intentionally small and file-backed. It is not Event Sourcing and does not make technical
component state a Business Truth authority. The backend boundary is explicit so storage can change
later without changing the component-state contract.
"""
from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_STORE = "sdlc/runtime/component-state/store.json"
ACCEPTED = "ACCEPTED"
REJECTED = "REJECTED"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _load(path: Path, default: Any = None) -> Any:
    if not path.is_file(): return copy.deepcopy(default)
    return json.loads(path.read_text(encoding="utf-8"))


def _save(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _path_parts(raw: Any) -> list[str]:
    if isinstance(raw, list): return [str(x) for x in raw if str(x)]
    return [x for x in str(raw or "").split(".") if x]


def _set_path(state: dict[str, Any], parts: list[str], value: Any) -> None:
    if not parts: raise ValueError("operation path required")
    cur = state
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict): nxt = {}; cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = copy.deepcopy(value)


def _remove_path(state: dict[str, Any], parts: list[str]) -> None:
    if not parts: raise ValueError("operation path required")
    cur: Any = state
    for part in parts[:-1]:
        if not isinstance(cur, dict) or part not in cur: return
        cur = cur[part]
    if isinstance(cur, dict): cur.pop(parts[-1], None)


def apply_operations(state: dict[str, Any], operations: list[dict[str, Any]]) -> dict[str, Any]:
    out = copy.deepcopy(state)
    for row in operations:
        op = str(row.get("op") or "").upper(); parts = _path_parts(row.get("path"))
        if op == "SET": _set_path(out, parts, row.get("value"))
        elif op == "REMOVE": _remove_path(out, parts)
        elif op == "MERGE":
            target: dict[str, Any] = {}
            cur: Any = out
            for part in parts:
                if not isinstance(cur, dict): raise ValueError("MERGE path must resolve to object")
                if part not in cur or not isinstance(cur[part], dict): cur[part] = {}
                cur = cur[part]
            target = cur
            value = row.get("value")
            if not isinstance(value, dict): raise ValueError("MERGE value must be object")
            target.update(copy.deepcopy(value))
        else: raise ValueError(f"unsupported component operation: {op}")
    return out


class JsonComponentStateBackend:
    def __init__(self, path: Path): self.path = path
    def load(self) -> dict[str, Any]:
        data = _load(self.path, {"schema_version": 1, "backend": "JSON", "components": {}, "releases": {}})
        data.setdefault("components", {}); data.setdefault("releases", {}); return data
    def save(self, data: dict[str, Any]) -> None: _save(self.path, data)


def _component(data: dict[str, Any], component_id: str) -> dict[str, Any]:
    row = (data.get("components") or {}).get(component_id)
    if not isinstance(row, dict): raise ValueError(f"component baseline not found: {component_id}")
    return row


def register_baseline(data: dict[str, Any], component_id: str, revision: int, state: dict[str, Any], *, replace: bool = False) -> dict[str, Any]:
    components = data.setdefault("components", {})
    if component_id in components and not replace: raise ValueError(f"component baseline already exists: {component_id}")
    components[component_id] = {
        "component_id": component_id,
        "baseline_revision": int(revision),
        "current_revision": int(revision),
        "baseline": copy.deepcopy(state),
        "deltas": [],
        "compactions": [],
        "updated_at": now(),
    }
    return components[component_id]


def register_release(data: dict[str, Any], release_id: str, sequence: int) -> dict[str, Any]:
    releases = data.setdefault("releases", {})
    current = releases.get(release_id)
    if current and int(current.get("sequence") or 0) != int(sequence): raise ValueError(f"release sequence conflict: {release_id}")
    releases[release_id] = {"release_id": release_id, "sequence": int(sequence)}
    return releases[release_id]


def _accepted_deltas(component: dict[str, Any], data: dict[str, Any], release_id: str | None = None) -> list[dict[str, Any]]:
    rows = [x for x in component.get("deltas") or [] if x.get("status") == ACCEPTED and not x.get("compacted")]
    if not release_id: return rows
    release = (data.get("releases") or {}).get(release_id)
    if not release: raise ValueError(f"release not registered: {release_id}")
    seq = int(release["sequence"])
    return [x for x in rows if int(((data.get("releases") or {}).get(str(x.get("release"))) or {}).get("sequence") or 10**9) <= seq]


def reconstruct(data: dict[str, Any], component_id: str, release_id: str | None = None) -> dict[str, Any]:
    component = _component(data, component_id)
    state = copy.deepcopy(component.get("baseline") or {})
    revision = int(component.get("baseline_revision") or 0)
    applied: list[str] = []
    for delta in _accepted_deltas(component, data, release_id):
        state = apply_operations(state, list(delta.get("operations") or []))
        revision = int(delta.get("result_component_revision") or revision + 1)
        applied.append(str(delta.get("change_id")))
    return {"component_id": component_id, "release": release_id or "LATEST_ACCEPTED", "component_revision": revision, "state": state, "applied_changes": applied, "authority": "AS_BUILT_TECHNICAL_VIEW", "business_truth_authority": False}


def append_delta(data: dict[str, Any], component_id: str, *, change_id: str, base_revision: int, operations: list[dict[str, Any]], release: str, status: str = ACCEPTED, supersedes: str | None = None, revert_of: str | None = None) -> dict[str, Any]:
    component = _component(data, component_id)
    if release not in (data.get("releases") or {}): raise ValueError(f"release not registered: {release}")
    if any(str(x.get("change_id")) == change_id for x in component.get("deltas") or []): raise ValueError(f"duplicate change_id for component: {change_id}")
    status = status.upper()
    if status not in {ACCEPTED, REJECTED}: raise ValueError("status must be ACCEPTED or REJECTED")
    current = int(component.get("current_revision") or component.get("baseline_revision") or 0)
    conflict = status == ACCEPTED and int(base_revision) != current
    if conflict:
        superseded = next((x for x in reversed(component.get("deltas") or []) if str(x.get("change_id")) == str(supersedes) and x.get("status") == ACCEPTED), None) if supersedes else None
        if not superseded or int(superseded.get("result_component_revision") or -1) != current:
            return {"status": "CONFLICT", "component_id": component_id, "change_id": change_id, "expected_base_component_revision": current, "actual_base_component_revision": int(base_revision), "current_state_preserved": True}
    result_revision = current + 1 if status == ACCEPTED else current
    row = {
        "change_id": change_id,
        "base_component_revision": int(base_revision),
        "operations": copy.deepcopy(operations),
        "release": release,
        "status": status,
        "supersedes": supersedes,
        "revert_of": revert_of,
        "result_component_revision": result_revision,
        "recorded_at": now(),
        "compacted": False,
    }
    component.setdefault("deltas", []).append(row)
    if status == ACCEPTED: component["current_revision"] = result_revision
    component["updated_at"] = now()
    return {
        "status": "DELTA_RECORDED",
        "delta_status": status,
        **{key: value for key, value in row.items() if key != "status"},
    }


def compact(data: dict[str, Any], component_id: str, release_id: str) -> dict[str, Any]:
    component = _component(data, component_id); current = reconstruct(data, component_id, release_id)
    applied = set(current["applied_changes"])
    component.setdefault("compactions", []).append({"release": release_id, "through_component_revision": current["component_revision"], "change_ids": sorted(applied), "compacted_at": now()})
    component["baseline"] = current["state"]; component["baseline_revision"] = current["component_revision"]
    for row in component.get("deltas") or []:
        if row.get("change_id") in applied: row["compacted"] = True
    component["updated_at"] = now()
    return {"status": "COMPACTED", "component_id": component_id, "release": release_id, "baseline_revision": component["baseline_revision"], "compacted_changes": sorted(applied)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["baseline", "release", "delta", "current", "compact"]); ap.add_argument("--root", default="."); ap.add_argument("--store", default=DEFAULT_STORE); ap.add_argument("--component"); ap.add_argument("--revision", type=int); ap.add_argument("--state-json"); ap.add_argument("--release"); ap.add_argument("--release-seq", type=int); ap.add_argument("--change"); ap.add_argument("--base-revision", type=int); ap.add_argument("--operations-json"); ap.add_argument("--status", default=ACCEPTED); ap.add_argument("--supersedes"); ap.add_argument("--revert-of"); ap.add_argument("--replace", action="store_true")
    args = ap.parse_args(argv); root = Path(args.root).resolve(); store_path = Path(args.store); store_path = store_path if store_path.is_absolute() else root / store_path; backend = JsonComponentStateBackend(store_path); data = backend.load()
    try:
        if args.command == "baseline":
            if not args.component or args.revision is None or not args.state_json: raise ValueError("baseline requires --component --revision --state-json")
            result = {"status": "BASELINE_RECORDED", **register_baseline(data, args.component, args.revision, _load(Path(args.state_json), {}), replace=args.replace)}; backend.save(data)
        elif args.command == "release":
            if not args.release or args.release_seq is None: raise ValueError("release requires --release --release-seq")
            result = {"status": "RELEASE_RECORDED", **register_release(data, args.release, args.release_seq)}; backend.save(data)
        elif args.command == "delta":
            if not all([args.component, args.change, args.release, args.operations_json]) or args.base_revision is None: raise ValueError("delta requires --component --change --base-revision --release --operations-json")
            operations = _load(Path(args.operations_json), []); result = append_delta(data, args.component, change_id=args.change, base_revision=args.base_revision, operations=operations, release=args.release, status=args.status, supersedes=args.supersedes, revert_of=args.revert_of)
            if result.get("status") != "CONFLICT": backend.save(data)
        elif args.command == "current":
            if not args.component: raise ValueError("current requires --component")
            result = {"status": "CURRENT_AS_BUILT", **reconstruct(data, args.component, args.release)}
        else:
            if not args.component or not args.release: raise ValueError("compact requires --component --release")
            result = compact(data, args.component, args.release); backend.save(data)
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0 if result.get("status") != "CONFLICT" else 4
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2)); return 2


if __name__ == "__main__": raise SystemExit(main())
