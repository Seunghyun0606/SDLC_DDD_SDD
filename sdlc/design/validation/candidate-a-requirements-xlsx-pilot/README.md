# 요구사항목록.xlsx Actual Pilot — Candidate A

> 상태: `VALIDATION PILOT / NOT BASELINE`
> Parent: `SDLC_DESIGN_SESSION_SECOND/validation/candidate-a-rule-skill-template-artifacts`
> 입력: 첨부 `요구사항목록.xlsx`
> 원칙: Candidate A만 적용하며 Candidate B와 결합하지 않는다.

## 1. 실제 실행 결과

| 항목 | 결과 |
|---|---:|
| Raw Row | 142 |
| Legacy ID 보존 | 142 |
| Topic Group | 22 |
| RQ Candidate | 22 |
| FR Candidate | 142 |
| SPLIT_REVIEW_REQUIRED | 3 |
| Clarification Question | 221 |
| Rough PM Work Item | 69 |
| Published RQ | 0 |
| Confirmed BR | 0 |
| Confirmed PGM | 0 |
| Actual Source Write | 0 |
| Verify PASS | 0 |

## 2. 실제 산출 흐름

```text
요구사항목록.xlsx 142 rows
→ Raw Inventory 142
→ Topic Group 22
→ RQ Candidate 22
→ FR Candidate 142
→ Boundary/Split Review
→ Clarification Questions 221
→ Stage Status 264 rows
→ PM Rough Worklist 69 rows
```

`RQ Candidate 22`는 확정된 RQ가 아니다. Candidate A 규칙에 따라 모든 `publish_permission=DENY`다.

## 3. Mega Group

- `TG-017 / RQC-017`: 근태마감, 39 rows
- `TG-018 / RQC-018`: 근태현황/통계, 22 rows
- `TG-019 / RQC-019`: Batch 근무집계, 23 rows

세 Group 모두 `SPLIT_REVIEW_REQUIRED`다.

### TG-017에서 원문으로 관찰되는 하위 흐름 후보

- 월근태 확인
- 일근태 입력/마감
- 월마감
- 마감 후 수정요청
- 퇴직자 근태마감
- 전사 근태마감
- 일근태 강제마감
- 선택적 근로마감

이들은 `INFERRED_CLUSTER / NOT_DECIDED`이며 자동 RQ가 아니다.

## 4. 생성 가능한 문서와 상태

| 영역 | 산출물 | 수량 | 현재 상태 |
|---|---|---:|---|
| Requirement | Requirement Candidate | 22 | CANDIDATE |
| Analysis | FR Candidate | 142 | CANDIDATE |
| Analysis | Clarification Question Set | 22 | OPEN |
| Analysis | Process Analysis | 22 | DRAFT |
| Impact | Impact Analysis | 22 | CANDIDATE / Source evidence missing |
| Design | Functional Design | 22 | DRAFT |
| Program | Confirmed PGM Spec | 0 | NOT_READY |
| Test | Test Scenario Candidate Set | 22 | CANDIDATE |
| Verify | Verification Result | 22 | NOT_READY |
| Management | PM Rough Worklist | 69 | CANDIDATE |

## 5. Source가 없어 확정하지 않은 것

현재 입력에는 Source Repository / Static Index / Test Result가 없으므로 다음은 0건이다.

- Confirmed PGM/ART
- Confirmed Technical Impact
- Target Write Proof
- Actual Source Change
- Executed Test Result
- Verify PASS
- K1/K2 Knowledge

따라서 이 Pilot은 `Legacy Requirement → Requirement/Analysis/Planning 후보 산출물`까지의 실제 데이터 결과를 보여준다.
