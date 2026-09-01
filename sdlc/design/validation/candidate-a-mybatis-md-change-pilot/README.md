# Candidate A — MyBatis MD + Change Propagation Pilot

> 상태: `VALIDATION PILOT / NOT BASELINE`
> 입력 근거: `요구사항목록.xlsx`의 `REQ_TM_TE016~054` 근태마감 39건
> Pilot 가정: 사용자 Boundary Review를 거쳐 `RQC-017`을 downstream 검증용 `RQ-PILOT-017`로 임시 승인한다. 실제 Baseline Publish가 아니다.

## Quick Start

사용자가 실제로 보게 되는 순서는 다음과 같다.

```text
요구사항목록.xlsx
→ docs/01_requirements/RQ-PILOT-017/requirement.md
→ docs/02_analysis/RQ-PILOT-017/requirement-analysis.md
→ docs/02_analysis/RQ-PILOT-017/process-analysis.md
→ docs/03_impact/RQ-PILOT-017/impact-analysis.md
→ docs/04_design/RQ-PILOT-017/functional-design.md
→ docs/05_program/RQ-PILOT-017/specs/PGM-ATT-CLOSE-001.md
→ docs/08_management/RQ-PILOT-017/task-plan.md
→ fixture/as-is Source
→ fixture/after-cr Source
→ docs/07_test/RQ-PILOT-017/test-scenarios.md
→ docs/08_management/RQ-PILOT-017/implementation-result.md
→ docs/07_test/RQ-PILOT-017/verification-result.md
```

중간에 변경요청을 한 번 발생시킨다.

```text
CR-PILOT-001
월마감 이후에도 승인된 수정요청 건은 재집계를 허용한다.
단, 강제마감(FORCE_CLOSE)에는 재집계를 허용하지 않는다.
```

변경 후 수정 시작점은 `CR → requirement/analysis의 Business Rule → process → impact → design → PGM spec → task/test/source`다. 단순히 Source부터 고치지 않는다.

## Fixture Stack

- Java 17 / Spring Service 가정
- MyBatis Mapper Interface + XML
- Oracle `MERGE`
- `TB_WORK_PLAN`, `TB_ATT_DAILY`, `TB_ATT_CLOSE`, `TB_ATT_CORRECTION_REQ`

## Candidate A에서 확인할 점

1. Legacy ID가 Requirement/FR까지 추적되는가.
2. 변경으로 RQ Boundary가 달라지는지 먼저 판단하는가.
3. 이번 CR은 RQ Split이 아니라 `policy_state_scope` revision으로 처리되는가.
4. 변경된 Business Rule을 기준으로 downstream 문서가 STALE→CURRENT 되는 흐름이 이해되는가.
