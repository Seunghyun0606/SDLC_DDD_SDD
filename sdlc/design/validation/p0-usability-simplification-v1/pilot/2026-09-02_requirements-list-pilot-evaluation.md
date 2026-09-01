# 요구사항목록.xlsx 기반 P0 Pilot 평가

> 기준 Branch: `SDLC_DESIGN_SESSION_SECOND/p0/usability-simplification-v1`  
> 입력: 첨부 `요구사항목록.xlsx` / `Sheet1`  
> Pilot 범위: 전체 142개 Legacy Row 구조화 + `근태마감` 39건 Deep Pilot  
> 판정 원칙: Excel에 없는 Business Truth/Source Mapping/Program/Data/Expected Result를 임의 확정하지 않는다.

---

## 1. Executive Verdict

**P0 PILOT: CONDITIONALLY PASS**

P0의 가장 중요한 목표인 **원본 요구사항 ID 보존, 모호한 RQ 자동확정 금지, OPEN/Escalation 보존, 다음 Agent로의 자기완결형 handoff**는 실제 요구사항목록에서 정상 작동했다.

반면 실제 도입 전 반드시 보강해야 할 P0 Gap도 확인되었다.

가장 큰 Gap은 `rq-boundary.yaml` 앞단에 **Legacy Requirement Normalizer가 정식 실행 계약으로 존재하지 않는 것**이다. 이번 Pilot에서는 `Level2 + 요구사항명`의 정확 일치만을 이용해 142행을 22개 `RQ Group Candidate`로 만들었지만, 이 규칙은 Pilot Convention이며 현재 P0 Core Contract가 아니다.

따라서 현 상태는 다음처럼 판정한다.

- **안전성:** PASS
- **Legacy Excel Intake:** PASS
- **Low-Agent용 기계 처리:** PASS WITH GUARDS
- **RQ/FR 자동 확정:** 의도적으로 BLOCKED
- **사용자 무교육 End-to-End:** 아직 NO
- **Source/Impact/Development/Reverse Sync:** 입력 Source 부재로 NOT TESTED
- **P0 다음 우선순위:** Legacy Requirement Normalizer + Group-level Boundary Contract

---

## 2. 입력 Profile

| 항목 | 결과 |
|---|---:|
| Legacy Requirement Row | 142 |
| 업무 Level1 | 1 (`근태관리`) |
| 업무 Level2 | 10 |
| 서로 다른 `요구사항명` | 22 |
| 중복 Source Requirement ID | 0 |
| 시작일 입력 | 0 / 142 |
| 종료일 입력 | 0 / 142 |
| 담당자 입력 | 0 / 142 |
| 자동 Canonical RQ 발행 | 0 |
| 자동 Canonical FR 발행 | 0 |

원본 Row는 모두 `source_requirement_id`로 보존 가능했고 ID 중복이 없었다.

---

## 3. Pilot Step 1 — Legacy Import

### 수행

각 Excel Row를 다음 상태로 Import했다.

```text
Legacy Row
→ source_requirement_id 보존
→ functional_item = CANDIDATE_ONLY
→ canonical_decision = UNRESOLVED
→ boundary_status = OPEN
```

### 결과

- 142 / 142 Row 원본 ID 보존
- Source Row 삭제/재번호/자동 Merge 없음
- Canonical RQ/FR 자동 Publish 0건
- P0 `RQB-001`, `RQB-003`, `RQB-005` 의도와 일치

**판정: PASS**

---

## 4. Pilot Step 2 — Candidate Normalization

Pilot에서는 Business Truth를 만들지 않는 선에서 **정확히 같은 `Level2 + 요구사항명`**만 묶어 Review Candidate를 생성했다.

결과:

```text
142 Legacy Rows
→ 22 RQ Group Candidates
→ 0 Confirmed Canonical RQ
```

사용자가 처음부터 142행을 하나씩 RQ 여부 판단하는 것과 비교하면 1차 검토 단위가 22개로 줄어 **약 84.5% 감소**한다.

단, 이 22개는 RQ가 아니다. `요구사항명`이 동일하다는 것은 Grouping Evidence일 뿐 Business Outcome 동일성을 증명하지 않는다.

### Candidate Groups

| Candidate | Level2 | 요구사항명 | Source Rows | 상태 |
|---|---|---|---:|---|
| RQG-CAND-017 | 근태마감 | 10분단위 근무계획 개선 근태마감 반영을 구현 | 39 | OPEN / UNRESOLVED |
| RQG-CAND-019 | Batch | 10분단위 근무계획 개선 근무집계 반영을 구현 | 23 | OPEN / UNRESOLVED |
| RQG-CAND-018 | 근태현황/통계 | 10분단위 근무계획 개선 근태현황/통계 반영을 구현 | 22 | OPEN / UNRESOLVED |
| RQG-CAND-013 | 근태/휴가 (ESS) | 10분단위 근무계획 개선 근무계획 반영을 구현 | 9 | OPEN / UNRESOLVED |
| RQG-CAND-004 | 근무계획 수립(탄력근로제) | 탄력근로제 개선 고과제/연봉제 예외사항 요청하는 기능 | 8 | OPEN / UNRESOLVED |
| RQG-CAND-008 | 근태 Report | 탄력근로제 개선 검증 Report 조회하는 기능 | 8 | OPEN / UNRESOLVED |
| RQG-CAND-003 | 근무계획 수립(탄력근로제) | 탄력근로제 개선 연봉제 예외사항 요청하는 기능 | 6 | OPEN / UNRESOLVED |
| RQG-CAND-002 | 근무계획 수립(탄력근로제) | 탄력근로제 개선 고과제 예외사항 요청하는 기능 | 4 | OPEN / UNRESOLVED |
| RQG-CAND-005 | 근무계획 수립(탄력근로제) | 탄력근로제 개선 근무계획 확정/안내하는 기능 | 4 | OPEN / UNRESOLVED |
| RQG-CAND-016 | 근태기록 | 10분단위 근무계획 개선 근태기록 반영을 구현 | 4 | OPEN / UNRESOLVED |
| RQG-CAND-001 | 근무계획 수립(탄력근로제) | 탄력근로제 개선 최초근무계획 자동 설정하는 기능 | 3 | OPEN / UNRESOLVED |
| RQG-CAND-021 | 근태/휴가 (ESS) | 10분단위 근무계획 개선 입출문시간 정보에 반영을 구현 | 2 | OPEN / UNRESOLVED |
| RQG-CAND-006 | 근무계획 수립(탄력근로제) | 탄력근로제 개선 운영이력 조회하는 기능 | 1 | OPEN / UNRESOLVED |
| RQG-CAND-007 | 근태/휴가 (ESS) | 탄력근로제 개선 확정 조회하는 기능 | 1 | OPEN / UNRESOLVED |
| RQG-CAND-009 | Interface | 탄력근로제 개선 데이터 HR Analytics 송신하는 기능 | 1 | OPEN / UNRESOLVED |
| RQG-CAND-010 | 근태기록 | 탄력근로제 개선 휴가내역 근태 집계하는 기능 | 1 | OPEN / UNRESOLVED |
| RQG-CAND-011 | 근태기록 | 탄력근로제 개선 근무내역 근태 집계하는 기능 | 1 | OPEN / UNRESOLVED |
| RQG-CAND-012 | 근태기록 | 탄력근로제 개선 출장/교육내역 집계하는 기능 | 1 | OPEN / UNRESOLVED |
| RQG-CAND-014 | 선택적근무제 | 10분단위 근무계획 개선 선택적근무관리 반영을 구현 | 1 | OPEN / UNRESOLVED |
| RQG-CAND-015 | 선택적근무제 | 10분단위 근무계획 개선 선택적근무관리 반영하는 기능 | 1 | OPEN / UNRESOLVED |
| RQG-CAND-020 | Interface | 10분단위 근무계획 개선 Yellow Page 송신 반영을 구현 | 1 | OPEN / UNRESOLVED |
| RQG-CAND-022 | 메인화면 | 10분단위 근무계획 개선 주간스케쥴 반영을 구현 | 1 | OPEN / UNRESOLVED |

**판정: PARTIAL PASS**

이유: 결과는 유용하지만 Candidate Group 생성 규칙이 아직 P0의 정식 Normalizer Contract로 정의되어 있지 않다.

---

## 5. Pilot Step 3 — `근태마감` 39건 Deep Pilot

대상:

`REQ_TM_TE016` ~ `REQ_TM_TE054`

공통 입력:

- Level1: `근태관리`
- Level2: `근태마감`
- 요구사항명: `10분단위 근무계획 개선 근태마감 반영을 구현`

### 문제

39행을 하나의 RQ로 만들면 너무 크고, 39행을 각각 RQ로 만들면 과도하게 세분화된다.

P0 규칙에 따라 자동 Split/Merge는 하지 않았다.

대신 `요구사항` 문자열의 명시적인 시작 표현만 이용하여 **Subgroup Candidate**를 생성했다.

| Candidate | 표시명 | Source Rows | 상태 |
|---|---|---:|---|
| SG-01 | 월근태확인 | 1 | CANDIDATE_ONLY / INFERRED |
| SG-02 | 일근태입력/마감 | 8 | CANDIDATE_ONLY / INFERRED |
| SG-03 | 월마감 | 8 | CANDIDATE_ONLY / INFERRED |
| SG-04 | 일/월마감후 수정요청 | 7 | CANDIDATE_ONLY / INFERRED |
| SG-05 | 퇴직자근태마감 | 5 | CANDIDATE_ONLY / INFERRED |
| SG-06 | 전사근태마감 | 2 | CANDIDATE_ONLY / INFERRED |
| SG-07 | 일근태 강제마감 | 2 | CANDIDATE_ONLY / INFERRED |
| SG-08 | 선택적 근로마감 | 6 | CANDIDATE_ONLY / INFERRED |

39개 개별 Row를 8개 Subgroup Candidate로 제시하므로 L2/Human의 1차 검토 단위가 약 **79.5% 감소**한다.

그러나 이 8개도 Canonical RQ가 아니다.

예를 들어 `일근태입력/마감` 내부에는 조회, 신청 CRUD, 강제마감, 전자결재 송수신이 섞여 있고, 이것들이 하나의 Business Outcome인지 여러 Outcome인지는 Excel만으로 확인할 수 없다.

**판정: PASS AS CANDIDATE / BLOCK AS CANONICAL**

---

## 6. Pilot Step 4 — Stage Input Pack

`근태마감` 39개 Source ID를 하나의 `RQ_CANDIDATE` Stage Input Pack으로 구성했다.

Pack에는 다음을 보존했다.

- 39개 `source_requirement_id`
- GIVEN: Level1 / Level2 / 요구사항명
- OBSERVED: 동일 Group에 39개 Row 존재
- 8개 Subgroup Candidate
- `BOUNDARY_AMBIGUOUS`
- `PROCESS_UNDERDEFINED`
- `MISSING_REQUIRED_SOURCE`
- 다음 Action / Escalation 대상
- Source 없는 상태에서 Program/DB를 추론하지 않는 Constraint

### 중요 발견

**Stage Input Pack은 Legacy Row별 1개가 아니라 Work Unit / Candidate Group별 1개가 적합하다.**

142행마다 Stage Pack을 생성하면 P0의 단순화 목적이 다시 무너진다.

권장 Granularity:

```text
Legacy Row 1..N
→ Candidate Group
→ Group-level Stage Input Pack 1개
→ 필요한 경우 Subgroup Pack으로 Split
```

**판정: PASS, 단 Granularity Rule 추가 필요**

---

## 7. Stage별 실제 진행 결과

| Stage | 실제 Pilot 결과 | 상태 | 평가 |
|---|---|---|---|
| INTAKE | 142개 Row 원본 보존 | PASS | 저수준 Agent도 기계 처리 가능 |
| DECOMPOSE | 22 Group Candidate 생성 | PARTIAL PASS | Normalizer가 아직 Pilot Convention |
| RQ BOUNDARY | 자동확정 0, 모두 OPEN 유지 | PASS | 가장 중요한 안전 Guard 동작 |
| CLARIFY | Boundary/Actor/State/권한/Expected Result 질문 생성 가능 | PASS | 다음 질문이 명확함 |
| PROCESS | 근태마감/전자결재 등 Process 후보만 가능 | DRAFT ONLY | Actor/State/Exception 부재 |
| DISCOVERY | Source Repository 없음 | SAFE STOP | Source를 지어내지 않음 |
| IMPACT | Business 후보 외 Technical Impact 확정 불가 | SAFE STOP | 정상적인 fail-safe |
| DESIGN | 화면/Transaction/Auth/Validation 확정 불가 | DRAFT ONLY | 입력 부족 |
| PROGRAM | PGM/ART/SYMBOL Evidence 없음 | SAFE STOP | 정상 |
| DEVELOPMENT | Write Target 없음 | BLOCKED | 정상 |
| TEST | CRUD/조회 기반 TC 후보 일부 가능 | DRAFT ONLY | Expected Result/Boundary 부족 |
| VERIFY | 실행/Test Result 없음 | BLOCKED | 정상 |
| REVERSE SYNC | Source Diff 없음 | NOT TESTED | 별도 Source Pilot 필요 |

이 Pilot에서 `SAFE STOP`은 실패가 아니라 **P0가 추론 과잉을 차단했다는 성공 신호**다.

---

## 8. Low-Agent 평가

### L1 Agent가 가능한 작업

- Excel Row 읽기
- Source ID 보존
- 필수 컬럼 존재 검사
- 동일 `Level2 + 요구사항명` Candidate grouping
- Row Count / Duplicate 검사
- Stage Input Pack 필드 채우기
- OPEN 유지
- Validator 실행

### L1 Agent가 하면 안 되는 작업

- 22개 Candidate를 Canonical RQ로 확정
- `근태마감` 39행을 임의의 8개 RQ로 Publish
- 전자결재를 API라고 추론
- `송신/수신`을 특정 Middleware로 단정
- CRUD 이름으로 Transaction/State를 확정
- Source 없이 PGM/DB Impact를 작성

### L2/Human이 필요한 작업

- 독립 Business Outcome 경계
- Group Split/Merge
- Actor/Owner/Release/AC 경계
- 마감/강제마감/수정요청 상태전이
- 전자결재 승인/반려/취소/재처리 규칙

**Low-Agent 판정: YES WITH DETERMINISTIC GUARDS for Intake/Normalization, L2_OR_HUMAN for Boundary**

---

## 9. P0에서 실제로 잘 된 점

### 9.1 Hallucination 억제

기존 방식이라면 `요구사항명`을 바로 RQ로 사용하기 쉽지만 P0는 `UNRESOLVED`를 정상 상태로 인정한다.

### 9.2 원본 Trace 보존

142개 기존 ID를 모두 유지하므로 이후 고객 원장과 Canonical 간 역추적이 가능하다.

### 9.3 Human Review 양 감소

Candidate grouping만으로 첫 검토 단위를 142 → 22로 줄일 수 있다.

### 9.4 거대한 RQ 감지

39 / 23 / 22 Row를 가진 3개 Candidate가 자동으로 눈에 띈다. 이들은 일반 RQ보다 추가 Boundary Review가 필요한 후보로 식별하기 쉽다.

### 9.5 Source 부재 시 정상 정지

Program/DB/Impact를 Excel 이름만 보고 만들어내지 않았다.

---

## 10. Pilot에서 드러난 P0 Gap

### P0-GAP-01 — Legacy Requirement Normalizer 부재 — **P0 필수**

현재 `rq-boundary.yaml`은 Boundary 결정을 정의하지만 그 앞단의 다음 처리가 정식 계약이 아니다.

```text
Legacy Row
→ Candidate Group
→ Candidate Functional Item
→ Boundary Review
```

이번 Pilot에서는 별도 규칙으로 처리했다.

**권장:** `legacy-requirement-normalizer.yaml` 추가.

최소 설정:

- source id column
- group candidate key
- exact / configured grouping
- candidate-only 보장
- max group size alert
- heterogeneous action signal
- source row immutable
- auto canonical publish = false

---

### P0-GAP-02 — Boundary Schema가 Row 중심

현재 Boundary Record는 `source_requirement_id` 단위다.

그러나 실제 고객 검토는 39개 Row 각각이 아니라 **Group 단위 의사결정**이 자연스럽다.

권장:

```text
source_requirement_ids: [...]
candidate_group_id
decision
canonical_rq_ids
canonical_fr_ids
```

를 지원하는 Group Boundary Contract를 추가한다.

---

### P0-GAP-03 — Stage Input Pack Granularity 미정

Pack을 Row마다 만들지 Group마다 만들지 계약이 없다.

이번 Pilot 결과 **Group/Work Unit 단위가 기본**이어야 한다.

---

### P0-GAP-04 — `Functional Item Candidate` 계층이 명확하지 않음

Legacy Row를 바로 FR Candidate라고 부르면 또 다른 과확정이 발생할 수 있다.

권장 상태:

- `SOURCE_FUNCTIONAL_ITEM`
- `FR_CANDIDATE`
- `CANONICAL_FR`

를 구분한다.

---

### P0-GAP-05 — 대형 Candidate 자동 Review Trigger 필요

다음 3개는 각각 39 / 23 / 22개 Row를 가진다.

- 근태마감
- 근무집계
- 근태현황/통계

단순 Row Count만으로 Split하지는 않되 `LARGE_GROUP_REVIEW` Alert를 자동 생성하는 것이 적합하다.

---

### P0-GAP-06 — Source Reverse Sync는 아직 검증되지 않음

이번 입력에는 Source Repository/Commit/Diff가 없기 때문에 Reverse Sync Contract는 실행할 수 없었다.

이는 설계 실패가 아니라 **별도의 Brownfield Source Pilot이 필요하다는 의미**다.

---

## 11. Artifact Profile 평가

이번 Pilot의 시작점에서는 `STANDARD`가 적합하다.

이유:

- Legacy/Brownfield 성격
- 전자결재/Batch/Interface 후보 존재
- 39개 대형 Candidate 존재
- Source Impact가 아직 미확인

그러나 고객에게 15개 문서를 한꺼번에 요구할 이유는 없다.

Pilot 기준 사람에게 우선 보일 산출물은 다음이면 충분하다.

1. 전체 작업목록
2. Requirement Review View
3. Engineering Design — Source 연결 이후
4. Test/Verification — 후속 단계

6W/Process/PGM 문서는 필요 조건이 확인될 때 분리 생성하는 현재 P0 Profile 방향이 적합하다.

**판정: PASS**

---

## 12. 정량 평가

| 항목 | 점수 | 평가 |
|---|---:|---|
| Source ID / 원본 보존 | 10/10 | 142/142 보존 가능 |
| Boundary Safety | 9/10 | 자동확정 차단 성공 |
| Low-Agent Intake | 9/10 | 기계 처리 가능 |
| Candidate Grouping 재현성 | 6/10 | Pilot에서는 가능, Core Normalizer 부재 |
| Stage Handoff | 8/10 | Group-level Pack 효과적 |
| Human Review Usability | 7/10 | 142→22 감소, 대형 Group 추가 처리 필요 |
| Over-engineering 억제 | 8/10 | Profile 방향 적합, Pack granularity 명시 필요 |
| Brownfield Source 연결 | N/T | Source 미첨부 |
| Reverse Sync | N/T | Source Diff 미첨부 |
| 무교육 전체 실행 | 6/10 | Boundary 판단 지침/Normalizer UI 보강 필요 |

### Tested Scope Score

**63 / 80 = 78.8%**

검증하지 못한 Source/Reverse Sync를 점수에 억지로 포함하지 않았다.

---

## 13. 최종 판정

### 이 요구사항목록으로 P0 Pilot을 시작할 수 있는가?

**YES**

### Excel만으로 전체 SDLC를 자동 진행할 수 있는가?

**NO — 그리고 자동 진행되지 않는 것이 올바른 동작이다.**

### BA + Dev + PM이 별도 교육 없이 바로 운영할 수 있는가?

**YES WITH GUIDANCE**

이전보다 개선되었지만, `Candidate Group`, `Boundary OPEN`, `L2/Human 결정`의 의미를 화면/가이드에서 한 번은 설명해야 한다.

### 저수준 Agent가 이전 대화 없이 실행할 수 있는가?

**YES WITH DETERMINISTIC GUARDS — INTAKE/NORMALIZE 한정**

RQ Boundary부터는 P0 정의대로 L2/Human Escalation이 필요하다.

---

## 14. P0 후속 우선순위

### P0.1 — 반드시 추가 권장

1. Legacy Requirement Normalizer Contract
2. Group-level Boundary Schema
3. Stage Input Pack Granularity Rule
4. `SOURCE_FUNCTIONAL_ITEM → FR_CANDIDATE → CANONICAL_FR` 상태 분리
5. `LARGE_GROUP_REVIEW` deterministic alert

### 다음 Pilot

Source Repository/Snapshot을 연결할 수 있다면 `근태마감` Candidate 하나를 대상으로:

```text
Candidate Group
→ Human Boundary Decision
→ Source Discovery
→ Impact
→ Engineering Design
→ 1 PGM Source Change Proposal
→ Test Candidate
→ Source Diff Reverse Sync
```

까지 진행해야 P0의 Brownfield 핵심인 Source↔Documentation 양방향 계약을 완전히 평가할 수 있다.
