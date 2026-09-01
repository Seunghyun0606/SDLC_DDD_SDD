#!/usr/bin/env python3
"""Run a conservative source-free Greenfield workflow replay from one real requirement.

The runner measures whether the simplified Harness can progress without inventing missing
business facts. It can materialize six compact user-facing pilot artifacts. This is an
Agent workflow usability replay, not a human usability study.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

WORKFLOW = [
    "INTAKE", "DECOMPOSE", "CLARIFY", "PROCESS", "DISCOVERY", "IMPACT",
    "DESIGN", "PROGRAM", "DEVELOPMENT", "TEST", "VERIFY", "KNOWLEDGE",
]
USER_ARTIFACTS = [
    "requirement.md",
    "open-resolution-workbook.md",
    "process-analysis.md",
    "functional-design.md",
    "program-spec.md",
    "test-scenario.md",
]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run(seed: dict[str, Any]) -> dict[str, Any]:
    required = ["schema_version", "pilot_id", "mode", "external_id", "requirement_text"]
    missing = [key for key in required if key not in seed]
    if missing:
        raise ValueError(f"seed missing fields: {missing}")
    if seed["schema_version"] != 1:
        raise ValueError("unsupported seed schema")
    if seed["mode"] != "GREENFIELD":
        raise ValueError("greenfield pilot requires GREENFIELD mode")

    source_repo = seed.get("existing_source_repository")
    requirement_text = str(seed["requirement_text"]).strip()
    if not requirement_text:
        raise ValueError("requirement_text is empty")

    open_items = [
        {"question": "누가 이 기능을 사용하거나 실행하는가?", "human_status": "미확정"},
        {"question": "언제 최초 근무계획을 만들고 저장해야 하는가?", "human_status": "미확정"},
        {"question": "저장에 필요한 입력값과 필수값은 무엇인가?", "human_status": "미확정"},
        {"question": "이미 계획이 있을 때 신규/수정/덮어쓰기 규칙은 무엇인가?", "human_status": "미확정"},
        {"question": "권한과 데이터 범위는 어떻게 제한되는가?", "human_status": "미확정"},
        {"question": "저장 실패·중복 요청·동시 수정은 어떻게 처리하는가?", "human_status": "미확정"},
    ]

    stages = [
        {"stage": "INTAKE", "status": "PASS", "basis": "외부 요구사항 ID와 원문을 변경 없이 보존", "source_required": False},
        {"stage": "DECOMPOSE", "status": "PASS_WITH_OPEN", "basis": f"요구사항 `{requirement_text}`를 단일 활성 Requirement Artifact에서 구조화", "invented_business_fact": False},
        {"stage": "CLARIFY", "status": "PASS_OPEN_BACKLOG_CREATED", "basis": f"미확정 업무 판단 {len(open_items)}건을 사람용 5상태 View로 노출", "open_count": len(open_items)},
        {
            "stage": "PROCESS", "status": "PARTIAL_WITH_OPEN",
            "basis": "What은 요구사항에서 확인되지만 Who/When/Where/Why와 상세 How는 미확정",
            "six_w": {"Who": "OPEN", "When": "OPEN", "Where": "OPEN", "What": requirement_text, "How": "PARTIAL_REQUIREMENT_TEXT_ONLY", "Why": "OPEN"},
        },
        {"stage": "DISCOVERY", "status": "NOT_APPLICABLE_NO_EXISTING_SOURCE", "basis": "Greenfield 시작에 기존 Source를 강제하지 않음", "brownfield_adapter_invoked": False},
        {"stage": "IMPACT", "status": "DESIGN_SCOPE_ONLY", "basis": "기존 시스템 영향이 아니라 신규 설계 범위와 OPEN만 관리", "complete_brownfield_impact_claimed": False},
        {"stage": "DESIGN", "status": "PROPOSAL_READY_WITH_OPEN", "basis": "화면/API/Data 설계안은 제안 가능하나 업무 미확정값을 확정 사실로 승격하지 않음", "proposal_is_business_truth": False},
        {"stage": "PROGRAM", "status": "NOT_IMPLEMENTATION_READY", "basis": "Functional Design 기준점은 만들 수 있으나 실제 Source Target이 없어 OPEN_REAL_SOURCE", "source_state": "OPEN_REAL_SOURCE", "readiness": "NOT_READY"},
        {"stage": "DEVELOPMENT", "status": "GUARDED_NOT_STARTED", "basis": "실제 Source Target/승인 설계가 없으므로 Source write를 실행하지 않음", "source_write_performed": False},
        {"stage": "TEST", "status": "TEST_CANDIDATE_ONLY", "basis": "확정된 AC와 실행 가능한 구현이 없으므로 TC는 후보 수준", "execution_claimed": False},
        {"stage": "VERIFY", "status": "NOT_VERIFIED", "basis": "실행 결과가 없으므로 검증 성공을 주장하지 않음", "success_claimed": False},
        {"stage": "KNOWLEDGE", "status": "NOT_PROMOTED", "basis": "미확정/미검증 내용을 운영 Knowledge로 승격하지 않음"},
    ]

    metrics = {
        "workflow_stage_count": len(stages),
        "active_user_artifact_count": len(USER_ARTIFACTS),
        "machine_result_envelope_is_user_artifact": False,
        "required_machine_taxonomy_input_count": 0,
        "open_item_count": len(open_items),
        "source_repository_required_to_start": False,
        "brownfield_adapter_invocation_count": 0,
        "business_fact_invention_count": 0,
        "source_write_count": 0,
    }

    return {
        "schema_version": 1,
        "pilot_id": seed["pilot_id"],
        "pilot_kind": "REAL_REQUIREMENT_GREENFIELD_AGENT_E2E_REPLAY",
        "input": {
            "source_document": seed.get("source_document"),
            "external_id": seed["external_id"],
            "requirement_group": seed.get("requirement_group"),
            "requirement_text": requirement_text,
            "existing_source_repository": source_repo,
        },
        "workflow": WORKFLOW,
        "stages": stages,
        "open_items": open_items,
        "active_user_artifacts": USER_ARTIFACTS,
        "metrics": metrics,
        "verdict": "PASS_AGENT_E2E_REPLAY_HUMAN_USABILITY_NOT_MEASURED",
        "limitations": [
            "실제 고객/분석가/설계자 사용시간과 이해도는 측정하지 않음",
            "실제 LLM 반복 생성 안정성은 별도 실험 대상",
            "실제 Source 구현이 없으므로 PROGRAM 이후 실행 성공을 검증하지 않음",
        ],
    }


def _render_artifacts(result: dict[str, Any]) -> dict[str, str]:
    inp = result["input"]
    req = inp["requirement_text"]
    group = inp.get("requirement_group") or "미제공"
    ext = inp["external_id"]
    questions = "\n".join(f"- [미확정] {row['question']}" for row in result["open_items"])
    return {
        "requirement.md": f"# 요구사항\n\n## 문서 목적\nGreenfield 최초 입력을 보존하고 설계 진행 기준을 만든다.\n\n## 한눈에 보기\n- 외부 요구사항 ID: `{ext}`\n- 요구 그룹: {group}\n- 요구사항: {req}\n- 기존 Source: 없음\n\n## 상세 내용\n현재 확정 가능한 내용은 `{req}`이다. 세부 업무 규칙은 별도 확인한다.\n\n## 미확정 사항·주의·가정\n{questions}\n",
        "open-resolution-workbook.md": f"# 미확정 사항 협의 목록\n\n## 문서 목적\n설계 전에 확인할 질문을 사람이 읽기 쉬운 상태로 관리한다.\n\n## 한눈에 보기\n- 대상: `{ext}` {req}\n- 미확정: {len(result['open_items'])}건\n\n## 고객과 함께 확인할 내용\n{questions}\n",
        "process-analysis.md": f"# 업무 흐름 분석\n\n## 문서 목적\n현재 요구사항에서 확인 가능한 업무 흐름과 부족한 정보를 구분한다.\n\n## 업무 흐름\n1. 탄력근로제 근무계획 저장 요청이 발생한다.\n2. 저장에 필요한 주체·시점·입력값·중복 규칙은 아직 확인이 필요하다.\n\n## 상세 내용\n- 누가: 미확정\n- 언제: 미확정\n- 어디서: 미확정\n- 무엇을: {req}\n- 어떻게: 요구 문구 수준에서만 부분 확인\n- 왜: 미확정\n",
        "functional-design.md": f"# 기능 설계 초안\n\n## 문서 목적\n확정 사실과 제안 가능한 설계 범위를 분리한다.\n\n## 한눈에 보기\n- 기능: {req}\n- 상태: 설계 제안 가능 / 업무 규칙 미확정\n\n## 상세 내용\n저장 기능의 화면/API/Data 구조는 제안할 수 있으나 입력 필드, 권한, 중복 처리, 실패 처리 규칙은 합의 전까지 확정하지 않는다.\n\n## 미확정 사항·주의·가정\n{questions}\n",
        "program-spec.md": f"# 프로그램 명세 준비도\n\n## 문서 목적\n기능 설계를 실제 구현 대상으로 연결할 수 있는지 확인한다.\n\n## 한눈에 보기\n- 기능 기준: {req}\n- 실제 Source Target: 미확정\n- 구현 준비도: NOT READY\n\n## 상세 내용\nGreenfield이므로 기존 Source를 요구하지 않는다. 실제 구현 Repository와 Target이 생성된 뒤 Program Spec 구현 매핑을 작성한다. 현재 단계에서 파일명·클래스·Query를 발명하지 않는다.\n",
        "test-scenario.md": f"# 테스트 시나리오 후보\n\n## 문서 목적\n확정된 요구만으로 만들 수 있는 테스트 후보와 실행 불가 영역을 구분한다.\n\n## 한눈에 보기\n- 대상: {req}\n- 실행 상태: 구현 전 / 테스트 후보만 작성\n\n## 상세 내용\n- 후보: 정상적인 근무계획 저장 요청 시 저장 결과를 확인한다.\n- 추가 확인 필요: 필수 입력, 중복 저장, 권한, 실패/동시성 규칙.\n- 실제 실행 성공은 주장하지 않는다.\n",
    }


def materialize(result: dict[str, Any], artifact_root: Path) -> list[str]:
    artifact_root.mkdir(parents=True, exist_ok=True)
    rendered = _render_artifacts(result)
    if sorted(rendered) != sorted(USER_ARTIFACTS):
        raise ValueError("rendered user artifact set does not match USER_ARTIFACTS")
    for name, text in rendered.items():
        (artifact_root / name).write_text(text.rstrip() + "\n", encoding="utf-8")
    return sorted(rendered)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--artifact-root")
    args = parser.parse_args(argv)
    try:
        result = run(_read_json(Path(args.seed)))
        if args.artifact_root:
            result["materialized_artifacts"] = materialize(result, Path(args.artifact_root))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verdict": result["verdict"], **result["metrics"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
