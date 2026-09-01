# Input 02 — 가상 고객 PPT SoP Evidence Fixture

> `SIMULATED CUSTOMER SOP`이며 실제 고객 문서가 아니다.

## Slide 1 — 업무 대상/목적
- Who: `ESS_PROFILE_FLEX` 권한의 탄력근로제 근무자
- When: 매일 예정 근무일 계획 입력
- Why: 예정 근무시간을 사전 등록하여 근태집계/마감 기준 제공

## Slide 2 — Menu/UI
- Where: `ESS > 근태/휴가 > 탄력근로제 근무계획`
- Fields: 근무일자, 근무유형, 시작시간, 종료시간, 예상근무시간, 상태
- Buttons: 조회, 저장, 수정, 기본값 설정

## Slide 3 — Rule
- 10분 단위 시간선택
- 시작 < 종료
- 사원/일자별 1계획
- 미존재 Create / 존재 Update
- CONFIRMED 상태 직접 수정 금지

## Slide 4 — 조회/기본값
- 월 Calendar 조회
- 일자 상세 조회
- 기본값 조회/등록/수정

## Slide 5 — Integration
- 근태집계/근태마감에서 근무계획 참조
- 미입력자는 알람메일 후보
- 전자결재는 화면 Scope 없음

## Slide 6 — Code/State
- Common Code Candidate: `WORK_TYPE/FLEX`
- Business State: `DRAFT`, `CONFIRMED`
- 10분 단위는 Validation Rule

## Evidence Policy

- Source type: `SOP_PRESENTATION`
- Authority: `PILOT_GIVEN`
- Locator: Slide 번호 유지
- Physical Java/Table/SQL은 이 문서에서 추정 금지
- `CONFIRMED`가 업무표현인지 실제 DB Code인지 구분해야 함