#!/usr/bin/env python3
"""Evaluate OPEN items with action-scoped guards; legacy fields are compatibility-only."""
import argparse
import json
import sys
from pathlib import Path
import yaml

LEGACY_ACTION_MAP = {
    "SOURCE_WRITE": "source.write",
    "DB_WRITE": "db.write",
    "CANONICAL_PUBLISH": "canonical.publish",
    "DEPLOY": "deploy.execute",
    "TEST_EXECUTION": "test.execute",
    "EXTERNAL_WRITE": "external.write",
}


def load(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def item_id(item):
    return item.get("open_id") or item.get("open_item_id")


def normalized_blocks_action(item):
    if "blocks_action" in item:
        return bool(item.get("blocks_action"))
    return bool(item.get("blocks_side_effecting_action"))


def normalized_scopes(item):
    scopes = item.get("action_scopes") or []
    if isinstance(scopes, str):
        scopes = [scopes]
    if scopes:
        return scopes
    if item.get("blocks_side_effecting_action"):
        return ["*"]
    return []


def normalized_action(action_class):
    return LEGACY_ACTION_MAP.get(action_class, action_class)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action_class")
    p.add_argument("paths", nargs="*")
    args = p.parse_args()

    action = normalized_action(args.action_class)
    items = []
    for path in args.paths:
        root = load(path).get("open_item", {})
        if root:
            items.append(root)

    active = [x for x in items if x.get("state") in {"OPEN", "ASSUMED", "DEFERRED", "GUARDED"}]
    action_blockers = []
    for item in active:
        if not normalized_blocks_action(item):
            continue
        scopes = normalized_scopes(item)
        if "*" in scopes or action in scopes:
            action_blockers.append(item)

    result = {
        "action_class": args.action_class,
        "normalized_action_scope": action,
        "active_open_items": [item_id(x) for x in active],
        "guarding_open_items": [item_id(x) for x in action_blockers],
        "decision": "GUARD" if action_blockers else "ALLOW",
        "non_side_effect_work_can_continue": True,
        "compatibility": {
            "legacy_open_item_id_supported": True,
            "legacy_blocks_side_effecting_action_supported": True,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["decision"] == "GUARD" else 0


if __name__ == "__main__":
    sys.exit(main())
