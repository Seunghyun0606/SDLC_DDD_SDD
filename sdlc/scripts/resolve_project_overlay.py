#!/usr/bin/env python3
import argparse
import copy
import sys
from pathlib import Path
import yaml


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def set_path(doc, dotted_key, value):
    parts = dotted_key.split(".")
    cur = doc
    for part in parts[:-1]:
        if part not in cur or not isinstance(cur[part], dict):
            cur[part] = {}
        cur = cur[part]
    cur[parts[-1]] = value


def main():
    p = argparse.ArgumentParser()
    p.add_argument("profile")
    p.add_argument("overlays", nargs="*")
    p.add_argument("-o", "--output", required=True)
    args = p.parse_args()

    resolved = copy.deepcopy(load_yaml(args.profile))
    applied = []
    skipped = []

    for path in args.overlays:
        root = load_yaml(path).get("overlay", {})
        overlay_id = root.get("overlay_id", path)
        if root.get("state") != "ACTIVE":
            skipped.append({"overlay_id": overlay_id, "reason": "NOT_ACTIVE"})
            continue
        safety = root.get("safety", {})
        if safety.get("copies_core_truth") or safety.get("sample_specific_only"):
            print(f"DENY {overlay_id}: unsafe overlay", file=sys.stderr)
            return 2
        change = root.get("change", {})
        key = change.get("target_key")
        if not key:
            print(f"DENY {overlay_id}: target_key missing", file=sys.stderr)
            return 2
        set_path(resolved, key, change.get("project_value"))
        applied.append({
            "overlay_id": overlay_id,
            "target_key": key,
            "revision": root.get("revision"),
        })

    output = {
        "resolved_project_configuration": resolved,
        "overlay_resolution": {
            "strategy": "LATE_BOUND_OVERLAY",
            "applied": applied,
            "skipped": skipped,
            "generated_from": args.profile,
        },
    }
    Path(args.output).write_text(yaml.safe_dump(output, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"OK: wrote {args.output}; applied={len(applied)} skipped={len(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
