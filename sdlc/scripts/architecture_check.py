#!/usr/bin/env python3
"""Small static Architecture Rule PoC.

Knowledge becomes an executable Standard check. Violations remain technical findings and may be
resolved by implementation change or an explicit human exception decision.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = "sdlc/config/architecture-rules.json"


def _load(path: Path) -> dict[str, Any]: return json.loads(path.read_text(encoding="utf-8"))

def _files(root: Path, source_roots: list[str], globs: list[str]) -> list[Path]:
    rows: list[Path] = []
    for source in source_roots:
        base = root / source
        if not base.exists(): continue
        for path in base.rglob("*"):
            if path.is_file():
                rel = path.relative_to(root).as_posix()
                if any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(path.name, g) for g in globs): rows.append(path)
    return sorted(set(rows))


def check(root: Path, config: dict[str, Any], source_roots: list[str]) -> dict[str, Any]:
    exceptions = {(str(x.get("rule_id")), str(x.get("path"))) for x in config.get("exceptions") or []}
    violations: list[dict[str, Any]] = []; checked = 0
    for rule in config.get("rules") or []:
        pattern = re.compile(str(rule["forbidden_regex"])); allowed = re.compile(str(rule.get("allowed_path_regex") or r"a^"), re.I)
        for path in _files(root, source_roots, list(rule.get("file_globs") or ["**/*"])):
            rel = path.relative_to(root).as_posix(); checked += 1
            if allowed.search(rel) or (str(rule.get("id")), rel) in exceptions: continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                violations.append({"rule_id": rule["id"], "severity": rule.get("severity", "ARCH_VIOLATION"), "path": rel, "line": line, "match": match.group(0)[:120], "guidance": rule.get("guidance"), "exception_decision_required_if_kept": True})
    return {"status": "PASS" if not violations else "ARCH_VIOLATION", "checked_file_rule_pairs": checked, "violation_count": len(violations), "violations": violations, "business_truth_mutated": False}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--config", default=DEFAULT_CONFIG); ap.add_argument("--source-root", action="append", default=[]); ap.add_argument("--out"); args = ap.parse_args(argv)
    root = Path(args.root).resolve(); config_path = Path(args.config); config_path = config_path if config_path.is_absolute() else root / config_path
    try:
        config = _load(config_path); roots = args.source_root or ["src/main/java", "src/main/kotlin", "src"]
        result = check(root, config, roots)
        text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            out = Path(args.out); out = out if out.is_absolute() else root / out; out.parent.mkdir(parents=True, exist_ok=True); out.write_text(text, encoding="utf-8")
        print(text, end=""); return 0 if result["status"] == "PASS" else 5
    except (OSError, ValueError, json.JSONDecodeError, re.error) as exc:
        print(json.dumps({"status": "FAILED", "error": str(exc)}, ensure_ascii=False, indent=2)); return 2


if __name__ == "__main__": raise SystemExit(main())
