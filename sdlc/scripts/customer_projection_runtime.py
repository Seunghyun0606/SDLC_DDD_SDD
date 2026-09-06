#!/usr/bin/env python3
"""Generate A01/A02/A03 Customer View and register its lifecycle metadata.

Customer View is generated from internal/canonical evidence, becomes PENDING_REVIEW, becomes
STALE_VIEW when upstream Canonical changes, and never becomes Business Truth by direct editing.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename); mod = importlib.util.module_from_spec(spec); assert spec and spec.loader; sys.modules[name] = mod; spec.loader.exec_module(mod); return mod

RENDER = _load("customer_projection_renderer", "render_customer_document.py")
LIFE = _load("customer_projection_lifecycle", "projection_lifecycle_runtime.py")

TYPE_TO_ID = {
    "solution_agreement": "A01",
    "delivery_scope": "A02",
    "acceptance_handover": "A03",
    "A01": "A01", "A02": "A02", "A03": "A03",
}


def generate(root: Path, *, target: str, document_type: str, inputs: list[str], out: str, short_name: str | None = None, contract_path: str = "sdlc/design/contracts/customer-document-contract.json", profile_path: str = "sdlc/config/customer-document-profile.example.json") -> dict:
    contract = RENDER.load(root / contract_path); profile = RENDER.load(root / profile_path); artifacts = []
    for raw in inputs:
        path = Path(raw); path = path if path.is_absolute() else root / path; artifacts.extend(RENDER.load_artifact_input(path, contract))
    projection = RENDER.project(document_type, contract, profile, artifacts, short_name); text = RENDER.render(document_type, contract, profile, projection)
    output = Path(out); output = output if output.is_absolute() else root / output; output.parent.mkdir(parents=True, exist_ok=True); output.write_text(text, encoding="utf-8")
    resolved = RENDER.resolve_document_type(document_type, contract); artifact_id = TYPE_TO_ID.get(document_type, TYPE_TO_ID.get(resolved, resolved))
    metadata = LIFE.register_generated(root, target=target, artifact_id=artifact_id, artifact_path=output.relative_to(root).as_posix(), audience="CUSTOMER", profile_id="CUSTOMER_STANDARD_3")
    return {"status": "CUSTOMER_VIEW_GENERATED", "target_id": target, "document_type": resolved, "artifact_id": artifact_id, "artifact_path": output.relative_to(root).as_posix(), "lifecycle": metadata["lifecycle"], "generated_from_revision": metadata["generated_from_revision"], "business_truth_authority": False, "customer_edit_auto_updates_canonical": False}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--root", default="."); ap.add_argument("--target", required=True); ap.add_argument("--type", required=True); ap.add_argument("--input", action="append", default=[]); ap.add_argument("--out", required=True); ap.add_argument("--short-name"); ap.add_argument("--contract", default="sdlc/design/contracts/customer-document-contract.json"); ap.add_argument("--profile", default="sdlc/config/customer-document-profile.example.json"); args = ap.parse_args(argv)
    try: result = generate(Path(args.root).resolve(), target=args.target, document_type=args.type, inputs=args.input, out=args.out, short_name=args.short_name, contract_path=args.contract, profile_path=args.profile); print(json.dumps(result, ensure_ascii=False, indent=2)); return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc: print(json.dumps({"status":"FAILED","error":str(exc)}, ensure_ascii=False, indent=2)); return 2


if __name__ == "__main__": raise SystemExit(main())
