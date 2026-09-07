# 13 CHANGE — STALE 전파 파일럿

## 문서 목적
자연어 변경이 들어왔을 때 어떤 산출물이 다시 검토되어야 하는지 보여준다.

## 30초 요약
가상의 `SIMULATED_CHANGE` “기존 계획이 있어도 기본 스케줄로 다시 생성한다”를 적용하면 ASM-PILOT-001과 충돌하며 PROCESS 이후 Artifact가 STALE 된다.

## Workflow
`natural language change → CR → affected relation traversal → STALE`

## 입력/Evidence
Pilot change: SIMULATED_CHANGE, 실제 요구 변경 아님.

## 본문
- `CR-PILOT-001`, Type BEHAVIOR_CHANGE
- PROC-PILOT-001: STALE
- Functional Design: STALE
- PGM-PILOT-001: STALE
- TASK-PILOT-DEV-001: STALE/REPLAN
- TC-PILOT-004: INVALID → redesign
- INTAKE 원문/FR-01/02: CURRENT

## 미확정/Alert/Assumption
실제 사용자 변경이 아니므로 Canonical Project Truth에는 반영하지 않는다.

## 관련 ID/Traceability
`CR-PILOT-001 → PROC/DESIGN/PGM/TASK/TC`

## 다음 작업
`/work RQ-CAND-0001` 재실행 시 가장 앞선 STALE Stage부터 갱신한다.
