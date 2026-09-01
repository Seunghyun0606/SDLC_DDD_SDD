---
document_id: DOC-RQ-PILOT-017
requirement_id: RQ-PILOT-017
revision: 2
status: COMPLETE
quality: WARNING
validity: CURRENT
legacy_source_ids: REQ_TM_TE016..REQ_TM_TE054
changes: [CR-PILOT-001]
---
# RQ-PILOT-017 근태마감에 10분 단위 근무계획 반영

## 목적
근태마감 계산 시 10분 단위 근무계획을 손실 없이 반영한다.

## 현재 문제
Fixture Source에서 `plannedMinutes`를 30분 단위로 절삭한다. 이는 `OBSERVED`이며 실제 운영 Source를 의미하지 않는다.

## 원하는 결과
1. 일반 마감 시 10분 단위 근무계획을 반영한다.
2. **CR-PILOT-001 반영:** 월마감 이후에는 승인된 수정요청이 있는 경우에만 재집계를 허용한다.
3. **CR-PILOT-001 반영:** `FORCE_CLOSE`에는 월마감 후 재집계를 허용하지 않는다.

## Scope Snapshot
| 항목 | 값 | Truth |
|---|---|---|
| business_goal | 10분 단위 계획을 근태마감 결과에 반영 | GIVEN + OBSERVED |
| actor_trigger | 마감 실행 사용자/배치 | CANDIDATE |
| observable_outcome | TB_ATT_DAILY 반영분이 10분 단위 계획과 일치 | CANDIDATE |
| policy_state_scope | 일반마감/월마감후 수정/강제마감 | GIVEN by CR |
| acceptance_release_scope | 하나의 RQ 내 정책 분기 | PILOT_DECISION |

## 변경 이력
- rev1: 10분 단위 반영
- rev2: CR-PILOT-001 월마감 후 승인 수정요청 예외 + 강제마감 제외

이번 변경은 Business Goal을 새 RQ로 분리하지 않고 `policy_state_scope`를 확장한다.
