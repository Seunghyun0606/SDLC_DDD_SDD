# 03. Sample Validation and Candidate Comparison

> 상태: `EXPERIMENT VALIDATION`
> Sample: `요구사항목록.xlsx`
> Baseline: v1.5.1
> Candidate: Stage Evidence + Execution Contract B
> 원칙: Excel에 없는 업무/기술 의미를 임의로 확정하지 않는다.

# 1. Quick Result

## 판정: `PASS AS A STAGE-SAFETY CONTRACT / NOT AN END-TO-END IMPLEMENTATION`

Candidate B를 첨부 Sample에 적용하면 다음이 가능하다.

```text
142 Raw Requirement Rows
→ Intake/Decompose Candidate
→ Clarification/Process/Design Draft
→ Evidence Gap을 유지한 채 다음 준비 작업 진행
→ Source 없는 PROGRAM/DEVELOPMENT actual write는 Guard
→ Test Result 없는 VERIFY PASS는 Guard
```

이 설계는 Sample만으로 모든 Stage를 완료시키는 것이 아니라 **Evidence가 없는 상태를 정상적으로 표현하면서 Workflow를 계속시키는 것**을 합격 조건으로 둔다.

# 2. Sample Re-check

첨부 Workbook을 다시 확인한 결과:

| 항목 | 결과 |
|---|---:|
| Raw Row | 142 |
| Level1 | 1 (`근태관리`) |
| Level2 | 10 |
| 서로 다른 요구사항명 | 22 |
| FL Prefix | 39 |
| TE Prefix | 103 |
| 중복 기존 요구사항 ID | 0 |
| 시작일 입력 | 0/142 |
| 종료일 입력 | 0/142 |
| 담당자 입력 | 0/142 |

상위명 기준 큰 Group:

| 요구사항명 | 행 수 | 범위 |
|---|---:|---|
| 10분단위 근무계획 개선 근태마감 반영을 구현 | 39 | REQ_TM_TE016~054 |
| 10분단위 근무계획 개선 근무집계 반영을 구현 | 23 | REQ_TM_TE077~099 |
| 10분단위 근무계획 개선 근태현황/통계 반영을 구현 | 22 | REQ_TM_TE055~076 |

이 관찰은 Candidate A와 동일한 Source Fixture에서 나온 사실이지만 Candidate B의 Core Contract가 `1 Row = RQ` 또는 `요구사항명 = RQ`를 요구하지는 않는다.

# 3. Sample Stage Evidence Matrix

| Stage | Sample에서 생성 가능한 결과 | workflow_exit | 주요 Action Permission | 판정 |
|---|---|---|---|---|
| INTAKE | Raw/Candidate Requirement + missing problem/outcome | OPEN | Canonical Publish = REVIEW/MAPPING 의존 | PASS |
| DECOMPOSE | 22 Group/142 Detail을 이용한 FR Candidate seed | OPEN | 자동 Published RQ/FR = DENY | PASS |
| CLARIFY | Actor/Trigger/정책/예외/범위 질문 | OPEN | BR CONFIRMED/K1 = DENY | PASS |
| PROCESS | 승인/송신/마감/Batch 흐름 Draft | OPEN | PROC Confirm = DENY without Truth | PASS |
| DISCOVERY | Source query + blind-spot checklist | OPEN | Discovery COMPLETE = DENY without Source | PASS |
| IMPACT | Business/Technical seed + missing evidence | OPEN | MODIFY/VERIFY_ONLY 확정 = DENY | PASS |
| DESIGN | Validation/State/Tx/Auth/NFR Skeleton | OPEN | Source Write permission과 독립 | PASS |
| PROGRAM | Program discovery condition | OPEN | PGM CONFIRMED = DENY | PASS |
| DEVELOPMENT | Patch Proposal 수준 | OPEN for other safe work | actual Source Write = DENY | PASS |
| TEST | TC Candidate/expected evidence request | OPEN | Test PASS = DENY | PASS |
| VERIFY | NOT_READY Verification Result | OPEN for unrelated work | VERIFY PASS = DENY | PASS |
| KNOWLEDGE | K3 historical candidate | OPEN | K1/K2 Promotion = DENY | PASS |
| PM/TASK | ROUGH Worklist | OPEN | null 담당/일정 허용 | PASS |

# 4. Scenario Validation

## Scenario A — FL001~003 최초 근무계획 자동 설정

Sample 내용:

- 근무계획 저장
- 근무계획 조회
- 기본 근무스케줄에 따라 자동 생성/저장

Candidate B Expected:

```text
INTAKE/DECOMPOSE Candidate
→ workflow_exit OPEN
→ CLARIFY 질문 생성
   - 자동 생성 Trigger
   - overwrite 규칙
   - 적용 대상/기간
   - 저장 실패 원자성
→ PROCESS/DESIGN Draft
→ Source Discovery Required
→ actual Source Write DENY
```

Silent Failure 방어:

- `자동 저장` 문구를 Transaction/Idempotency 규칙으로 CONFIRMED하지 않는다.
- PGM/ART를 이름 유사도로 확정하지 않는다.

## Scenario B — FL014~021 승인/전자결재

세부 요구에는 등록/삭제/조회, 결재 송신/수신, 승인 후처리, 취소가 포함된다.

Risk Trigger:

- Interface
- State Transition
- Retry
- Duplicate receive
- Compensation
- Authorization

Context Escalation Expected:

```text
Summary/Snippet only
→ NOT ENOUGH
→ Interface config + sender/receiver code + full transaction scope + error handling
```

Source가 없으므로 현재 Sample에서는 Escalation **요청 조건만 생성**하고 실제 Source Context가 채워졌다고 간주하지 않는다.

## Scenario C — TE016~054 근태마감 39행

Candidate B는 Grouping 구조 자체를 결정하지 않는다.

Expected:

- `granularity_uncertainty = HIGH`
- `workflow_exit = OPEN`
- Process/Impact Candidate는 생성 가능
- Mega-RQ 자동확정 금지
- Source Write Target Proof 생성 불가

즉 `SPLIT_REVIEW_REQUIRED` 같은 Intake Rule은 Candidate A가 더 구체적이다. Candidate B에서는 이를 외부 Intake Adapter의 Alert로 받아 Stage Evidence에 보존한다.

## Scenario D — TE077~099 Batch 23행

Red Team blind spot을 강제로 표면화한다.

Required `blind_spots` 후보:

- Scheduler/Job
- Shared Procedure
- Dynamic SQL
- Trigger
- File I/O
- DB Polling
- downstream Payroll/Settlement consumer
- Runtime schedule/cut-off

Excel 이름만으로 `Impact COMPLETE`, `PGM MODIFY`, `VERIFY_ONLY`를 만들면 FAIL이다.

## Scenario E — FL036/TE100 송신 Interface

`송신`은 API라는 뜻이 아니다.

Candidate B Expected evidence request:

- transport type
- endpoint/file/table/MQ
- auth/secret
- payload/data classification
- retry/timeout
- duplicate prevention
- monitoring/retention

Security boundary가 확인되기 전 외부 Model Context에 interface secret/schema를 그대로 전송하면 FAIL이다.

# 5. Wrong Target Stress Test

가정:

```text
Target Resolver:
PGM-A score 0.94 HIGH
PGM-B score 0.52
```

하지만 Source/Canonical current revision evidence가 없다.

Candidate B Expected:

```text
resolver_confidence = HIGH
target_write_proof = FAIL
Patch Proposal = ALLOW
actual Source Write = DENY
```

이것이 Candidate B가 v1.5.1의 단순 confidence threshold보다 추가하는 핵심 안전계약이다.

# 6. `/work` Retry Stress Test

가정:

1. Source patch apply 성공
2. Canonical delta 쓰기 전에 process crash
3. 사용자가 `/work` 재실행

Expected:

```text
기존 APPLIED Work Unit 발견
→ 동일 patch 재적용 금지
→ source fingerprint 확인
→ Canonical delta부터 resume 또는 recovery
→ RECOVERY_REQUIRED가 해소되기 전 DONE/PASS 표시 금지
```

Candidate A Sync Contract에서도 Process Crash Recovery는 미검증 영역으로 남아 있었으므로 Candidate B가 이 공백을 직접 다룬다.

# 7. Contract Validation Summary

| Validation | Expected | Result |
|---|---|---|
| Raw 142 row를 142 Published RQ로 자동 승격하지 않음 | 0 auto publish | PASS by contract |
| Source 없는 Discovery COMPLETE | 0 | PASS by contract |
| Source 없는 PROGRAM CONFIRMED | 0 | PASS by contract |
| Target proof 없는 Source Write | 0 | PASS by contract |
| Test Result 없는 VERIFY PASS | 0 | PASS by contract |
| Scope 없는 K1 Global Promotion | 0 | PASS by contract |
| CRITICAL uncertainty 중 Draft 분석 진행 | 가능 | PASS |
| 담당/일정 null 때문에 Workflow block | 0 | PASS |
| retry duplicate source apply | 0 | PASS by Work Unit contract |
| partial failure를 정상 DONE으로 표시 | 0 | PASS by Recovery state |

주의: `PASS by contract`는 구현 자동테스트가 통과했다는 뜻이 아니다. 실제 PoC 코드/Converter/Router가 아직 없으므로 **Implementation NOT VERIFIED**다.

# 8. Candidate Comparison

Candidate A와 B는 같은 문제의 단순 대안이 아니라 독립 설계축이다.

| 항목 | Candidate A — Intake/Sync | Candidate B — Stage/Execution | Scenario 근거 |
|---|---|---|---|
| 비숙련 사용자 이해성 | 강함 | 중상 | A는 Raw→RQ→FR을 설명. B는 내부 Evidence 상태를 사용자 문구로 숨겨야 쉬움 |
| Brownfield 적용성 | 강함 | 강함 | A는 Legacy Excel, B는 Source blind spot/target/recovery 대응 |
| Greenfield 적용성 | 중상 | 강함 | A의 Legacy Normalizer 필요성 낮음. B Stage Contract는 동일 적용 |
| Legacy 문서 수용성 | 매우 강함 | 중상 | A가 Mapping Overlay/Raw 보존을 직접 정의 |
| Non-blocking 적합성 | 강함 | 매우 강함 | B가 workflow_exit와 action permission을 명시적으로 분리 |
| Silent Failure 방어 | 중상 | 매우 강함 | B가 false COMPLETE/PASS/HIGH와 partial failure를 직접 차단 |
| Traceability | 강함 | 강함 | A source_item_id/round-trip, B evidence revision/work unit lineage |
| PM 사용성 | 강함 | 중상 | A Worklist/Optional field가 직접적. B는 recovery/guard 상태 추가 필요 |
| MD↔Excel 사용성 | 매우 강함 | 약함/비대상 | A의 핵심 설계축 |
| Customizing 용이성 | 강함 | 강함 | A mapping overlay, B stage/evidence policy overlay 가능 |
| Recovery / Idempotency | 약함/미구현 | 매우 강함 | B 핵심 설계축 |
| Security | 중간 | 강함 | B outbound/model/secret/environment guard 포함 |
| 구현 복잡도 | 중간 | 높음 | B journal/fingerprint/invariant가 추가됨 |
| 운영 복잡도 | 중간 | 중상~높음 | B recovery state와 journal 운영 필요 |
| Token 비용 | 낮음~중간 | 중간~높음 | B risk-based escalation로 고위험 Context 확대 |
| 다른 프로젝트 재사용성 | 강함 | 매우 강함 | B는 입력 형식과 무관한 Stage/Execution 공통계약 |

# 9. Candidate B 자체 평가

| 비교 기준 | 평가 | Scenario 기반 근거 |
|---|---|---|
| 비숙련 사용자 이해성 | 4/5 | 내부 상태를 `분석 가능/실제 수정 보류`로 번역하면 사용자는 계약 구조를 몰라도 됨 |
| Brownfield 적용성 | 5/5 | Trigger/Dynamic SQL/Batch/Polling/Reflection blind spot을 명시 필드로 보존 |
| Greenfield 적용성 | 5/5 | Source가 새로 생기는 Greenfield에서도 Target revision/Test evidence/Work Unit 동일 적용 |
| Legacy 문서 수용성 | 3/5 | 입력 정규화는 별도 Adapter에 위임; Candidate A보다 약함 |
| Non-blocking 적합성 | 5/5 | workflow와 actual action 분리 |
| Silent Failure 방어 | 5/5 | false COMPLETE/PASS/HIGH와 partial failure가 핵심 검증대상 |
| Traceability | 5/5 | evidence revision + work unit + side effect lineage |
| PM 사용성 | 4/5 | guard/recovery 상태를 PM Risk로 보여줄 수 있으나 UI 설계 필요 |
| MD↔Excel 사용성 | 2/5 | 직접 해결하지 않음 |
| Customizing 용이성 | 4/5 | Stage action/evidence policy를 Project Overlay로 이동 가능 |
| Recovery / Idempotency | 5/5 | journal/idempotency가 core |
| Security | 4/5 | 최소 trust boundary 포함, Enterprise RBAC/retention 상세는 후속 필요 |
| 구현 복잡도 | 2/5 | Candidate A보다 구현 난이도가 높음 |
| 운영 복잡도 | 3/5 | recovery journal 청소/감사/상태 설명 부담 |
| Token 비용 | 3/5 | 고위험에서 Context 확대를 의도적으로 허용 |
| 다른 프로젝트 재사용성 | 5/5 | 입력 형식보다 Stage/Side Effect semantics에 의존 |

# 10. Red Team Regression Check

| 기존 위험 | Candidate B 처리 |
|---|---|
| HIGH-confidence Wrong Target | confidence와 Target Write Proof 분리 |
| Knowledge Poisoning | authority/scope/effective period + K1 permission |
| Truth Temporal 오류 | effective period/last verified 요구 |
| Static Analysis Blind Spot | blind_spots/coverage_basis 필수 |
| Canonical Partial Failure | Work Unit + Recovery Journal |
| Semantic Merge False PASS | 직접 해결하지 않음; post-merge invariant는 후속 Candidate 필요 |
| Stale Program Summary | evidence revision + stale summary proof 불인정 |
| Assumption Debt | lineage/critical status는 필요하나 debt ceiling 상세는 후속 |
| Security Boundary | 최소 model/secret/environment/no-prod-write guard |
| Test PASS + Business Regression | executed test evidence 요구; hidden consumer coverage는 Impact와 연계 |
| Metric Gaming | 직접 해결하지 않음 |

# 11. Remaining Gaps

Candidate B만으로 해결되지 않는 것:

- 실제 Legacy Intake Normalizer 구현
- 실제 MD↔Excel round-trip Converter
- 동일 PGM 병렬 semantic merge 전략
- runtime trace collector
- full Security RBAC/ACL/Retention implementation
- Metric Integrity Contract
- Assumption debt ceiling/expiry automation
- Production release/rollback/hotfix 전체 workflow

따라서 Candidate B를 Full Baseline으로 단독 승격하면 안 된다.
