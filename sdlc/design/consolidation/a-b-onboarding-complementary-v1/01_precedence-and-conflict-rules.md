# Complementary Precedence & Conflict Rules

## 1. 동일 개념이 A/B 양쪽에 있을 때

| Concern | Canonical responsibility | Complement |
|---|---|---|
| Raw Requirement Intake | A | B는 evidence quality 표시 |
| RQ Boundary / Split-Merge | A | B는 decision evidence/revision 관리 |
| 6W Business Scenario | A | B는 각 6W 값의 truth/evidence/freshness |
| RQ/FR/BR/AC 구조 | A | B는 authority/scope/temporal guard |
| Customer Functional Spec | A | B는 고객용 agreement/verification 상태 projection |
| Development Blueprint 구조 | A | B는 evidence coverage, blind spot, permission overlay |
| Existing Source Pattern | Shared | A는 설계 Context, B는 current revision/target proof |
| Source Write 허용 | B | A Blueprint는 intent/target input |
| Same-PGM concurrency | B | A Task grouping을 planning input으로 사용 |
| Recovery / Idempotency | B | A 산출물 revision과 source revision을 key input으로 사용 |
| Knowledge/K1 promotion | B guard | A BR/Source candidate를 promotion input으로 사용 |

## 2. ID Rule

A/B가 동일 업무를 표현할 때 새 RQ/FR/BR ID를 중복 생성하지 않는다.

예:

```text
RQ-FLEX-PLAN-001
BR-FLEX-02
PGM-FLEX-WORK-PLAN-001
TASK-FLEX-DEV-001
```

B는 다음 Overlay ID만 추가한다.

```text
EVD-RQ-FLEX-PLAN-001-R3
TWP-PGM-FLEX-WORK-PLAN-001-R2
WU-TASK-FLEX-DEV-001-0001
```

## 3. Truth Conflict

문서와 Source가 충돌하면 최신 파일을 무조건 선택하지 않는다.

```text
Business Policy A1/A2
  vs
Current Source OBSERVED
```

- Source는 AS-IS Evidence다.
- 공식 Policy는 Business Authority다.
- 불일치는 자동 덮어쓰지 않고 `CONTRADICTION`으로 기록한다.
- TO-BE가 필요한지 Historical Document가 잘못된 것인지 Human Review한다.

## 4. Design Conflict

A Development Blueprint가 실제 Source와 충돌하면 Blueprint를 Source에 맞춰 몰래 바꾸지 않는다.

```text
Discovery Finding
→ DESIGN_MISMATCH
→ 영향을 받는 6W/FR/BR/PGM 확인
→ 기술 상세만 잘못되었으면 Blueprint revision
→ 업무 의미가 달라지면 SCOPE_CHANGE_CANDIDATE
```

## 5. Customer View Conflict

고객 View에는 내부 Work Unit/PGM Lane을 기본 노출하지 않는다. 대신 다음으로 투영한다.

- 업무합의: CONFIRMED / REVIEW_REQUIRED / OPEN
- 구현: NOT_STARTED / IN_PROGRESS / IMPLEMENTED
- 검증: NOT_TESTED / TESTED_WITH_GAPS / VERIFIED
- 배포: NOT_READY / READY

Customer Functional Specification의 업무내용은 A 책임, 상태 계산은 B Evidence를 사용한다.

## 6. Source Write Gate

실제 Source Write는 아래를 모두 고려한다.

1. A Development Blueprint의 target/change boundary가 충분한가?
2. B Current Source Evidence가 현재 revision인가?
3. Target Write Proof가 PASS인가?
4. CRITICAL OPEN/Contradiction이 해당 변경에 영향을 주는가?
5. Same-PGM Lane을 소유하는가?
6. Work Unit/idempotency가 준비됐는가?
7. Project security/write policy가 허용하는가?

하나라도 필수 Guard에 실패하면 Patch Proposal은 가능하더라도 actual write는 DENY한다.

## 7. Change Propagation

업무 의미 변경:

```text
CR
→ 6W/RQ/BR/AC revision
→ downstream A artifact STALE
→ B evidence_revision / permission 재계산
→ Impact/Blueprint/Target Proof 재검증
```

기술 구현만 변경:

```text
Impact/PGM/Blueprint revision
→ Source Evidence refresh
→ Target Proof
→ Work Unit
→ Test
```

상위 업무문서는 `UNCHANGED`로 유지할 수 있다.
