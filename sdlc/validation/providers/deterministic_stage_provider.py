#!/usr/bin/env python3
"""Deterministic validation-only provider for /work executor CI.

This file is not an Agent and must never be used as evidence of LLM/Agent semantic quality.
It only proves provider invocation -> artifact -> Stage Result -> validator -> Canonical
NO_CHANGE wiring across arbitrary stages and target IDs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--result", required=True)
    args = parser.parse_args()
    context = json.loads(Path(args.context).read_text(encoding="utf-8"))
    stage = context["selection"]["stage"]
    artifact_rel = context["selection"]["artifact_path"]
    target_id = context["target"]["id"]
    entity = context["target"].get("entity") or {}
    fields = entity.get("fields", {}) if isinstance(entity, dict) else {}
    original = fields.get("original_text") or fields.get("name") or "입력 내용은 Canonical Target을 참조한다."
    artifact = Path(artifact_rel)
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(
        f"---\nstage: {stage}\ndocument_type: validation_fixture\nstatus: CURRENT\n---\n"
        f"# {stage} 검증용 산출물\n\n"
        f"## 문서 목적\n/work 실행 경로의 Stage/Artifact 선택과 검증 연결을 확인한다.\n\n"
        f"## 한눈에 보기\n- 대상: {target_id}\n- 입력: {original}\n\n"
        f"## 상세 내용\n이 문서는 deterministic validation fixture가 생성했으며 업무 사실을 추가하지 않는다.\n\n"
        f"## 미확정 사항·주의·가정\n실제 Agent 의미 품질은 검증하지 않는다.\n\n"
        f"## 관련 ID 및 추적성\n{target_id}\n\n"
        f"## 다음 작업\n실제 Provider 연결 시 동일 실행 경계를 사용한다.\n",
        encoding="utf-8",
    )
    result = {
        "schema_version": 1,
        "stage": stage,
        "artifact_path": artifact_rel,
        "canonical_delta": {
            "schema_version": 1,
            "delta_id": f"FIXTURE-{target_id}-{stage}",
            "base_revision": context["canonical"]["base_revision"],
            "stage": stage,
            "source_artifact": artifact_rel,
            "operations": [],
            "no_change_reason": "Validation fixture proves executor wiring only and intentionally changes no Canonical semantics.",
        },
        "quality_gate": {"status": "PASS", "failures": []},
        "alerts": ["VALIDATION_FIXTURE_NOT_AGENT"],
        "uncertainty": [],
    }
    out = Path(args.result)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
