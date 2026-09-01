# P0.1 전체 142건 Legacy Normalizer 검증

> 입력: 첨부 `요구사항목록.xlsx` / `Sheet1`  
> Branch: `SDLC_DESIGN_SESSION_SECOND/p0.1/legacy-normalizer-v1`

## 결과

첨부 Workbook을 `artifact_tool`로 다시 읽어 142개 Source Row를 추출한 뒤 P0.1의 `EXACT_LEVEL2_REQUIREMENT_NAME` 규칙을 적용했다.

| 항목 | 결과 |
|---|---:|
| Source Row | 142 |
| 고유 Source Requirement ID | 142 |
| 중복 ID | 0 |
| Candidate Group | 22 |
| Group Source Count 합계 | 142 |
| Canonical RQ 자동발행 | 0 |
| Canonical FR 자동발행 | 0 |

가장 큰 Group은 다음과 같이 재현되었다.

| Stable Group ID | Level2 | Source Count |
|---|---|---:|
| `RQG-CAND-6BB6D66548` | 근태마감 | 39 |
| `RQG-CAND-D89319F3D1` | Batch | 23 |
| `RQG-CAND-8E538471B6` | 근태현황/통계 | 22 |
| `RQG-CAND-5BAC94F471` | 근태/휴가 (ESS) / 근무계획 반영 | 9 |
| `RQG-CAND-DC49AB42B6` | 탄력근로 예외사항 요청 | 8 |

기존 P0 Pilot의 순번형 Group ID `RQG-CAND-001~022`는 `requirements-list-stable-group-crosswalk.yaml`에서 Stable ID와 연결했다.

## 판정

**PASS**

P0 Pilot에서 사람이 적용했던 `Level2 + 요구사항명 EXACT` 142→22 Candidate Grouping이 P0.1 규칙으로 동일하게 재현되었다.

다만 이는 Business Outcome 확정이 아니다. 모든 Candidate Group의 Canonical Boundary 기본 상태는 계속 `OPEN / UNRESOLVED`이며 Human/L2 Review 전 RQ/FR Publish를 허용하지 않는다.

## 의미

P0.1 이후에는 다음 부분이 저수준 Agent의 자유 추론에 의존하지 않는다.

```text
Source ID 보존
→ 1차 exact grouping
→ stable group ID
→ group-level handoff
→ unresolved boundary guard
```

여전히 사람/L2 판단이 필요한 부분은 Candidate Group을 실제 RQ/FR로 확정하거나 Split/Merge하는 Business Boundary 결정이다.

## 남은 우선순위

1. 22개 Group Candidate를 Worklist/Review UI에 표현하는 방식
2. Human Boundary 결정 후 Canonical RQ/FR Publish Procedure
3. Brownfield Source Repository를 연결한 실제 `DISCOVERY → IMPACT → DESIGN` Pilot
4. Source Change/Test 이후 Reverse Sync Pilot
