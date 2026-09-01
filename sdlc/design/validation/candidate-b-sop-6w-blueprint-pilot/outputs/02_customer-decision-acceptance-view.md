# 고객 검토/완료조건 — 탄력근로제 일일 근무계획

> business_agreement: `REVIEW_REQUIRED`
> implementation: `NOT_STARTED_REAL_REPO`
> verification: `NOT_TESTED`
> release_readiness: `NOT_READY`

## 1. 업무 목표

탄력근로제 근무자가 매일 예정 근무시간을 10분 단위로 등록하고, 해당 계획을 근태집계/마감의 기준으로 사용한다.

## 2. 6W

| 관점 | 고객 View | 합의상태 |
|---|---|---|
| 누가 | ESS 탄력근로제 권한을 가진 근무자 | 실제 권한명 확인 필요 |
| 언제 | 매일, 예정 근무일 계획 입력/확인 시 | REVIEW_REQUIRED |
| 어디서 | ESS > 근태/휴가 > 탄력근로제 근무계획 | 실제 화면 ID 확인 필요 |
| 무엇을 | 근무일자/유형/시작/종료/예상근무시간/상태 | REVIEW_REQUIRED |
| 어떻게 | 10분 단위 검증 후 저장/수정, 월 Calendar 조회 | REVIEW_REQUIRED |
| 왜 | 근태집계/마감 기준 제공, 미입력 예방 | REVIEW_REQUIRED |

## 3. 화면/기능

- 월 Calendar
- 일 상세입력
- 조회/저장/수정/기본값 설정
- 예상근무시간/상태 표시
- 삭제는 현재 Scope 제외

## 4. 고객 결정 필요사항

| Decision | 제안 | 상태 |
|---|---|---|
| CDEC-FLEX-01 | 시간은 10분 단위 | REVIEW_REQUIRED |
| CDEC-FLEX-02 | CONFIRMED 상태 직접 수정 금지 | REVIEW_REQUIRED |
| CDEC-FLEX-03 | 사원/일자별 1계획 | REVIEW_REQUIRED |
| CDEC-FLEX-04 | 삭제 기능은 제외 | REVIEW_REQUIRED |
| CDEC-FLEX-05 | 미입력 알람메일 운영조건 | OPEN |

## 5. 완료조건

- 10분 단위 신규/수정 가능
- 잘못된 시간단위/범위 차단
- 확정계획 수정 차단
- 월/일 조회 가능
- 기본값 사용 가능

## 6. 현재 상태

- 업무정의: `DRAFT_COMPLETE`
- 고객합의: `REVIEW_REQUIRED`
- 상세설계: `DRAFT_COMPLETE_FOR_FIXTURE`
- 실제 고객 Source 구현: `NOT_STARTED`
- 실제 Test: `NOT_TESTED`

내부 Work Unit/Target Proof 상세는 고객에게 노출하지 않지만, 미확정/미검증 상태는 숨기지 않는다.