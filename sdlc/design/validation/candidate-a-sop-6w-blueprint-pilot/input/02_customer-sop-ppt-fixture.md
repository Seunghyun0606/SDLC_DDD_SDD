# Input 02 — 가상 고객 PPT SoP Fixture

> 이 파일은 실제 고객 PPT가 아니라 Extraction Skill 검증을 위해 만든 `SIMULATED CUSTOMER SOP`다. Slide 번호/Shape 성격을 보존해 PPT 추출 결과를 재현한다.

## Slide 1 — 탄력근로제 근무계획 입력 업무

- 대상: `ESS_PROFILE_FLEX` 권한을 가진 탄력근로제 적용 근무자
- 주기: 매일, 예정 근무일의 근무계획을 입력
- 목적: 근무자의 예정 근무시간을 사전에 등록하여 근태집계/마감 기준으로 사용
- 업무 Channel: ESS

## Slide 2 — 메뉴와 화면

- Menu Path: `ESS > 근태/휴가 > 탄력근로제 근무계획`
- 화면 구성:
  - 월 선택
  - 근무 Calendar
  - 선택 일자 상세입력 Panel
- 입력/노출 Field:
  - 근무일자
  - 근무유형
  - 시작시간
  - 종료시간
  - 예상근무시간(Read Only)
  - 상태(Read Only)
- Button:
  - 조회
  - 저장
  - 수정
  - 기본값 설정

## Slide 3 — 저장/수정 Rule

1. 시간은 10분 단위로 선택한다.
2. 시작시간은 종료시간보다 이전이어야 한다.
3. 근무자/근무일자 기준으로 1개의 근무계획을 유지한다.
4. 계획이 없으면 저장(Create), 기존 계획이 있으면 수정(Update)한다.
5. 확정 상태의 근무계획은 이 화면에서 직접 수정하지 않는다.
6. 예상근무시간은 시작/종료시간을 기준으로 계산하여 보여준다.

## Slide 4 — 조회/Calendar/기본값

- 월 선택 시 해당 월의 근무계획을 Calendar에 표시한다.
- 일자 선택 시 저장된 근무계획을 상세 Panel에 조회한다.
- 기본값 설정에 저장된 시작/종료시간이 있으면 신규 계획 입력 시 초기값으로 제안한다.
- 기본값은 조회/등록/수정 가능하다.

## Slide 5 — 업무 연계

- 저장된 근무계획은 근태집계/근태마감에서 참조한다.
- 당일 기준 근무계획 미입력 대상자는 알람 메일 대상 후보가 된다.
- 전자결재 연계는 본 근무계획 입력 화면 Scope에는 없다.

## Slide 6 — 코드/업무용어

- 근무유형 Code Group: `WORK_TYPE`
- 탄력근무 Code: `FLEX`
- 상태 업무값:
  - `DRAFT`: 입력/수정 가능
  - `CONFIRMED`: 직접 수정 불가
- 10분 단위 자체는 Code가 아니라 Time Validation Rule로 정의한다.

## PPT Extraction Expectation

Skill은 위 Slide에서 최소 다음 Candidate를 뽑아야 한다.

- 6W
- UI Screen/Field/Button
- CRUD
- Validation/State Rule
- Integration Candidate
- Common Code Candidate
- Customer-confirmation/open item

PPT에 없는 DB Table/Java Class/MyBatis Statement는 추정하지 않는다.