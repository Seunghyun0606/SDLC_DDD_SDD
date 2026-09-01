#!/usr/bin/env python3
"""Build Source Drift inputs directly from source, artifacts and Canonical provenance.

This removes the previous requirement that a project hand-author source manifests and
artifact-evidence indexes before every reverse check. The builder is intentionally
conservative: it creates direct source evidence when a path/hash can be proven, and
creates only CHECK_REQUIRED reverse edges between semantic artifacts that share a
Canonical entity. It never infers a Business Truth change from source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

SOURCE_EXTENSIONS = {
    ".java", ".kt", ".kts", ".groovy", ".scala", ".py", ".js", ".jsx", ".ts", ".tsx",
    ".cs", ".go", ".rs", ".c", ".cc", ".cpp", ".h", ".hpp", ".xml", ".sql", ".yaml",
    ".yml", ".properties", ".json", ".gradle", ".toml", ".sh",
}
DEFAULT_EXCLUDES = {".git", "build", "target", "node_modules", ".idea", ".gradle", "dist", "out"}
HASH_RE = re.compile(r"(?:sha256:)?([0-9a-fA-F]{64})")
LOCATOR_RE = re.compile(
    r"(?P<path>[A-Za-z0-9_./\\-]+\.(?:java|kt|kts|groovy|scala|py|js|jsx|ts|tsx|cs|go|rs|c|cc|cpp|h|hpp|xml|sql|yaml|yml|properties|json|gradle|toml|sh))"
    r"(?:#(?P<symbol>[^\s`|,;]+))?"
)
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
META_RE = re.compile(r"^\s*([A-Za-z_][\w.-]*):\s*[\"']?([^\"'\n]+)", re.M)
STAGE_ORDER = {
    "INTAKE": 0, "DECOMPOSE": 1, "CLARIFY": 2, "PROCESS": 3, "DISCOVERY": 4, "IMPACT": 5,
    "DESIGN": 6, "PROGRAM": 7, "DEVELOPMENT": 8, "TEST": 9, "VERIFY": 10,
    "KNOWLEDGE_PROMOTION": 11, "KNOWLEDGE": 11,
}


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _source_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in DEFAULT_EXCLUDES for part in rel_parts):
            continue
        yield path


def build_source_manifest(source_root: Path, source_ref: str) -> dict[str, Any]:
    source_root = source_root.resolve()
    evidence = []
    for path in _source_files(source_root):
        evidence.append({
            "path": path.relative_to(source_root).as_posix(),
            "symbol": "",
            "hash": _hash_file(path),
        })
    return {
        "schema_version": 1,
        "source_ref": source_ref,
        "source_root": str(source_root),
        "evidence": evidence,
    }


def _frontmatter_meta(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.search(text)
    if not match:
        return {}
    return {m.group(1): m.group(2).strip() for m in META_RE.finditer(match.group(1))}


def _normalize_source_locator(locator: str, source_root: Path) -> tuple[str, str] | None:
    raw = locator.strip().strip("`")
    if not raw:
        return None
    if "#" in raw:
        path_part, symbol = raw.split("#", 1)
    else:
        path_part, symbol = raw, ""
    path_part = path_part.replace("\\", "/")
    try:
        path = Path(path_part)
        if path.is_absolute():
            rel = path.resolve().relative_to(source_root.resolve()).as_posix()
        else:
            candidate = source_root / path
            if candidate.exists():
                rel = path.as_posix()
            else:
                parts = path.parts
                rel = None
                for index in range(len(parts)):
                    suffix = Path(*parts[index:])
                    if (source_root / suffix).exists():
                        rel = suffix.as_posix()
                        break
                if rel is None:
                    return None
    except (OSError, ValueError):
        return None
    return rel, symbol


def _artifact_fallback_evidence(text: str, source_root: Path) -> list[dict[str, str]]:
    rows = []
    seen = set()
    for line in text.splitlines():
        locator_match = LOCATOR_RE.search(line)
        hash_match = HASH_RE.search(line)
        if not locator_match or not hash_match:
            continue
        locator = locator_match.group("path") + (f"#{locator_match.group('symbol')}" if locator_match.group("symbol") else "")
        normalized = _normalize_source_locator(locator, source_root)
        if not normalized:
            continue
        path, symbol = normalized
        row = {"path": path, "symbol": symbol, "source_hash": "sha256:" + hash_match.group(1).lower()}
        key = (path, symbol, row["source_hash"])
        if key not in seen:
            rows.append(row)
            seen.add(key)
    return rows


def _canonical_artifact_maps(store: dict[str, Any], source_root: Path):
    evidence_by_artifact: dict[str, list[dict[str, str]]] = defaultdict(list)
    entities_by_artifact: dict[str, set[str]] = defaultdict(set)
    stage_by_artifact: dict[str, str] = {}
    for entity_id, entity in store.get("entities", {}).items():
        for prov in entity.get("provenance", []):
            artifact = str(prov.get("source_artifact") or "").strip()
            if not artifact:
                continue
            entities_by_artifact[artifact].add(entity_id)
            stage = str(prov.get("stage") or "").strip()
            if stage:
                stage_by_artifact[artifact] = stage
            source_hash = str(prov.get("source_hash") or "").strip()
            locator = str(prov.get("locator") or "").strip()
            if not source_hash or not locator:
                continue
            normalized = _normalize_source_locator(locator, source_root)
            if not normalized:
                continue
            path, symbol = normalized
            row = {"path": path, "symbol": symbol, "source_hash": source_hash}
            if row not in evidence_by_artifact[artifact]:
                evidence_by_artifact[artifact].append(row)
    return evidence_by_artifact, entities_by_artifact, stage_by_artifact


def build_artifact_index(artifact_root: Path, source_root: Path, store: dict[str, Any] | None = None) -> dict[str, Any]:
    artifact_root = artifact_root.resolve()
    source_root = source_root.resolve()
    store = store or {"entities": {}, "relations": []}
    canon_evidence, canon_entities, canon_stages = _canonical_artifact_maps(store, source_root)
    artifacts = []
    entities_by_path: dict[str, set[str]] = defaultdict(set)
    stage_by_path: dict[str, str] = {}

    for path in sorted(artifact_root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(artifact_root).as_posix()
        canonical_keys = [key for key in canon_entities if key.endswith(rel) or Path(key).name == path.name]
        entity_ids = set()
        evidence = []
        stage = None
        for key in canonical_keys:
            entity_ids.update(canon_entities[key])
            for row in canon_evidence[key]:
                if row not in evidence:
                    evidence.append(row)
            stage = canon_stages.get(key) or stage
        for entity_id in store.get("entities", {}):
            if entity_id and entity_id in text:
                entity_ids.add(entity_id)
        meta = _frontmatter_meta(text)
        stage = meta.get("stage") or stage
        if stage == "KNOWLEDGE":
            stage = "KNOWLEDGE_PROMOTION"
        if not evidence:
            evidence = _artifact_fallback_evidence(text, source_root)
        artifact_id = f"artifact:{rel}"
        artifacts.append({
            "artifact_id": artifact_id,
            "artifact_type": meta.get("document_type") or path.stem,
            "status": meta.get("status") or "CURRENT",
            "artifact_path": rel,
            "stage": stage,
            "canonical_entity_ids": sorted(entity_ids),
            "source_evidence": evidence,
        })
        entities_by_path[artifact_id] = entity_ids
        if stage:
            stage_by_path[artifact_id] = stage

    edges = []
    seen_edges = set()
    ids = [row["artifact_id"] for row in artifacts]
    for source_id in ids:
        source_stage = stage_by_path.get(source_id)
        if source_stage not in STAGE_ORDER:
            continue
        for target_id in ids:
            if source_id == target_id:
                continue
            target_stage = stage_by_path.get(target_id)
            if target_stage not in STAGE_ORDER or STAGE_ORDER[target_stage] >= STAGE_ORDER[source_stage]:
                continue
            shared = entities_by_path[source_id] & entities_by_path[target_id]
            if not shared:
                continue
            key = (source_id, target_id)
            if key in seen_edges:
                continue
            edges.append({
                "from_artifact": source_id,
                "to_artifact": target_id,
                "on_source_drift": "CHECK_REQUIRED",
                "kind": "AUTO_SHARED_CANONICAL_ENTITY_REVERSE_REVIEW",
                "note": "자동 생성된 보수적 역방향 검토 Edge. Business Truth를 자동 변경하지 않는다.",
                "shared_entity_ids": sorted(shared),
            })
            seen_edges.add(key)

    return {"schema_version": 1, "artifacts": artifacts, "propagation_edges": edges}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build source manifest and artifact evidence index for drift/reverse review.")
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--store")
    parser.add_argument("--manifest-out", required=True)
    parser.add_argument("--artifact-index-out", required=True)
    args = parser.parse_args(argv)
    source_root = Path(args.source_root)
    artifact_root = Path(args.artifact_root)
    store = None
    if args.store and Path(args.store).is_file():
        store = json.loads(Path(args.store).read_text(encoding="utf-8"))
    manifest = build_source_manifest(source_root, args.source_ref)
    index = build_artifact_index(artifact_root, source_root, store)
    Path(args.manifest_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.artifact_index_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.manifest_out).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    Path(args.artifact_index_out).write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_evidence_count": len(manifest["evidence"]),
        "artifact_count": len(index["artifacts"]),
        "propagation_edge_count": len(index["propagation_edges"]),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
