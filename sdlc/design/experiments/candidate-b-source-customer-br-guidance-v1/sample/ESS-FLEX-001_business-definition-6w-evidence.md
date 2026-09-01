# ESS-FLEX-001 탄력근로제 일일 근무계획 저장 — 6W Evidence Sample

> 사용자가 제시한 예시를 구조화한 비교용 Sample이며 실제 고객 SoP Evidence가 아니다.

| 6W | Value | Truth | Evidence |
|---|---|---|---|
| Who | ESS Profile 권한을 가진 탄력근로제 근무자 | GIVEN_EXAMPLE | current user example |
| When | 매일 | GIVEN_EXAMPLE | current user example |
| Where | ESS > 탄력근로제 근무계획 메뉴 | GIVEN_EXAMPLE | current user example |
| What | 날짜/시작시간/종료시간 | GIVEN_EXAMPLE | current user example |
| How | 날짜/시간 선택 후 근무계획 저장 | GIVEN_EXAMPLE | current user example |
| Why | 근무자는 매일 예정 근무시간을 입력해야 함 | GIVEN_EXAMPLE | current user example |

## Development Evidence Gaps

- 실제 ESS 권한/Profile Code
- 화면 ID/URL/Menu ID
- 날짜/시간 Field Type과 10분 단위 Validation
- 저장이 INSERT인지 UPSERT인지
- 수정/삭제 허용 상태
- 탄력근로제 기간/법정시간 Rule
- 휴일/휴가/마감 충돌 Rule
- 승인/근태마감/알림 Integration
- Work Plan Table/Key
- 근무제/상태 Common Code

따라서 현재 권한:

```yaml
business_definition_candidate: ALLOW
customer_review_view: ALLOW
development_blueprint_draft: ALLOW
real_source_write: DENY
```

실제 SoP/Source에서 Gap Evidence를 채우면 권한을 다시 계산한다.
