---
document_type: customer_functional_spec
requirement_id: RQ-PILOT-017
revision: 2
customer_view_status: REVIEW_REQUIRED
scope_version: 2
source_artifacts:
  - requirement-analysis.md#rev2
  - process-analysis.md#rev2
  - functional-design.md#rev2
---
# 근태마감 10분 단위 근무계획 반영 — 고객 기능 정의서

## 1. 변경 배경
현재 Pilot Source는 근무계획 시간을 30분 단위로 절삭하여 근태마감 결과에 반영한다. 10분 단위 근무계획을 운영하는 경우 실제 계획과 근태마감 결과가 다를 수 있다.

### 변경 목적
- 근무계획의 10분 단위를 근태마감 결과에 반영한다.
- 월마감 이후 수정이 필요한 경우 승인된 수정요청만 재집계를 허용한다.
- 강제마감은 월마감 이후 재집계에서 제외한다.

## 2. Scope
### 포함
- 일반 일근태 마감의 10분 단위 계획 반영
- 월마감 이후 승인 수정요청 재집계
- FORCE_CLOSE 예외 처리

### 제외
- 과거 전체 월마감 데이터 일괄 재처리
- 전자결재 시스템 자체 기능 변경
- 근무계획 수립 화면 변경

## 3. AS-IS / TO-BE
| 항목 | AS-IS | TO-BE |
|---|---|---|
| 근무계획 반영 단위 | 30분 단위 절삭 | 10분 단위 반영 |
| 월마감 후 수정 | 정책/구현 불명확 | 승인 수정요청만 재집계 허용 |
| 강제마감 | 별도 예외 없음 | 월마감 후 재집계 불가 |

## 4. 업무 흐름
```text
근태마감 요청
→ 월마감 여부 확인
   ├ 미마감: 10분 단위 계획 반영 후 마감
   └ 월마감:
       → FORCE_CLOSE 여부 확인
          ├ FORCE_CLOSE: 재집계 불가
          └ 일반 수정:
              → 승인 수정요청 여부 확인
                 ├ 승인: 10분 단위 재집계
                 └ 미승인: 재집계 불가
```

## 5. 업무 규칙
| 규칙 | 조건 | 결과 | 예외 | 확인상태 |
|---|---|---|---|---|
| BR-P017-01 | 일반 근태마감 | 근무계획을 10분 단위로 반영 | 없음 | 제안 |
| BR-P017-02 | 월마감 + 승인 수정요청 | 재집계 허용 | FORCE_CLOSE 제외 | 고객확인 필요 |
| BR-P017-03 | 월마감 + FORCE_CLOSE | 재집계 불가 | 없음 | 고객확인 필요 |

## 6. 고객 접점 영향
- 화면: 직접 UI 변경 없음으로 가정
- 운영: 월마감 후 수정요청 승인 절차와 연계됨
- Data: 근태 일집계 결과가 변경될 수 있음
- Interface: 본 Pilot 범위에서는 직접 변경 없음

## 7. 완료 조건
| AC | 고객 관점 완료 조건 | 확인 방법 |
|---|---|---|
| AC-01 | 485분 계획이 480분으로 반영 | Test 결과 확인 |
| AC-03 | 월마감 후 승인 수정요청은 재집계 성공 | Test 결과 확인 |
| AC-04 | 월마감 후 미승인 요청은 재집계 실패 | Test 결과 확인 |
| AC-05 | 승인 요청이어도 FORCE_CLOSE는 재집계 실패 | Test 결과 확인 |

## 8. 고객 확인 필요사항
- [ ] 승인 수정요청의 공식 승인 상태값/승인주체
- [ ] FORCE_CLOSE의 업무 정의와 실행 권한
- [ ] 기존 월마감 데이터 중 소급 재처리 대상 존재 여부
- [ ] 10분 미만 잔여분 처리 정책

## 9. 참고/근거
- Legacy Requirement: REQ_TM_TE016~REQ_TM_TE054
- Change: CR-PILOT-001
- Pilot Source: AttendanceCloseService / MyBatis Mapper Fixture

## 10. 변경 이력
| Revision | 변경내용 | 원인 | 상태 |
|---:|---|---|---|
| 1 | 10분 단위 근무계획 반영 | Legacy RQ | DRAFT |
| 2 | 월마감 승인 수정요청/FORCE_CLOSE 정책 추가 | CR-PILOT-001 | REVIEW_REQUIRED |
