---
document_type: customer_decision_acceptance_view
requirement_id: RQ-PILOT-017
revision: 3
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

## 3. 6W 업무정의 / 합의상태

| 관점 | 고객 View | 합의상태 |
|---|---|---|
| Who — 누가 | 근태마감 권한 사용자 또는 마감 Batch | OPEN — 실제 권한/Profile 필요 |
| When — 언제 | 일마감 또는 월마감 후 승인 수정요청 재집계 시 | REVIEW_REQUIRED |
| Where — 어디서 | 근태마감 업무기능 | OPEN — 실제 메뉴/Batch Entry 필요 |
| What — 무엇을 | 사원/근무일자의 계획근무분을 일집계에 반영 | REVIEW_REQUIRED |
| How — 어떻게 | 상태/승인/FORCE 조건 검증 후 10분 단위 계산/반영 | REVIEW_REQUIRED |
| Why — 왜 | 계획과 마감결과 일치 및 월마감 후 임의수정 통제 | REVIEW_REQUIRED |

### 고객 업무문장

```text
근태마감 권한 사용자 또는 마감 Batch가
일마감 또는 승인된 월마감 수정요청 재집계 시
근태마감 업무기능에서
대상 사원/근무일자의 근무계획 시간을
마감/승인/강제마감 조건을 확인한 후 10분 단위로 계산하여 일집계에 반영한다.
목적은 계획과 마감결과를 일치시키고 월마감 후 변경을 통제하는 것이다.
```

Who/Where가 OPEN이므로 고객 업무합의는 아직 `REVIEW_REQUIRED`다.

## 4. AS-IS / TO-BE
| 항목 | AS-IS | TO-BE |
|---|---|---|
| 계획 반영단위 | 30분 | 10분 |
| 월마감 후 수정 | 정책/구현 미정 | 승인 수정요청만 허용 |
| FORCE_CLOSE | 명시 예외 없음 | 월마감 후 재집계 금지 |

## 5. 업무 흐름
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

## 6. 고객 결정 필요사항
| Decision | 제안안 | 근거 | 결정권자 | 상태 |
|---|---|---|---|---|
| CDEC-P017-00 | 실제 처리주체 Profile/Menu/Batch Entry 확정 | 6W Who/Where OPEN | 고객 업무/IT | REVIEW_REQUIRED |
| CDEC-P017-01 | 월마감 후 승인 수정요청만 허용 | CR-PILOT-001 / BR-P017-02 | 인사운영책임자 | REVIEW_REQUIRED |
| CDEC-P017-02 | FORCE_CLOSE는 예외 없이 재집계 금지 | CR-PILOT-001 / BR-P017-03 | 인사운영책임자 | REVIEW_REQUIRED |
| CDEC-P017-03 | 10분 미만 잔여분은 절삭 | Pilot 설계 | 업무담당자 | REVIEW_REQUIRED |

## 7. 업무 규칙 / 예외
| Rule | 조건 | 결과 | 예외 | 합의상태 |
|---|---|---|---|---|
| BR-P017-01 | 일반마감 | 10분 단위 계획 반영 | 10분 미만 잔여 | REVIEW_REQUIRED |
| BR-P017-02 | 월마감+승인 수정요청 | 재집계 허용 | FORCE_CLOSE | REVIEW_REQUIRED |
| BR-P017-03 | 월마감+FORCE_CLOSE | 재집계 금지 | 없음 | REVIEW_REQUIRED |

## 8. 고객 접점 영향
- UI: 신규 UI 없음으로 가정하지만 실제 메뉴/Entry 확인 필요
- Field: 신규 Field 없음으로 가정. closeType/수정요청 참조 위치 확인 필요
- 운영: 월마감 후 승인 수정요청 절차 영향
- 연계: 직접 Interface 변경은 미확인; 승인상태 생성 Upstream은 확인 필요
- Data: 근태 일집계 결과 변경

## 9. 완료 조건
| AC | 고객 관점 완료조건 | 실제 검증 Evidence | 상태 |
|---|---|---|---|
| AC-01 | 485분 계획 → 480분 반영 | Scenario 정의만 존재 | NOT_TESTED |
| AC-03 | 월마감+승인 요청 → 재집계 성공 | Scenario 정의만 존재 | NOT_TESTED |
| AC-04 | 월마감+미승인 → 실패 | Scenario 정의만 존재 | NOT_TESTED |
| AC-05 | 월마감+FORCE_CLOSE → 실패 | Scenario 정의만 존재 | NOT_TESTED |

## 10. 현재 진행 상태
- 업무합의: `REVIEW_REQUIRED`
- 구현: `IN_PROGRESS` — Pilot Fixture Patch 작성
- 검증: `NOT_TESTED` — 실제 Spring/MyBatis/Oracle 실행 없음
- 배포 준비: `NOT_READY`

> 내부 Stage `progress=COMPLETE`와 고객 합의/검증/배포상태는 분리한다.

## 11. 고객 영향 / 리스크
- 실제 권한/Profile과 처리 Entry 확인 필요
- 승인 수정요청의 실제 상태코드/승인주체 확인 필요
- 기존 월마감 소급 재처리 요구가 생기면 Scope 변경
- 실제 DB Lock/성능은 운영 유사환경 검증 필요

## 12. 참고 근거
- Legacy RQ: REQ_TM_TE016~REQ_TM_TE054
- Change: CR-PILOT-001
- Pilot Source Fixture

## 13. 변경 이력
| Revision | 변경 | 원인 | 고객상태 |
|---:|---|---|---|
| 1 | 10분 단위 반영 | Legacy RQ | OPEN |
| 2 | 승인 수정요청/FORCE_CLOSE 정책 | CR-PILOT-001 | REVIEW_REQUIRED |
| 3 | 6W 업무정의 및 고객 접점 추가 | Design improvement | REVIEW_REQUIRED |
