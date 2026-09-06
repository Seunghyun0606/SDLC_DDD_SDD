#!/usr/bin/env python3
"""Generate a structural Standard-3 / Standard-5 / Full Tailoring comparison.

The comparison intentionally reuses one Canonical snapshot, one target, one Change Level and one
Stage sequence. It demonstrates that Tailoring changes Human Artifact grouping without deleting or
renaming Runtime Stages and without creating Business Truth. It does not claim that independently
Agent-authored document prose is semantically identical; that requires a separate empirical/Human
review.
"""
from __future__ import annotations

import argparse
import hashlib
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


TAILOR = _load("tailoring_profile_comparison_runtime", "tailoring_runtime.py")
PROFILES = ["STANDARD_3", "STANDARD_5", "STAGE_ORIENTED_FULL"]
PROFILE_LABELS = {
    "STANDARD_3": "Standard 3",
    "STANDARD_5": "Standard 5",
    "STAGE_ORIENTED_FULL": "Full",
}
DEFAULT_STAGES = [stage for stage in TAILOR.STAGES if stage != "INTAKE"]


def _fingerprint(target: str, store: dict[str, Any]) -> str:
    entity = (store.get("entities") or {}).get(target)
    if not isinstance(entity, dict):
        raise ValueError(f"target not found in canonical store: {target}")
    related = []
    for relation in store.get("relations") or []:
        if str(relation.get("from") or "") == target or str(relation.get("to") or "") == target:
            related.append(relation)
    payload = {
        "target": entity,
        "direct_relations": sorted(related, key=lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True)),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _project(profile_id: str) -> dict[str, Any]:
    return {
        "documents": {
            "language": "ko-KR",
            "internal": {"profile": profile_id},
            "customer": {"profile": "CUSTOMER_STANDARD_3"},
            "pm": {"profile": "PM_STANDARD"},
            "machine": {"visibility": "HIDDEN"},
        }
    }


def compare(
    root: Path,
    *,
    store: dict[str, Any],
    target: str,
    change_level: str = "L3",
    stages: list[str] | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    change_level = change_level.upper()
    if change_level not in TAILOR.LEVELS:
        raise ValueError(f"unsupported change level: {change_level}")
    stage_sequence = [str(x).upper() for x in (stages or DEFAULT_STAGES)]
    unknown = [stage for stage in stage_sequence if stage not in TAILOR.STAGES]
    if unknown:
        raise ValueError("unsupported stage(s): " + ", ".join(unknown))
    canonical_fingerprint = _fingerprint(target, store)

    profiles: dict[str, Any] = {}
    for profile_id in PROFILES:
        project = _project(profile_id)
        stage_rows: list[dict[str, Any]] = []
        unique: dict[str, dict[str, Any]] = {}
        all_stage_preserved = True
        no_truth_creation = True
        for stage in stage_sequence:
            resolved = TAILOR.resolve_artifacts(
                root,
                project=project,
                target=target,
                stage=stage,
                change_level=change_level,
                store=store,
            )
            internal = resolved["affected_artifacts"]["internal"]
            artifacts = []
            for row in internal:
                artifact = {
                    "id": row.get("id"),
                    "output_path": row.get("output_path"),
                    "template": row.get("template"),
                    "visibility": row.get("visibility", "PRIMARY"),
                }
                artifacts.append(artifact)
                unique[str(row.get("id"))] = artifact
            stage_rows.append({
                "stage": stage,
                "primary_artifact": (resolved.get("primary_work_artifact") or {}).get("id"),
                "artifacts": artifacts,
            })
            all_stage_preserved = all_stage_preserved and resolved.get("stage") == stage and resolved.get("stage_preserved") is True
            no_truth_creation = no_truth_creation and resolved.get("projection_creates_business_truth") is False
        profiles[profile_id] = {
            "label": PROFILE_LABELS[profile_id],
            "canonical_fingerprint": canonical_fingerprint,
            "target_id": target,
            "change_level": change_level,
            "stage_sequence": stage_sequence,
            "unique_artifact_count": len(unique),
            "unique_artifacts": list(unique.values()),
            "stage_map": stage_rows,
            "stage_preserved": all_stage_preserved,
            "projection_creates_business_truth": not no_truth_creation,
        }

    fingerprints = {row["canonical_fingerprint"] for row in profiles.values()}
    targets = {row["target_id"] for row in profiles.values()}
    levels = {row["change_level"] for row in profiles.values()}
    stage_sequences = {tuple(row["stage_sequence"]) for row in profiles.values()}
    structural_pass = (
        len(fingerprints) == 1
        and len(targets) == 1
        and len(levels) == 1
        and len(stage_sequences) == 1
        and all(row["stage_preserved"] for row in profiles.values())
        and all(row["projection_creates_business_truth"] is False for row in profiles.values())
    )
    return {
        "schema_version": 1,
        "comparison_type": "STRUCTURAL_TAILORING_PROJECTION",
        "target_id": target,
        "canonical_revision": int(store.get("revision") or 0),
        "canonical_fingerprint": canonical_fingerprint,
        "change_level": change_level,
        "stage_sequence": stage_sequence,
        "profiles": profiles,
        "expected_document_family_counts": {
            "STANDARD_3": 3,
            "STANDARD_5": 5,
            "STAGE_ORIENTED_FULL": 10,
        },
        "structural_invariant_pass": structural_pass,
        "semantic_claim_boundary": "같은 Canonical/Stage/Change Level을 사용하고 Business Truth를 생성하지 않는 구조적 불변성만 검증한다. Agent가 실제 작성한 세 Profile 문서 본문의 의미동등성은 별도 Human/Empirical 검증 대상이다.",
    }


def render_markdown(result: dict[str, Any]) -> str:
    profiles = result["profiles"]
    lines = [
        "# Standard 3 / Standard 5 / Full Tailoring 비교 Sample",
        "",
        "> 동일 Canonical snapshot, 동일 RQ, 동일 Change Level, 동일 Runtime Stage sequence에서 Human Artifact grouping만 비교한다.",
        "> 이 결과는 실제 Agent 작성 본문의 의미동등성을 주장하지 않는다.",
        "",
        "## 비교 기준",
        "",
        f"- Target: `{result['target_id']}`",
        f"- Canonical revision: `{result['canonical_revision']}`",
        f"- Canonical fingerprint: `{result['canonical_fingerprint']}`",
        f"- Change Level: `{result['change_level']}`",
        f"- Structural invariant: `{'PASS' if result['structural_invariant_pass'] else 'FAIL'}`",
        "",
        "## 문서군 수",
        "",
        "| Profile | 고유 Human Artifact 수 | Stage 보존 | Business Truth 생성 |",
        "|---|---:|---|---|",
    ]
    for profile_id in PROFILES:
        row = profiles[profile_id]
        lines.append(
            f"| {row['label']} (`{profile_id}`) | {row['unique_artifact_count']} | "
            f"{'YES' if row['stage_preserved'] else 'NO'} | "
            f"{'YES' if row['projection_creates_business_truth'] else 'NO'} |"
        )
    lines.extend(["", "## Stage → Primary Human Artifact", ""])
    lines.append("| Runtime Stage | Standard 3 | Standard 5 | Full |")
    lines.append("|---|---|---|---|")
    by_profile = {
        profile_id: {row["stage"]: row for row in profiles[profile_id]["stage_map"]}
        for profile_id in PROFILES
    }
    for stage in result["stage_sequence"]:
        cells = []
        for profile_id in PROFILES:
            row = by_profile[profile_id][stage]
            primary = row.get("primary_artifact") or "—"
            artifacts = [x["id"] for x in row.get("artifacts") or []]
            extra = " + ".join(x for x in artifacts if x != primary)
            cells.append(f"`{primary}`" + (f" (+ `{extra}`)" if extra else ""))
        lines.append(f"| `{stage}` | {cells[0]} | {cells[1]} | {cells[2]} |")
    lines.extend(["", "## Profile별 고유 산출물", ""])
    for profile_id in PROFILES:
        row = profiles[profile_id]
        lines.append(f"### {row['label']} — {row['unique_artifact_count']}종")
        lines.append("")
        for artifact in row["unique_artifacts"]:
            lines.append(f"- `{artifact['id']}` → `{artifact['output_path']}`")
        lines.append("")
    lines.extend([
        "## 판정 경계",
        "",
        f"- {result['semantic_claim_boundary']}",
        "- 따라서 이 Sample의 PASS는 `Stage 유지 + Canonical 동일 + Projection 무변조`에 대한 구조 검증이다.",
        "- 실제 사용자 관점의 가독성·중복·누락과 Agent 작성본문의 의미 보존은 Human first-use / External Agent pilot에서 별도 검증한다.",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Compare Standard 3 / Standard 5 / Full Tailoring against one Canonical snapshot.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--store", required=True, help="Canonical-like JSON store used only as comparison input")
    ap.add_argument("--target", required=True)
    ap.add_argument("--change-level", default="L3")
    ap.add_argument("--out-json")
    ap.add_argument("--out-md")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    store_path = Path(args.store)
    if not store_path.is_absolute():
        store_path = root / store_path
    try:
        store = json.loads(store_path.read_text(encoding="utf-8"))
        if not isinstance(store, dict):
            raise ValueError("store must be a JSON object")
        result = compare(root, store=store, target=args.target, change_level=args.change_level)
        if args.out_json:
            path = Path(args.out_json)
            if not path.is_absolute():
                path = root / path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if args.out_md:
            path = Path(args.out_md)
            if not path.is_absolute():
                path = root / path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render_markdown(result), encoding="utf-8")
        print(json.dumps({
            "status": "PASS" if result["structural_invariant_pass"] else "FAIL",
            "target_id": result["target_id"],
            "canonical_fingerprint": result["canonical_fingerprint"],
            "artifact_counts": {k: v["unique_artifact_count"] for k, v in result["profiles"].items()},
            "out_json": args.out_json,
            "out_md": args.out_md,
        }, ensure_ascii=False, indent=2))
        return 0 if result["structural_invariant_pass"] else 3
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
