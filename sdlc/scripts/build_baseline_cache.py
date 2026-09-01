#!/usr/bin/env python3
import argparse
import hashlib
from pathlib import Path
import yaml


def digest(path):
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()


def detect_revision(doc):
    if not isinstance(doc, dict):
        return None
    for root_key in ("project_bootstrap", "overlay", "reference_graph", "knowledge_candidate", "glossary_entry"):
        root = doc.get(root_key)
        if isinstance(root, dict) and "revision" in root:
            return root.get("revision")
        if isinstance(root, dict) and "bootstrap_revision" in root:
            return root.get("bootstrap_revision")
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("paths", nargs="+")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--source-revision", default="")
    args = p.parse_args()

    records = []
    for raw in sorted(args.paths):
        path = Path(raw)
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        records.append({
            "path": raw,
            "sha256": digest(path),
            "declared_revision": detect_revision(doc),
        })

    cache = {
        "baseline_cache": {
            "derived_only": True,
            "contains_truth_copy": False,
            "rebuildable": True,
            "source_revision": args.source_revision,
            "records": records,
        }
    }
    Path(args.output).write_text(yaml.safe_dump(cache, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"OK: wrote rebuildable baseline cache {args.output} records={len(records)}")


if __name__ == "__main__":
    main()
