# 08 PROGRAM — 프로그램설계

> Program/Artifact는 `SIMULATED_SOURCE_FIXTURE`에만 존재한다.

## 문서 목적
Source Evidence를 Logical Program/Artifact/TASK 후보에 연결한다.

## 30초 요약
`PGM-PILOT-001 FlexibleWorkPlan`을 기존 Program MODIFY로 보고 Service 중심 L2 Spec으로 구성한다.

## Workflow
`Functional Design → existing program reuse → PGM Spec → TASK`

## 입력/Evidence
| Artifact | Symbol | Locator | Source Hash | Evidence Status |
|---|---|---|---|---|
| ART-PILOT-SVC | getPlan/savePlan | `as-is/...Service.java` | sha256:490fd18a0e8a006d71805e9675dfd0707b764bb63fdd3758a128d76f1313fab4 | SIMULATED_OBSERVED |
| ART-PILOT-MAP | selectPlan/selectDefaultSchedule/upsertPlan | `as-is/...Mapper.xml` | sha256:080ef6f36e761984065d9e36b8127f7c58ab3de54156e17bb15be991c6153612 | SIMULATED_OBSERVED |

## 본문
- PGM: `PGM-PILOT-001`
- Change Type: MODIFY
- Spec Level: L2
- TO-BE: Service에 `initializeFirstPlan` candidate 추가.
- Controller endpoint 추가는 `SIMULATED_TECHNICAL_CHOICE`.
- Mapper SQL은 fixture 기준 재사용 가능.

TASK: `TASK-PILOT-DEV-001`, 조건부 `TASK-PILOT-DEV-002`, `TASK-PILOT-TST-001`.

## 미확정/Alert/Assumption
Controller 수정 여부는 INT-PILOT-001 답변에 종속.

## 관련 ID/Traceability
`PGM-PILOT-001 → ART-PILOT-* → DATA-PILOT-* → TASK-PILOT-*`

## 다음 작업
DEVELOPMENT에서 AS-IS/TO-BE fixture 차이를 기록한다.
