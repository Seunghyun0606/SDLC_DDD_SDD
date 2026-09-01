# ESS-FLEX-001 탄력근로제 일일 근무계획 저장 — 6W 업무정의 Sample

> 입력 근거: 사용자가 제시한 업무 예시. 실제 고객 Source로 Confirm된 내용이 아니므로 `PILOT_EXAMPLE`이다.

## 1. 6W

| 6W | 내용 | 상태 |
|---|---|---|
| Who | ESS Profile 권한을 가진 탄력근로제 근무자 | GIVEN_EXAMPLE |
| When | 매일 근무계획 입력 시 | GIVEN_EXAMPLE |
| Where | ESS > 탄력근로제 근무계획 메뉴 | GIVEN_EXAMPLE |
| What | 근무일자, 시작시간, 종료시간 | GIVEN_EXAMPLE |
| How | 날짜/시간 선택 → 유효성검증 → 근무계획 저장 | GIVEN_EXAMPLE + 일부 분해 |
| Why | 근무자는 매일 예정 근무시간을 입력해야 함 | GIVEN_EXAMPLE |

## 2. Scenario

```text
ESS Profile을 가진 탄력근로제 근무자
→ 매일
→ ESS 탄력근로제 근무계획 메뉴에서
→ 근무일자/시작시간/종료시간을 입력하고
→ 저장을 누르면
→ 입력값/정책을 검증한 후 근무계획을 저장한다.
```

## 3. 후속 설계로 반드시 내려갈 질문

### UI / Field
- 근무일자 기본값은 오늘인가?
- 시작/종료시간은 10분 단위인가?
- 휴게시간 입력이 필요한가?
- 조회기간/달력/Grid 구성은 무엇인가?
- 저장/수정/삭제 버튼 노출조건은 무엇인가?

### CRUD
- 동일 근무일자의 기존 계획이 있으면 INSERT인가 UPDATE인가?
- 월/주 단위 조회가 필요한가?
- 마감 이후 수정/삭제 가능한가?

### Core Rule
- 최소/최대 근무시간
- 일/주 법정시간 검증
- 탄력근로제 적용기간 검증
- 휴일/휴가/근태마감 상태와의 충돌

### Integration
- 승인 Workflow가 있는가?
- 근태마감/스케줄/전자결재/알림과 연계되는가?

### Data / Code
- Work Plan Table/Key
- 근무제 유형 Code
- ESS Profile/권한 Code
- 시간단위 Code 또는 Config

이 질문에 답이 없으면 개발자가 화면/DB/Rule을 임의 설계해서는 안 된다.
