# ESS-FLEX-PLAN — 6W 업무정의서

> Status: `CANDIDATE / CUSTOMER REVIEW REQUIRED`
> Source: 실제 요구사항 XLSX + 가상 PPT SoP + 가상 Brownfield Source

## 업무정의 한 문장

`ESS_PROFILE_FLEX 권한을 가진 탄력근로제 근무자(Who)가 매일 예정 근무일의 계획을 입력할 때(When) ESS > 근태/휴가 > 탄력근로제 근무계획 메뉴(Where)에서 근무일자·근무유형·시작시간·종료시간(What)을 선택하고 10분 단위 검증 후 저장 또는 수정(How)하여 근태집계와 근태마감이 사용할 예정 근무시간 기준을 제공한다(Why).`

## SCN-FLEX-01 — 일일 근무계획 저장/수정

| 6W | 정의 | Source |
|---|---|---|
| Who | ESS_PROFILE_FLEX 권한을 가진 탄력근로제 근무자 | PPT Slide1; Source WorkProfile |
| When | 매일, 예정 근무일 계획 입력 시 | PPT Slide1 |
| Where | ESS > 근태/휴가 > 탄력근로제 근무계획 | PPT Slide2; flexWorkPlan.jsp |
| What | 근무일자, 근무유형, 시작시간, 종료시간 | PPT Slide2 |
| How | 10분 단위/순서/상태 검증 → 미존재 Create, 존재하면 Update | XLSX TE001~002 + PPT Slide3 + Source |
| Why | 근태집계/마감이 예정 근무시간을 기준으로 사용할 수 있게 함 | PPT Slide1/5 |

### Rules

- BR-FLEX-01: FLEX 대상자만 입력 가능
- BR-FLEX-02: 시간은 10분 단위
- BR-FLEX-03: 시작시간 < 종료시간
- BR-FLEX-04: 사원+근무일자 기준 1개 계획
- BR-FLEX-05: CONFIRMED 상태는 직접 수정 금지

## SCN-FLEX-02 — 월/일 계획 조회

| 6W | 정의 |
|---|---|
| Who | 탄력근로제 근무자 |
| When | 계획 확인/변경 전 |
| Where | 동일 ESS 메뉴 |
| What | 월 Calendar, 일자별 계획, 예상근무시간, 상태 |
| How | 월 조회 → Calendar 표시 → 일자 선택 → 상세 조회 |
| Why | 입력/변경 전 현재 계획과 예상시간을 확인하기 위함 |

## SCN-FLEX-03 — 기본값 및 미입력 알림

| 6W | 정의 |
|---|---|
| Who | 탄력근로제 근무자 / 알람 Batch |
| When | 신규 계획 입력 / 미입력 대상자 점검 시 |
| Where | ESS 기본값 설정 / Batch |
| What | 기본 시작·종료시간 / 미입력 대상 |
| How | 기본값 R/C/U, 신규 계획 초기값 제안, 미입력자 Mail Candidate 생성 |
| Why | 반복 입력을 줄이고 계획 미입력을 예방하기 위함 |

## OPEN / 고객 확인 필요

1. 실제 Profile/Role 명칭과 권한 ID
2. 실제 Menu ID/URL
3. CONFIRMED 실제 상태 Code
4. 휴게시간을 예상근무시간에서 차감하는 방식
5. 알람메일 발송 시각과 수신자
6. 확정 이후 수정 시 예외 승인 프로세스

## Handoff

이 문서는 고객/분석가가 업무의 의미를 확인하는 기준이며, 개발자는 `04_development-blueprint.md`의 UI/CRUD/Query/Data/Source Mapping과 함께 사용한다.