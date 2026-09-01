#!/usr/bin/env python3
"""End-to-end source drift/reverse-review check from real source + artifacts.

The first run can create a baseline. Later runs rebuild the observed manifest and artifact
index automatically, invoke detect_source_drift, and emit review candidates. No artifact
or Business Truth is auto-rewritten.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


BUILD = _load("reverse_input_builder", SCRIPT_DIR / "build_reverse_inputs.py")
DRIFT = _load("source_drift_runtime", SCRIPT_DIR / "detect_source_drift.py")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build reverse inputs automatically and run non-destructive source drift review.")
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--store", default="sdlc/canonical/store.json")
    parser.add_argument("--source-ref", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--runtime-root", default="sdlc/runtime/reverse")
    parser.add_argument("--output", required=True)
    parser.add_argument("--create-baseline", action="store_true")
    parser.add_argument("--promote-observed-to-baseline", action="store_true")
    args = parser.parse_args(argv)

    source_root = Path(args.source_root)
    artifact_root = Path(args.artifact_root)
    store_path = Path(args.store)
    runtime_root = Path(args.runtime_root)
    observed_path = runtime_root / "observed-source-manifest.json"
    index_path = runtime_root / "artifact-evidence-index.json"
    baseline_path = Path(args.baseline)

    try:
        store = _read(store_path) if store_path.is_file() else None
        observed = BUILD.build_source_manifest(source_root, args.source_ref)
        index = BUILD.build_artifact_index(artifact_root, source_root, store)
        _write(observed_path, observed)
        _write(index_path, index)
        if args.create_baseline:
            if baseline_path.exists():
                raise ValueError("baseline already exists; refuse overwrite without an explicit promotion run")
            _write(baseline_path, observed)
            result = {
                "schema_version": 1,
                "status": "BASELINE_CREATED",
                "baseline": str(baseline_path),
                "source_evidence_count": len(observed["evidence"]),
                "artifact_count": len(index["artifacts"]),
                "business_truth_modified": False,
            }
        else:
            if not baseline_path.is_file():
                raise ValueError("baseline manifest not found; run once with --create-baseline")
            result = DRIFT.analyze(_read(baseline_path), observed, index)
            result["generated_inputs"] = {
                "observed_manifest": str(observed_path),
                "artifact_index": str(index_path),
                "manual_manifest_authoring_required": False,
                "manual_artifact_index_authoring_required": False,
            }
            if args.promote_observed_to_baseline:
                baseline_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(observed_path, baseline_path)
                result["baseline_promoted"] = True
            else:
                result["baseline_promoted"] = False
        _write(Path(args.output), result)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result.get("summary", result), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
