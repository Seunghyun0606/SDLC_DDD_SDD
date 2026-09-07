#!/usr/bin/env python3
"""Empirical SDLC cost/quality metrics runtime for Red Team Cases A-D.

No metric is fabricated. Missing observations stay null/INSUFFICIENT_EVIDENCE. Derived ROI is only
calculated when its required measurements are actually present.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = "sdlc/runtime/metrics"
METRICS = {
    "change_analysis_minutes", "impact_recall", "impact_precision", "missed_impact", "false_positive",
    "agent_draft_minutes", "human_review_minutes", "human_edit_minutes", "duplicate_content_pct", "stale_document_rate",
    "coding_start_latency_minutes", "rework_minutes", "architecture_violation_count", "source_design_mismatch_count",
    "historical_knowledge_reuse_count", "unexpected_discovery_reuse_count", "incident_analysis_minutes", "onboarding_handoff_minutes",
    "framework_command_count", "generated_artifact_count", "manual_framework_edit_count", "unsupported_ai_fact_count",
    "total_elapsed_minutes", "baseline_elapsed_minutes", "framework_input_minutes", "framework_maintenance_minutes",
    "avoided_analysis_minutes", "avoided_documentation_minutes", "avoided_rework_minutes", "avoided_handover_minutes",
    "discovery_capture_minutes", "regression_test_recall", "review_burden_rating", "semantic_equivalence_score"
}
CASES = {"CASE_A_L1_LOCAL", "CASE_B_MULTI_PROGRAM_RULE", "CASE_C_UNEXPECTED_DISCOVERY", "CASE_D_TAILORING_REVIEW"}


def now() -> str: return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
def _safe(v: str) -> str: return re.sub(r"[^A-Za-z0-9_.-]+", "_", v).strip("_") or "RUN"
def _path(root: Path, run_id: str) -> Path: return root / ROOT / f"{_safe(run_id)}.json"
def _load(path: Path) -> dict[str, Any]: return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
def _save(path: Path, data: dict[str, Any]) -> None: path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def init_run(root: Path, run_id: str, case: str, target: str) -> dict[str, Any]:
    case = case.upper()
    if case not in CASES: raise ValueError(f"unsupported empirical case: {case}")
    path = _path(root, run_id)
    if path.exists(): raise ValueError(f"metrics run already exists: {run_id}")
    data = {"schema_version": 1, "run_id": run_id, "case": case, "target": target, "execution_status": "OBSERVING", "started_at": now(), "metrics": {}, "notes": [], "empirical_pass_claimed": False}
    _save(path, data); return data


def record(root: Path, run_id: str, metric: str, value: float) -> dict[str, Any]:
    if metric not in METRICS: raise ValueError(f"unsupported metric: {metric}")
    path = _path(root, run_id); data = _load(path)
    if not data: raise ValueError(f"metrics run not found: {run_id}")
    data.setdefault("metrics", {})[metric] = float(value); data["updated_at"] = now(); _save(path, data); return data


def summarize(data: dict[str, Any]) -> dict[str, Any]:
    m = data.get("metrics") or {}
    baseline = m.get("baseline_elapsed_minutes"); total = m.get("total_elapsed_minutes")
    overhead_ratio = None
    if baseline is not None and float(baseline) > 0 and total is not None:
        overhead_ratio = (float(total) - float(baseline)) / float(baseline)
    framework_cost_keys = ["framework_input_minutes", "human_review_minutes", "human_edit_minutes", "framework_maintenance_minutes"]
    avoided_keys = ["avoided_analysis_minutes", "avoided_documentation_minutes", "avoided_rework_minutes", "avoided_handover_minutes"]
    has_roi = all(k in m for k in framework_cost_keys + avoided_keys)
    net = sum(float(m[k]) for k in avoided_keys) - sum(float(m[k]) for k in framework_cost_keys) if has_roi else None
    required_by_case = {
        "CASE_A_L1_LOCAL": ["total_elapsed_minutes", "baseline_elapsed_minutes", "framework_command_count", "generated_artifact_count", "human_review_minutes", "human_edit_minutes", "coding_start_latency_minutes", "unsupported_ai_fact_count"],
        "CASE_B_MULTI_PROGRAM_RULE": ["impact_recall", "impact_precision", "false_positive", "missed_impact", "change_analysis_minutes", "human_review_minutes", "rework_minutes", "regression_test_recall"],
        "CASE_C_UNEXPECTED_DISCOVERY": ["discovery_capture_minutes", "manual_framework_edit_count", "stale_document_rate", "unexpected_discovery_reuse_count", "regression_test_recall"],
        "CASE_D_TAILORING_REVIEW": ["human_review_minutes", "human_edit_minutes", "duplicate_content_pct", "unsupported_ai_fact_count", "review_burden_rating", "semantic_equivalence_score", "generated_artifact_count"]
    }
    required = required_by_case.get(str(data.get("case")), []); missing = [x for x in required if x not in m]
    return {
        "run_id": data.get("run_id"), "case": data.get("case"), "target": data.get("target"),
        "measurement_status": "COMPLETE" if not missing else "INSUFFICIENT_EVIDENCE",
        "missing_metrics": missing, "metrics": m,
        "framework_overhead_ratio": overhead_ratio,
        "net_sdlc_saving_minutes": net,
        "net_sdlc_saving_formula": "avoided analysis/documentation/rework/handover - framework input/review/edit/maintenance",
        "empirical_pass": None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("command", choices=["init", "record", "summary"]); ap.add_argument("--root", default="."); ap.add_argument("--run", required=True); ap.add_argument("--case"); ap.add_argument("--target"); ap.add_argument("--metric"); ap.add_argument("--value", type=float); args = ap.parse_args(argv); root = Path(args.root).resolve()
    try:
        if args.command == "init":
            if not args.case or not args.target: raise ValueError("init requires --case and --target")
            result = {"status": "METRICS_RUN_INITIALIZED", "run": init_run(root, args.run, args.case, args.target)}
        elif args.command == "record":
            if not args.metric or args.value is None: raise ValueError("record requires --metric --value")
            result = {"status": "METRIC_RECORDED", "run": record(root, args.run, args.metric, args.value)}
        else:
            data = _load(_path(root, args.run))
            if not data: raise ValueError(f"metrics run not found: {args.run}")
            result = {"status": "METRICS_SUMMARY", "summary": summarize(data)}
        print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2)); return 2


if __name__ == "__main__": raise SystemExit(main())
