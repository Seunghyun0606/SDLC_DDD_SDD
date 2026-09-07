#!/usr/bin/env python3
"""Validate Canonical invariance and Engineering/Customer topology independence.

The validator deliberately does not assert a fixed Engineering or Customer document count.
Change Level controls execution/evidence/review depth; audience-local Profiles control Human Artifact
topology.  Projection resolution must not mutate Canonical meaning.
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
ENGINEERING_PROFILES = ["ENGINEERING_SDD_COMPACT", "STANDARD_3", "STANDARD_5"]
CUSTOMER_PROFILES = ["CUSTOMER_STANDARD_3", "CUSTOMER_WATERFALL_FULL"]


def _canonical_payload(store: dict[str, Any], target: str) -> dict[str, Any]:
    entity = (store.get("entities") or {}).get(target)
    if not isinstance(entity, dict):
        raise ValueError(f"target not found in canonical store: {target}")
    relations = [
        row
        for row in (store.get("relations") or [])
        if str(row.get("from") or row.get("source") or "") == target
        or str(row.get("to") or row.get("target") or "") == target
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


def _project(engineering_profile: str, customer_profile: str) -> dict[str, Any]:
    # `internal` is a runtime compatibility alias. Engineering remains the preferred project key.
    return {
        "documents": {
            "language": "ko-KR",
            "engineering": {"profile": engineering_profile},
            "internal": {"profile": engineering_profile},
            "customer": {"profile": customer_profile},
            "pm": {"profile": "PM_STANDARD"},
            "machine": {"visibility": "HIDDEN"},
        }
    }


def _collect_layer(
    root: Path,
    store: dict[str, Any],
    target: str,
    level: str,
    engineering_profile: str,
    customer_profile: str,
) -> dict[str, Any]:
    project = _project(engineering_profile, customer_profile)
    engineering: dict[str, dict[str, Any]] = {}
    customer: dict[str, dict[str, Any]] = {}
    selectors: set[str] = set()
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
            engineering[str(row["id"])] = row
        for row in resolved["affected_artifacts"]["customer"]:
            customer[str(row["id"])] = row
            for selector in (row.get("sources") or {}).get("canonical", []) or []:
                selectors.add(str(selector))
    return {
        "change_level": level,
        "engineering_profile": engineering_profile,
        "customer_profile": customer_profile,
        "canonical_fingerprint": canonical_fingerprint(store, target),
        "engineering_layer": {
            "projection_role": "ENGINEERING",
            "artifact_ids": sorted(engineering),
            "artifact_count": len(engineering),
            "authoring_modes": sorted({str(row.get("authoring") or "") for row in engineering.values()}),
        },
        "customer_layer": {
            "projection_role": "CUSTOMER",
            "artifact_ids": sorted(customer),
            "artifact_count": len(customer),
            "authoring_modes": sorted({str(row.get("authoring") or "") for row in customer.values()}),
            "canonical_selectors": sorted(selectors),
            "business_truth_authority": False,
        },
    }


def validate(root: Path, *, store: dict[str, Any], target: str) -> dict[str, Any]:
    root = root.resolve()
    before = copy.deepcopy(store)
    fingerprint = canonical_fingerprint(store, target)

    level_rows = [
        _collect_layer(root, store, target, level, "ENGINEERING_SDD_COMPACT", "CUSTOMER_STANDARD_3")
        for level in LEVELS
    ]
    canonical_level_invariant = {row["canonical_fingerprint"] for row in level_rows} == {fingerprint}

    matrix: list[dict[str, Any]] = []
    for engineering_profile in ENGINEERING_PROFILES:
        for customer_profile in CUSTOMER_PROFILES:
            matrix.append(
                _collect_layer(root, store, target, "L3", engineering_profile, customer_profile)
            )

    baseline_customer = next(
        row["customer_layer"]["artifact_ids"]
        for row in matrix
        if row["engineering_profile"] == "ENGINEERING_SDD_COMPACT"
        and row["customer_profile"] == "CUSTOMER_STANDARD_3"
    )
    customer_when_engineering_changes = {
        tuple(row["customer_layer"]["artifact_ids"])
        for row in matrix
        if row["customer_profile"] == "CUSTOMER_STANDARD_3"
    }
    customer_independent = customer_when_engineering_changes == {tuple(baseline_customer)}

    baseline_engineering = next(
        row["engineering_layer"]["artifact_ids"]
        for row in matrix
        if row["engineering_profile"] == "ENGINEERING_SDD_COMPACT"
        and row["customer_profile"] == "CUSTOMER_STANDARD_3"
    )
    engineering_when_customer_changes = {
        tuple(row["engineering_layer"]["artifact_ids"])
        for row in matrix
        if row["engineering_profile"] == "ENGINEERING_SDD_COMPACT"
    }
    engineering_independent = engineering_when_customer_changes == {tuple(baseline_engineering)}

    canonical_unchanged = before == store
    customer_truth_boundary = all(
        row["customer_layer"]["business_truth_authority"] is False for row in matrix
    )
    no_fixed_count_rule = len({row["engineering_layer"]["artifact_count"] for row in matrix}) > 1 and len(
        {row["customer_layer"]["artifact_count"] for row in matrix}
    ) > 1

    invariant_pass = all([
        canonical_level_invariant,
        canonical_unchanged,
        customer_independent,
        engineering_independent,
        customer_truth_boundary,
        no_fixed_count_rule,
    ])
    return {
        "schema_version": 2,
        "validation_type": "CANONICAL_AND_AUDIENCE_TOPOLOGY_INDEPENDENCE",
        "target_id": target,
        "canonical_revision": int(store.get("revision") or 0),
        "canonical_fingerprint": fingerprint,
        "change_levels": LEVELS,
        "canonical_change_level_invariant": canonical_level_invariant,
        "canonical_store_unchanged_by_projection_resolution": canonical_unchanged,
        "engineering_topology_independent_from_customer": engineering_independent,
        "customer_topology_independent_from_engineering": customer_independent,
        "fixed_artifact_count_is_not_an_invariant": no_fixed_count_rule,
        "customer_business_truth_authority": False,
        "level_rows": level_rows,
        "profile_matrix": matrix,
        "invariant_pass": invariant_pass,
        "interpretation": {
            "canonical": "Change Level과 Projection Profile 해석은 Canonical semantic fingerprint를 변경하지 않는다.",
            "engineering": "Engineering Profile은 개발용 Living Spec topology만 결정하며 Customer 문서 수/순번을 결정하지 않는다.",
            "customer": "Customer Profile은 제출/합의용 topology만 결정하며 Engineering 문서 수/순번을 결정하지 않는다.",
        },
        "semantic_claim_boundary": "구조적 불변성만 검증한다. Agent 작성 본문의 의미동등성과 실제 Source/Test 품질은 별도 E2E/Pilot 검증 대상이다.",
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Canonical / Engineering / Customer Projection 불변성 검증",
        "",
        f"- Target: `{result['target_id']}`",
        f"- Canonical fingerprint: `{result['canonical_fingerprint']}`",
        f"- Overall: `{'PASS' if result['invariant_pass'] else 'FAIL'}`",
        f"- Change Level → Canonical invariant: `{result['canonical_change_level_invariant']}`",
        f"- Engineering ← Customer topology independent: `{result['engineering_topology_independent_from_customer']}`",
        f"- Customer ← Engineering topology independent: `{result['customer_topology_independent_from_engineering']}`",
        f"- Fixed document count is NOT invariant: `{result['fixed_artifact_count_is_not_an_invariant']}`",
        "",
        "## Profile Matrix (L3)",
        "",
        "| Engineering Profile | Customer Profile | Engineering Count | Customer Count |",
        "|---|---|---:|---:|",
    ]
    for row in result["profile_matrix"]:
        lines.append(
            f"| `{row['engineering_profile']}` | `{row['customer_profile']}` | "
            f"{row['engineering_layer']['artifact_count']} | {row['customer_layer']['artifact_count']} |"
        )
    lines.extend([
        "",
        "Customer Projection은 Business Truth 권위를 갖지 않는다.",
        "",
        "## 판정 경계",
        "",
        f"- {result['semantic_claim_boundary']}",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate Canonical invariance and audience-local Projection topology.")
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
            "engineering_customer_independent": result["engineering_topology_independent_from_customer"],
            "customer_engineering_independent": result["customer_topology_independent_from_engineering"],
            "out_json": args.out_json,
            "out_md": args.out_md,
        }, ensure_ascii=False, indent=2))
        return 0 if result["invariant_pass"] else 3
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
