#!/usr/bin/env python3
"""One-action unexpected legacy discovery capture.

Developer input is intentionally small: target + discovered component (+ optional business key).
The runtime captures historical learning, refreshes typed Change Level evidence, expands test scope,
marks affected projections stale, and creates a reconciliation CHECK_REQUIRED record. It does not
update Business Truth or AS-BUILT before an accepted implementation delta exists.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename); mod = importlib.util.module_from_spec(spec); assert spec and spec.loader; sys.modules[name] = mod; spec.loader.exec_module(mod); return mod

IMPACT = _load_module("unexpected_impact_learning", "impact_learning_runtime.py")
EXEC = _load_module("unexpected_change_execution", "change_execution_runtime.py")
CONFIG = _load_module("unexpected_runtime_config", "runtime_config_v19.py")
TAILOR = _load_module("unexpected_tailoring", "tailoring_runtime.py")


def now() -> str: return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
def _safe(v: str) -> str: return re.sub(r"[^A-Za-z0-9_.-]+", "_", v).strip("_") or "RQ"
def _read(path: Path, default: Any) -> Any:
    if not path.is_file(): return default
    return json.loads(path.read_text(encoding="utf-8"))
def _write(path: Path, data: Any) -> None: path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def capture(root: Path, *, target: str, component: str, change_id: str | None = None, keys: list[str] | None = None) -> dict[str, Any]:
    change_id = change_id or target; history_path = root / IMPACT.DEFAULT_STORE; history = _read(history_path, {"schema_version": 1, "records": []})
    captured = IMPACT.capture_discovery(root, history, change_id=change_id, target_id=target, component_id=component, keys=keys or [])
    _write(history_path, history)

    store = TAILOR.load_store(root)
    project: dict[str, Any] = {}
    if (root / CONFIG.PROJECT_ENTRY_PATH).is_file(): project = CONFIG.resolve_runtime_config(root).get("project") or {}
    change = EXEC.resolve_change(root, target, store, project, phase="DEVELOPMENT_DISCOVERY")
    execution = EXEC.resolve_execution_plan(root, change)

    test_scope_path = root / "sdlc/runtime/test-scope" / f"{_safe(target)}.json"
    test_scope = _read(test_scope_path, {"schema_version": 1, "target_id": target, "components": [], "reasons": []})
    components = sorted(set(list(test_scope.get("components") or []) + [component])); test_scope["components"] = components; test_scope.setdefault("reasons", []).append({"component_id": component, "reason": "UNEXPECTED_LEGACY_DISCOVERY", "captured_at": now()}); test_scope["regression_expansion_required"] = True; _write(test_scope_path, test_scope)

    stale_count = 0; projection_root = root / TAILOR.PROJECTION_RUNTIME_ROOT
    if projection_root.is_dir():
        for path in projection_root.glob("*.json"):
            try: row = _read(path, {})
            except (OSError, json.JSONDecodeError): continue
            if str(row.get("target_id") or "") != target: continue
            row["lifecycle"] = "STALE_VIEW"; row["stale_reason"] = "UNEXPECTED_LEGACY_DISCOVERY"; row["stale_evidence"] = f"{change_id}:{component}"; _write(path, row); stale_count += 1

    reconciliation_path = root / "sdlc/runtime/reconciliation" / f"{_safe(target)}.json"
    reconciliation = {
        "schema_version": 1, "target_id": target, "status": "CHECK_REQUIRED", "reason": "UNEXPECTED_LEGACY_DISCOVERY",
        "discovered_component": component, "captured_at": now(), "source_observation_is_business_truth": False,
        "business_truth_auto_rewritten": False, "as_built_update_allowed_before_accepted_delta": False,
        "next": "개발/테스트 후 Accepted Component Delta와 Human/Technical Evidence로 Reconcile한다."
    }
    _write(reconciliation_path, reconciliation)
    return {
        "status": "UNEXPECTED_DISCOVERY_REFRESHED", "target_id": target, "change_id": change_id, "component_id": component,
        "historical_learning": captured, "change_level": change, "execution_policy": execution,
        "test_scope": test_scope_path.relative_to(root).as_posix(), "projection_stale_count": stale_count,
        "reconciliation": reconciliation_path.relative_to(root).as_posix(), "canonical_business_truth_mutated": False,
        "as_built_mutated": False,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--target", required=True); ap.add_argument("--component", required=True); ap.add_argument("--change"); ap.add_argument("--key", action="append", default=[]); args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    try: result = capture(root, target=args.target, component=args.component, change_id=args.change, keys=args.key); print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc: print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2)); return 2


if __name__ == "__main__": raise SystemExit(main())
