#!/usr/bin/env python3
"""Validate that Change Level never changes Canonical semantics, only projection/work density.

This validator uses one Canonical target and resolves the Standard developer/customer projection
profiles for L1..L5. It proves structural invariants only:

- target-scoped Canonical semantic fingerprint is identical for every Change Level,
- Artifact Tailoring resolution never mutates the Canonical store,
- the Standard INTERNAL_IT document topology is stable across levels,
- the Standard CUSTOMER document topology is stable across levels,
- Customer documents remain GENERATED_VIEW and never become Business Truth.

It does not claim independently Agent-authored prose is semantically equivalent. That remains a
Human/Empirical validation boundary.
"""
from __future__ import annotations

import argparse
import copy
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


TAILOR = _load("canonical_projection_invariant_tailoring", "tailoring_runtime.py")
LEVELS = ["L1", "L2", "L3", "L4", "L5"]
STAGES = [stage for stage in TAILOR.STAGES if stage != "INTAKE"]


def _canonical_payload(store: dict[str, Any], target: str) -> dict[str, Any]:
    entity = (store.get("entities") or {}).get(target)
    if not isinstance(entity, dict):
        raise ValueError(f"target not found in canonical store: {target}")
    relations = [
        row
        for row in (store.get("relations") or [])
        if str(row.get("from") or "") == target or str(row.get("to") or "") == target
    ]
    return {
        "target": entity,
        "direct_relations": sorted(
            relations,
            key=lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True),
        ),
    }


def canonical_fingerprint(store: dict[str, Any], target: str) -> str:
    raw = json.dumps(
        _canonical_payload(store, target),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _project(profile_internal: str = "STANDARD_5") -> dict[str, Any]:
    return {
        "documents": {
            "language": "ko-KR",
            "internal": {"profile": profile_internal},
            "customer": {"profile": "CUSTOMER_STANDARD_3"},
            "pm": {"profile": "PM_STANDARD"},
            "machine": {"visibility": "HIDDEN"},
        }
    }


def _collect_level(root: Path, store: dict[str, Any], target: str, level: str) -> dict[str, Any]:
    project = _project()
    internal: dict[str, dict[str, Any]] = {}
    customer: dict[str, dict[str, Any]] = {}
    canonical_selectors: set[str] = set()
    stage_rows: list[dict[str, Any]] = []

    for stage in STAGES:
        resolved = TAILOR.resolve_artifacts(
            root,
            project=project,
            target=target,
            stage=stage,
            change_level=level,
            store=store,
        )
        if resolved.get("projection_creates_business_truth") is not False:
            raise ValueError(f"projection truth boundary violated at {level}/{stage}")
        for row in resolved["affected_artifacts"]["internal"]:
            internal[str(row["id"])] = row
        for row in resolved["affected_artifacts"]["customer"]:
            customer[str(row["id"])] = row
            for selector in (row.get("sources") or {}).get("canonical", []) or []:
                canonical_selectors.add(str(selector))
        stage_rows.append(
            {
                "stage": stage,
                "internal": sorted(str(row["id"]) for row in resolved["affected_artifacts"]["internal"]),
                "customer": sorted(str(row["id"]) for row in resolved["affected_artifacts"]["customer"]),
            }
        )

    return {
        "change_level": level,
        "canonical_fingerprint": canonical_fingerprint(store, target),
        "developer_layer": {
            "audience": "INTERNAL_IT",
            "artifact_ids": sorted(internal),
            "artifact_count": len(internal),
            "authoring_modes": sorted({str(row.get("authoring") or "") for row in internal.values()}),
            "templates": sorted({str(row.get("template") or "") for row in internal.values()}),
            "projection_role": "DESIGN_DEVELOPMENT_HUMAN_REVIEW_SURFACE",
        },
        "customer_layer": {
            "audience": "CUSTOMER",
            "artifact_ids": sorted(customer),
            "artifact_count": len(customer),
            "authoring_modes": sorted({str(row.get("authoring") or "") for row in customer.values()}),
            "templates": sorted({str(row.get("template") or "") for row in customer.values()}),
            "canonical_selectors": sorted(canonical_selectors),
            "projection_role": "GENERATED_COMMUNICATION_VIEW",
            "business_truth_authority": False,
        },
        "stage_projection_map": stage_rows,
    }


def validate(root: Path, *, store: dict[str, Any], target: str) -> dict[str, Any]:
    root = root.resolve()
    before = copy.deepcopy(store)
    fingerprint = canonical_fingerprint(store, target)
    levels = [_collect_level(root, store, target, level) for level in LEVELS]
    after = store

    fingerprints = {row["canonical_fingerprint"] for row in levels}
    developer_sets = {tuple(row["developer_layer"]["artifact_ids"]) for row in levels}
    customer_sets = {tuple(row["customer_layer"]["artifact_ids"]) for row in levels}
    developer_modes = {tuple(row["developer_layer"]["authoring_modes"]) for row in levels}
    customer_modes = {tuple(row["customer_layer"]["authoring_modes"]) for row in levels}

    canonical_unchanged = before == after
    invariant_pass = (
        fingerprints == {fingerprint}
        and len(developer_sets) == 1
        and len(customer_sets) == 1
        and developer_modes == {("AGENT_DRAFT_HUMAN_REVIEW",)}
        and customer_modes == {("GENERATED_VIEW",)}
        and all(row["customer_layer"]["business_truth_authority"] is False for row in levels)
        and canonical_unchanged
    )

    developer = levels[0]["developer_layer"]
    customer = levels[0]["customer_layer"]
    return {
        "schema_version": 1,
        "validation_type": "CANONICAL_CHANGE_LEVEL_PROJECTION_INVARIANT",
        "target_id": target,
        "canonical_revision": int(store.get("revision") or 0),
        "canonical_fingerprint": fingerprint,
        "change_levels": LEVELS,
        "canonical_change_level_invariant": len(fingerprints) == 1,
        "canonical_store_unchanged_by_projection_resolution": canonical_unchanged,
        "developer_projection_topology_invariant": len(developer_sets) == 1,
        "customer_projection_topology_invariant": len(customer_sets) == 1,
        "developer_layer": developer,
        "customer_layer": customer,
        "levels": levels,
        "invariant_pass": invariant_pass,
        "interpretation": {
            "canonical": "L1~L5는 동일 Canonical semantic identity를 공유한다. Change Level은 Canonical 필드 삭제/변경이 아니라 필요한 Semantic Work/Evidence/Review와 문서 물질화 밀도를 결정한다.",
            "developer": "INTERNAL_IT는 설계/개발자가 검토하는 Agent Draft + Human Review 문서 계층이다. 문서 Section이 축약되어도 Canonical 의미가 삭제된 것으로 해석하지 않는다.",
            "customer": "CUSTOMER는 동일 Canonical/내부 근거를 고객 자연어로 재구성한 GENERATED_VIEW다. 내부 ID/기술 상세를 숨길 수 있지만 독립 Business Truth가 아니며 고객 수정은 Canonical 자동 변경이 아니다.",
        },
        "semantic_claim_boundary": "구조적 Canonical/Projection 불변성만 검증한다. 실제 Agent 작성 본문의 의미동등성·가독성·누락 여부는 External Agent/Human Pilot에서 별도 검증한다.",
    }


def render_markdown(result: dict[str, Any]) -> str:
    dev = result["developer_layer"]
    cust = result["customer_layer"]
    lines = [
        "# Canonical Change Level / Projection 불변성 검증",
        "",
        f"- Target: `{result['target_id']}`",
        f"- Canonical revision: `{result['canonical_revision']}`",
        f"- Canonical fingerprint: `{result['canonical_fingerprint']}`",
        f"- L1~L5 invariant: `{'PASS' if result['invariant_pass'] else 'FAIL'}`",
        "",
        "## 핵심 구조",
        "",
        "```mermaid",
        "flowchart LR",
        "    C[\"Canonical Spec<br>동일 semantic identity\"] --> D[\"INTERNAL_IT<br>설계/개발자 문서\"]",
        "    C --> U[\"CUSTOMER<br>고객 Generated View\"]",
        "    L[\"Change Level L1~L5\"] --> W[\"Semantic Work / Evidence / Review 밀도\"]",
        "    W --> D",
        "    W -. 문서 밀도만 영향 .-> U",
        "    U -. 자동 변경 금지 .-> C",
        "```",
        "",
        "## 설계/개발자 Layer",
        "",
        f"- Audience: `{dev['audience']}`",
        f"- 문서군: {dev['artifact_count']}종 — " + ", ".join(f"`{x}`" for x in dev["artifact_ids"]),
        f"- Authoring: {', '.join(f'`{x}`' for x in dev['authoring_modes'])}",
        "- 목적: 설계/개발 검토 표면. Canonical 의미를 기술·구현 문맥으로 상세화한다.",
        "",
        "## 고객 Layer",
        "",
        f"- Audience: `{cust['audience']}`",
        f"- 문서군: {cust['artifact_count']}종 — " + ", ".join(f"`{x}`" for x in cust["artifact_ids"]),
        f"- Authoring: {', '.join(f'`{x}`' for x in cust['authoring_modes'])}",
        f"- Canonical selector union: {', '.join(f'`{x}`' for x in cust['canonical_selectors'])}",
        "- 목적: 고객 의사소통용 자연어 View. 내부 ID·Machine Evidence·구현 상세는 숨길 수 있다.",
        "- 고객 문서 자체는 Business Truth 권위를 갖지 않는다.",
        "",
        "## L1~L5 확인",
        "",
        "| Level | Canonical fingerprint | Internal 문서군 | Customer 문서군 |",
        "|---|---|---:|---:|",
    ]
    for row in result["levels"]:
        lines.append(
            f"| `{row['change_level']}` | `{row['canonical_fingerprint']}` | "
            f"{row['developer_layer']['artifact_count']} | {row['customer_layer']['artifact_count']} |"
        )
    lines.extend([
        "",
        "## 판정 경계",
        "",
        f"- {result['semantic_claim_boundary']}",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate Canonical invariance and audience projection topology across L1..L5.")
    ap.add_argument("--root", default=".")
    ap.add_argument("--store", default="sdlc/canonical/store.json")
    ap.add_argument("--target", required=True)
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
        result = validate(root, store=store, target=args.target)
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
            "status": "PASS" if result["invariant_pass"] else "FAIL",
            "target_id": result["target_id"],
            "canonical_fingerprint": result["canonical_fingerprint"],
            "developer_artifact_count": result["developer_layer"]["artifact_count"],
            "customer_artifact_count": result["customer_layer"]["artifact_count"],
            "out_json": args.out_json,
            "out_md": args.out_md,
        }, ensure_ascii=False, indent=2))
        return 0 if result["invariant_pass"] else 3
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
