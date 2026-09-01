# CR-PILOT-001 월마감 후 재집계 정책 변경

## 변경 입력
> 월마감 이후에도 승인된 수정요청 건은 재집계를 허용한다. 단, 강제마감은 재집계를 허용하지 않는다.

Truth: `GIVEN`

## Before
월마감 이후 재집계 정책이 OPEN.

## After
- 승인된 수정요청: 재집계 허용
- 승인되지 않은 수정요청: 재집계 금지
- FORCE_CLOSE: 승인여부와 무관하게 재집계 금지

## 어디서부터 고치는가
이 변경은 Java/MyBatis 구현 세부가 아니라 **업무 정책/상태 규칙 변경**이다. 따라서 Source부터 고치지 않는다.

```text
CR-PILOT-001
→ requirement.md scope revision
→ requirement-analysis.md BR/AC
→ process-analysis.md state/exception
→ impact-analysis.md 재탐색
→ functional-design.md
→ PGM spec
→ task/test
→ Source
→ verification
```

## STALE 전파
| Artifact | 즉시 상태 | 이유 |
|---|---|---|
| requirement.md | WORKING→CURRENT | 변경 원문 반영 |
| requirement-analysis.md | STALE | BR/AC 변경 |
| process-analysis.md | STALE | 월마감 후 상태전이 변경 |
| impact-analysis.md | STALE | 수정요청 Table/Mapper 영향 추가 |
| functional-design.md | STALE | 예외/Transaction 변경 |
| PGM Spec | STALE | 신규 Mapper query 필요 |
| task-plan.md | STALE | 개발 Task 내용 변경 |
| test-scenarios.md | STALE | 승인/비승인/FORCE Case 추가 |
| Source | NOT_YET_CHANGED | 문서 재정렬 후 수정 |
