#!/usr/bin/env python3
from __future__ import annotations
import tempfile
from pathlib import Path
import yaml
from validate_p0_exit import validate

def write(root:Path, rel:str, content:str):
 p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content,encoding="utf-8")

def main():
 with tempfile.TemporaryDirectory() as td:
  root=Path(td)
  required=["a.txt","sdlc/config/baseline-contract-index.yaml","sdlc/config/provider-registry.example.yaml","sdlc/config/runtime-invocation.yaml","sdlc/scripts/execute_command_runtime.py","sdlc/config/canonical-publish.yaml","core.txt"]
  gate={"p0_exit_gate":{"success_state":"P0_BASELINE_READY","failure_state":"P0_BASELINE_BLOCKED","required_paths":required,"required_test_definitions":[],"anti_overfitting":{"forbidden_core_tokens":["PILOT_TOKEN"],"core_paths":["core.txt"]},"external_non_p0_blockers":["actual_runtime"]}}
  write(root,"a.txt","ok")
  write(root,"sdlc/config/baseline-contract-index.yaml",yaml.safe_dump({"baseline_roles":{"a":{"authority":"a.txt"}},"truth_ownership":{"index_is_authoritative_for_content":False,"duplicate_truth_in_index":"DENY"}}))
  write(root,"sdlc/config/provider-registry.example.yaml",yaml.safe_dump({"registry":{"providers":[{"provider_type":"SOURCE","provider_state":"UNCONFIGURED"},{"provider_type":"TEST","provider_state":"UNCONFIGURED"}]}}))
  write(root,"sdlc/config/runtime-invocation.yaml",yaml.safe_dump({"runtime_invocation":{"write_retry":{"enabled":False,"unknown_after_dispatch_state":"UNKNOWN_AFTER_WRITE"}}}))
  write(root,"sdlc/scripts/execute_command_runtime.py","from route_provider_command import build_plan\nfrom invoke_provider_runtime import invoke_request\n")
  write(root,"sdlc/config/canonical-publish.yaml","required_status: CONFIRMED\npublish: guarded\n")
  write(root,"core.txt","generic core")
  result,errors=validate(root,gate); assert not errors and result["p0_exit_status"]["state"]=="P0_BASELINE_READY" and result["p0_exit_status"]["production_ready"] is False
  (root/"a.txt").unlink(); result,errors=validate(root,gate); assert any(e.startswith("P0X-001:") for e in errors)
  write(root,"a.txt","ok"); write(root,"core.txt","PILOT_TOKEN"); result,errors=validate(root,gate); assert any(e.startswith("P0X-007:") for e in errors)
  write(root,"core.txt","generic"); write(root,"sdlc/config/runtime-invocation.yaml",yaml.safe_dump({"runtime_invocation":{"write_retry":{"enabled":True,"unknown_after_dispatch_state":"UNKNOWN_AFTER_WRITE"}}})); result,errors=validate(root,gate); assert any(e.startswith("P0X-005:") for e in errors)
 print("OK: P0 design baseline exit tests passed")
 return 0
if __name__=="__main__": raise SystemExit(main())
