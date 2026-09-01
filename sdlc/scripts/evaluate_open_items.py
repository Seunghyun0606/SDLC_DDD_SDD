#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
import yaml

SIDE_EFFECTING = {"SOURCE_WRITE", "DB_WRITE", "CANONICAL_PUBLISH", "DEPLOY", "TEST_EXECUTION", "EXTERNAL_WRITE"}


def load(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action_class")
    p.add_argument("paths", nargs="*")
    args = p.parse_args()

    items = []
    for path in args.paths:
        root = load(path).get("open_item", {})
        if root:
            items.append(root)

    active = [x for x in items if x.get("state") in {"OPEN", "ASSUMED", "DEFERRED", "GUARDED"}]
    blockers = [x for x in active if x.get("blocks_side_effecting_action")]
    side_effecting = args.action_class in SIDE_EFFECTING

    result = {
        "action_class": args.action_class,
        "side_effecting": side_effecting,
        "active_open_items": [x.get("open_item_id") for x in active],
        "guarding_open_items": [x.get("open_item_id") for x in blockers],
        "decision": "GUARD" if side_effecting and blockers else "ALLOW",
        "non_side_effect_work_can_continue": True,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["decision"] == "GUARD" else 0


if __name__ == "__main__":
    sys.exit(main())
