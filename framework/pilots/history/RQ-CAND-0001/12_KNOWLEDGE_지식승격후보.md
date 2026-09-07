# 12 KNOWLEDGE — 지식승격 후보

## 문서 목적
완료 문서 전체가 아니라 재사용 가치가 있는 Knowledge 후보만 추출한다.

## 30초 요약
실제 Business Knowledge로 승격 가능한 항목은 아직 없다. Fixture에서 검증한 기술 패턴만 `PILOT_ONLY` 후보로 남긴다.

## Workflow
`VERIFY → candidate extract → evidence check → promote/reject`

## 입력/Evidence
- Requirement: GIVEN
- Source: SIMULATED_SOURCE_FIXTURE
- 실제 운영자/정책 확인: 없음

## 본문
| Candidate | Type | 내용 | Promotion |
|---|---|---|---|
| KNW-PILOT-001 | Technical Pattern | 기존 계획 조회→default 조회→계획 저장 | REJECT_FOR_PROJECT_KB / PILOT_ONLY |
| KNW-PILOT-002 | Data Meaning | TB_TM_FLEX_PLAN=근무계획 fixture table | REJECT_FOR_PROJECT_KB / PILOT_ONLY |
| KNW-PILOT-003 | Business Rule | 기존 계획 존재 시 반환 | NOT_PROMOTABLE / ASSUMPTION |

## 미확정/Alert/Assumption
실제 Source 또는 운영 확인 없는 지식을 프로젝트 Knowledge로 승격하면 안 된다.

## 관련 ID/Traceability
`VERIFY → KNW-PILOT-*`

## 다음 작업
실제 프로젝트 Pilot에서 Verified Technical Knowledge와 Confirmed Business Knowledge를 분리 승격한다.
