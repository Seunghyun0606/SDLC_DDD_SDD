# 08. 6W Business Analysis Guide

## 기본 단위
6W는 RQ 전체가 아니라 **핵심 Business Scenario** 단위로 작성한다.

```text
RQ
├ Scenario 1: Who/When/Where/What/How/Why
└ Scenario 2: Who/When/Where/What/How/Why
```

## 정의
- Who: Role/조직/대상/권한/Profile/System Actor
- When: Trigger/Frequency/State/Effective/Cutoff
- Where: Menu/Screen/Channel/Batch/API/조직/국가
- What: Object/Input/Output/Field/State
- How: CRUD/Validation/계산/승인/Transition/Exception/Integration
- Why: Goal/Policy/Pain Point/Control/규정

## 6W→RQ/FR/BR/AC 예

```text
Who: ESS 탄력근로제 근무자
When: 매일
Where: 근무계획 메뉴
What: 날짜/시작/종료
How: 10분 단위 저장
Why: 근태마감 기준 제공
```

RQ: 탄력근로제 일일 근무계획 관리

FR:
- 월/일 조회
- 계획 저장/수정
- 예상시간 계산

BR:
- FLEX 대상자만
- 10분 단위
- start < end
- 확정상태 수정 제한

AC:
- 09:00~18:10 성공
- 09:05 실패
- 비대상자 실패

## 규칙
- 원문에 없으면 OPEN
- Source 현행동작은 AS-IS Evidence
- Why를 임의 정책으로 만들지 않음
- 서로 다른 Who/Trigger/Lifecycle/Release면 Split 후보
- 파일/테이블 수만으로 RQ Split 금지
