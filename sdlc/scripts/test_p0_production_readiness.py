#!/usr/bin/env python3
"""Self-test for P0 production-readiness primitives.

This test uses a temporary real Git worktree and actual subprocess execution. It is still not a
customer-source validation, so the report explicitly keeps real_customer_source_validated=false.
"""
from __future__ import annotations

import hashlib
import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
import yaml

HARNESS_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = HARNESS_ROOT / "sdlc" / "scripts"
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from sdlc.adapters.production import git_worktree_source, subprocess_test  # noqa: E402
import analyze_interface_contract  # noqa: E402
import manage_source_claims  # noqa: E402
import render_human_artifact  # noqa: E402


def git(root: Path, *args: str) -> str:
    cp = subprocess.run(["git", "-C", str(root), *args], shell=False, capture_output=True, text=True, check=True)
    return cp.stdout.strip()


def init_repo(root: Path) -> str:
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    git(root, "config", "user.email", "p0-selftest@example.invalid")
    git(root, "config", "user.name", "P0 Selftest")
    (root / "src").mkdir(parents=True)
    (root / "src" / "Service.java").write_text("class Service { String value() { return \"A\"; } }\n", encoding="utf-8")
    (root / "contracts").mkdir()
    (root / "contracts" / "openapi.yaml").write_text(
        "openapi: 3.0.0\ninfo: {title: Selftest, version: '1'}\npaths:\n  /yellow-page:\n    post:\n      operationId: sendWorkPlan\n      responses:\n        '200': {description: ok}\n",
        encoding="utf-8",
    )
    git(root, "add", "."); git(root, "commit", "-q", "-m", "baseline")
    git(root, "checkout", "-q", "-b", "agent/REQ-1/TASK-1/selftest")
    return git(root, "rev-parse", "HEAD")


def request(req_id: str, provider_type: str, operation: str, mode="BROWNFIELD", write=False, expected=None, ext=None):
    return {"provider_request": {"request_id": req_id, "provider_type": provider_type, "operation": operation,
        "project_context": {"project_id": "SELFTEST", "mode": mode}, "target": {"target_type": "RQ", "target_id": "REQ-1"},
        "inputs": [], "write_intent": write, "expected_revision": expected, "idempotency_key": "SELFTEST-1" if write else None,
        "permission_proof_ref": "SELFTEST-PERMISSION" if write else None, "constraints": {"do_not_invent_missing_result": True},
        "extensions": ext or {}}}


def main() -> int:
    checks: dict[str, dict] = {}
    with tempfile.TemporaryDirectory(prefix="ai-sdlc-p0-") as tmp:
        root = Path(tmp) / "project"; root.mkdir()
        head = init_repo(root)

        snap = git_worktree_source.invoke(request("R1", "SOURCE", "source.snapshot.read", ext={"root": str(root)}), {"root": str(root)})
        checks["git_source_snapshot"] = {"pass": snap["provider_response"]["status"] == "OK", "status": snap["provider_response"]["status"]}

        store = root / ".ai-sdlc" / "claims" / "source-claims.yaml"
        code_a, result_a = manage_source_claims.acquire(root, store, "CLAIM-A", "agent-a", ["src/Service.java"], ["PGM-1"], head,
                                                        "agent/REQ-1/TASK-1/selftest", 30)
        code_b, result_b = manage_source_claims.acquire(root, store, "CLAIM-B", "agent-b", ["src/Service.java"], ["PGM-1"], head,
                                                        "agent/REQ-1/TASK-1/selftest", 30)
        checks["atomic_claim_conflict"] = {"pass": code_a == 0 and code_b != 0 and result_b.get("decision") == "DENY",
                                            "first": result_a.get("decision"), "second": result_b.get("decision")}

        source = root / "src" / "Service.java"
        before_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        write_doc = request("W1", "SOURCE", "source.write", write=True, expected=head, ext={"root": str(root), "path": "src/Service.java",
            "content": "class Service { String value() { return \"B\"; } }\n", "expected_object_sha256": before_hash,
            "expected_agent_branch": "agent/REQ-1/TASK-1/selftest"})
        write = git_worktree_source.invoke(write_doc, {"root": str(root)})
        checks["revision_guarded_source_write"] = {"pass": write["provider_response"]["status"] == "OK" and '"B"' in source.read_text(encoding="utf-8"),
                                                    "status": write["provider_response"]["status"]}

        interface = analyze_interface_contract.analyze(root, ["contracts/openapi.yaml"])
        ev = interface["source_analysis_result"]["evidence"]
        operations = ev[0].get("operations") if ev else []
        checks["interface_analyzer"] = {"pass": bool(operations) and operations[0].get("operation_id") == "sendWorkPlan",
                                        "evidence_count": len(ev)}

        command = [sys.executable, "-c", "print('runtime-ok')"]
        test = subprocess_test.invoke(request("T1", "TEST", "test.execute", ext={"cwd": str(root), "command": command}),
                                     {"cwd": str(root), "allowed_commands": [command], "timeout_seconds": 30})
        outputs = test["provider_response"].get("outputs") or []
        checks["actual_subprocess_test"] = {"pass": test["provider_response"]["status"] == "OK" and outputs and outputs[0].get("test_status") == "PASSED" and outputs[0].get("actual_runtime") is True,
                                             "status": test["provider_response"]["status"], "test_status": outputs[0].get("test_status") if outputs else None}

        context = {"context": {"representative_id": "REQ-1", "short_business_name": "YellowPage송신", "requirement_id": "REQ-1",
            "title": "근무계획 송신", "project_name": "SELFTEST", "project_mode": "BROWNFIELD", "source_revision": head,
            "truth_state": "GIVEN", "request_detail": "근무계획을 송신한다.", "desired_result": "송신 성공 여부를 검증한다.",
            "scope": "Yellow Page interface", "evidence_refs": ["EV-SELFTEST"]}}
        registry = yaml.safe_load((HARNESS_ROOT / "sdlc/config/human-artifacts.yaml").read_text(encoding="utf-8"))
        text, meta = render_human_artifact.render(HARNESS_ROOT, registry, "요구사항", context)
        checks["human_artifact_renderer"] = {"pass": "REQ-1" in text and "OPEN" in text and meta["render_result"]["open_preserved"] is True,
                                             "missing_fields": len(meta["render_result"]["missing_fields"])}

    passed = all(item.get("pass") for item in checks.values())
    report = {"schema_version": 1, "artifact_type": "P0_PRODUCTION_READINESS_SELFTEST", "selftest": {
        "state": "PASS" if passed else "FAIL", "checks": checks,
        "production_candidate_e2e": passed, "real_git_worktree_used": True, "actual_subprocess_used": True,
        "real_customer_source_validated": False, "production_ready_claim_allowed": False,
        "next_gate": "Run the same flow against an actual customer source repository, build/test command, DB/interface evidence and review Reverse Sync."}}
    print(yaml.safe_dump(report, allow_unicode=True, sort_keys=False), end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
