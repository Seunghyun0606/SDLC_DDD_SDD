---
document_type: customer_decision_acceptance_view
requirement_id: RQ-PILOT-017
revision: 2
business_agreement: REVIEW_REQUIRED
implementation: IN_PROGRESS
verification: NOT_TESTED
release_readiness: NOT_READY
---
# 근태마감 10분 단위 근무계획 반영 — 고객 검토/완료조건

## 1. 변경 배경과 목표
- 현재 Pilot 구현은 근무계획을 30분 단위로 절삭한다.
- 10분 단위 근무계획을 근태마감 결과에 반영한다.
- 월마감 후에는 승인된 수정요청만 재집계를 허용하되 FORCE_CLOSE는 제외한다.

## 2. Scope / Out of Scope
### 포함
- 일반 마감 10분 단위 반영
- 월마감 승인 수정요청 재집계
- FORCE_CLOSE 예외

### 제외
- 과거 데이터 일괄 재집계
- 전자결재 시스템 자체 변경
- 운영 DB 직접 변경 자동화

## 3. AS-IS / TO-BE
| 항목 | AS-IS | TO-BE |
|---|---|---|
| 계획 반영단위 | 30분 | 10분 |
| 월마감 후 수정 | 정책/구현 미정 | 승인 수정요청만 허용 |
| FORCE_CLOSE | 명시 예외 없음 | 월마감 후 재집계 금지 |

## 4. 업무 흐름
```text
근태마감 요청
→ 월마감 여부
   ├ 미마감 → 10분 단위 반영
   └ 월마감
      → FORCE_CLOSE?
         ├ Yes → 재집계 불가
         └ No → 승인 수정요청?
                ├ Yes → 재집계
                └ No → 재집계 불가
```

## 5. 고객 결정 필요사항
| Decision | 제안안 | 근거 | 결정권자 | 상태 |
|---|---|---|---|---|
| CDEC-P017-01 | 월마감 후 승인 수정요청만 허용 | CR-PILOT-001 / BR-P017-02 | 인사운영책임자 | REVIEW_REQUIRED |
| CDEC-P017-02 | FORCE_CLOSE는 예외 없이 재집계 금지 | CR-PILOT-001 / BR-P017-03 | 인사운영책임자 | REVIEW_REQUIRED |
| CDEC-P017-03 | 10분 미만 잔여분은 절삭 | Pilot 설계 | 업무담당자 | REVIEW_REQUIRED |

## 6. 업무 규칙 / 예외
| Rule | 조건 | 결과 | 예외 | 합의상태 |
|---|---|---|---|---|
| BR-P017-01 | 일반마감 | 10분 단위 계획 반영 | 10분 미만 잔여 | REVIEW_REQUIRED |
| BR-P017-02 | 월마감+승인 수정요청 | 재집계 허용 | FORCE_CLOSE | REVIEW_REQUIRED |
| BR-P017-03 | 월마감+FORCE_CLOSE | 재집계 금지 | 없음 | REVIEW_REQUIRED |

## 7. 완료 조건
| AC | 고객 관점 완료조건 | 실제 검증 Evidence | 상태 |
|---|---|---|---|
| AC-01 | 485분 계획 → 480분 반영 | Scenario 정의만 존재 | NOT_TESTED |
| AC-03 | 월마감+승인 요청 → 재집계 성공 | Scenario 정의만 존재 | NOT_TESTED |
| AC-04 | 월마감+미승인 → 실패 | Scenario 정의만 존재 | NOT_TESTED |
| AC-05 | 월마감+FORCE_CLOSE → 실패 | Scenario 정의만 존재 | NOT_TESTED |

## 8. 현재 진행 상태
- 업무합의: `REVIEW_REQUIRED`
- 구현: `IN_PROGRESS` — Pilot Fixture Patch 작성
- 검증: `NOT_TESTED` — 실제 Spring/MyBatis/Oracle 실행 없음
- 배포 준비: `NOT_READY`

> 내부 Stage의 `progress=COMPLETE` 여부와 무관하게 고객에게는 실제 의미 기준 상태를 보여준다.

## 9. 고객 영향 / 리스크
- 승인 수정요청의 실제 상태코드/승인주체 확인 필요
- 기존 월마감 소급 재처리 요구가 생기면 Scope 변경
- 실제 DB Lock/성능은 운영 유사환경 검증 필요

## 10. 참고 근거
- Legacy RQ: REQ_TM_TE016~REQ_TM_TE054
- Change: CR-PILOT-001
- Pilot Source Fixture

## 11. 변경 이력
| Revision | 변경 | 원인 | 고객상태 |
|---:|---|---|---|
| 1 | 10분 단위 반영 | Legacy RQ | OPEN |
| 2 | 승인 수정요청/FORCE_CLOSE 정책 | CR-PILOT-001 | REVIEW_REQUIRED |
