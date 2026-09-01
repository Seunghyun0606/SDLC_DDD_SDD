# Candidate A Pilot Scenario Reference Guide

> 목적: 파일럿에서 사용한 변경 시나리오를 재사용 가능한 가이드로 남기고, 변경 유형별로 어느 산출물부터 수정해야 하는지 명확히 한다.

## Scenario Index

| ID | 변경 유형 | 대표 입력 | 수정 시작점 | 주요 STALE 범위 |
|---|---|---|---|---|
| A-S01 | 신규/고도화 업무요구 | 10분 단위 근무계획을 근태마감에 반영 | requirement.md | Analysis 이후 전체 |
| A-S02 | 업무 정책 변경 | 월마감 후 승인 수정요청은 재집계 허용, FORCE_CLOSE 제외 | CR + requirement/BR | Process/Impact/Design/PGM/Test |
| A-S03 | SQL 성능 변경 | 같은 결과를 더 빠른 Query로 변경 | impact/PGM spec | Task/Test/Source |
| A-S04 | 내부 Refactoring | Service 내부 구조 정리, 외부 동작 동일 | PGM spec/Task | Source/Regression Test |
| A-S05 | RQ Boundary 오류 발견 | Source 분석 결과 일마감/월마감이 독립 Lifecycle | SCOPE_CHANGE_CANDIDATE | RQ/FR + downstream STALE |

## A-S01 신규/고도화 업무요구

```text
Legacy Excel / Human Input
→ Raw/Topic Group
→ RQ Boundary Candidate
→ requirement.md
→ requirement-analysis.md
→ process-analysis.md
→ impact-analysis.md
→ functional-design.md
→ PGM Spec
→ Task
→ Source
→ Test
→ Verification
```

### Reference
- `docs/01_requirements/RQ-PILOT-017/requirement.md`
- `docs/02_analysis/RQ-PILOT-017/requirement-analysis.md`
- `docs/03_impact/RQ-PILOT-017/impact-analysis.md`
- `docs/05_program/RQ-PILOT-017/specs/PGM-ATT-CLOSE-001.md`

## A-S02 업무 정책 변경

변경 예:

> 월마감 이후에도 승인된 수정요청 건은 재집계를 허용한다. 단 FORCE_CLOSE는 재집계를 허용하지 않는다.

업무 의미가 바뀌므로 Source부터 수정하지 않는다.

```text
CR-PILOT-001
→ requirement scope revision
→ BR / AC 변경
→ Process State/Exception 변경
→ Impact 재분석
→ Functional Design
→ PGM Spec
→ Task/Test
→ Source
→ Verification
```

### Reference
- `docs/01_requirements/RQ-PILOT-017/CR-PILOT-001.md`
- `docs/08_management/RQ-PILOT-017/change-propagation.md`
- `fixture/as-is/`
- `fixture/after-cr/`

## A-S03 SQL 성능 변경

업무결과/Rule이 동일하고 SQL 실행방식만 변경되는 경우 Requirement/BR을 재작성하지 않는다.

```text
Observed performance evidence
→ impact-analysis.md TECHNICAL_CHANGE
→ PGM Spec
→ Development Task
→ SQL/MyBatis XML
→ Performance + Regression Test
```

Requirement/Process/Functional Design은 `UNCHANGED` 표시 가능.

## A-S04 내부 Refactoring

외부 동작과 Data Contract가 동일한 경우:

```text
PGM Spec Standard Deviation/Refactoring Note
→ Task
→ Source
→ Unit/Regression Test
```

RQ/BR/Process를 억지로 변경하지 않는다.

## A-S05 Source 분석 중 RQ Boundary 오류 발견

Source/Runtime Evidence에서 기존 RQ Candidate가 서로 다른 Business Lifecycle을 포함한다고 확인되면 Agent가 자동 Split하지 않는다.

```text
Discovery Finding
→ SCOPE_CHANGE_CANDIDATE
→ Before/After RQ Boundary Card
→ affected Legacy IDs / FR 목록
→ Human Review
→ RQ revision/split
→ downstream STALE propagation
```

## Change Routing Rule

변경을 먼저 다음 네 질문으로 분류한다.

1. 고객이 기대하는 업무결과가 바뀌는가? → Requirement/BR부터
2. Process/State/Policy가 바뀌는가? → BR/Process부터
3. 같은 기능인데 구현/성능만 바뀌는가? → Impact/PGM부터
4. 외부 동작도 그대로인 내부정리인가? → PGM/Task부터

변경 시작점보다 상위 문서는 `UNCHANGED`, 영향을 받는 하위 문서는 `STALE → CURRENT` 흐름을 명시한다.
