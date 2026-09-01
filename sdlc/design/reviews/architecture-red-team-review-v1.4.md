# Architecture Red Team Review — Brownfield AI-SDLC Harness v1.4

> Review target: `brownfield_ai_sdlc_harness_full_design_v1_4.md`
> Review mode: Architecture Red Team
> Baseline rule: 기존 v1.4의 방어책을 새 제안처럼 반복하지 않고, 방어가 실패하는 조건과 Silent Semantic Failure를 우선한다.
> Branch: `review/architecture-red-team-v1.4`

---

# A. Red Team Verdict

## POC UNSAFE WITHOUT FIXES

1. v1.4의 방향성은 유지 가능하지만, **잘못된 의미가 COMPLETE/CURRENT/PASS 상태로 전파되는 Silent Failure**를 막는 계약이 부족하다.
2. 특히 `CRITICAL Alert + 계속 진행`, `MEDIUM 이상 Source Write`, Summary/Knowledge 재사용이 결합되면 잘못된 판단을 빠르고 일관되게 확산시킬 수 있다.
3. Canonical/Source/Test/Generated Doc/Hook을 하나의 실행 단위로 다루는 Transaction, Recovery Journal, Idempotency가 정의되지 않았다.
4. Brownfield의 Dynamic SQL, Trigger, DB polling, Reflection, 파일 배치 등 Static Analyzer blind spot에 대한 **Impact completeness 보강 전략**이 부족하다.
5. Security/Authorization/Environment/Release/Rollback 경계가 PoC 수준에서도 불충분하다.

**핵심 결론:** 이 Harness는 안전장치가 보강되면 개발자를 더 안전하고 빠르게 만들 수 있다. 현재 상태로 자동화를 넓히면 **잘못된 분석을 더 빠르고 일관되게 확산시키는 시스템**이 될 위험이 더 크다.

---

# B. Catastrophic Risks Top 10

| Rank | Risk | Probability | Impact | Detectability | Time-to-Detection | Blast Radius | Current Defense | Gap |
|---:|---|---|---|---|---|---|---|---|
| 1 | HIGH confidence의 Wrong Target Source 수정 | MEDIUM | CRITICAL | HARD | 테스트/운영 이후 | 다수 프로그램/데이터 | Resolver 우선순위, ambiguity 중단, MEDIUM 이상 Write | HIGH가 틀린 경우의 독립 검증이 없음. stale summary/static blind spot이 confidence를 오염 가능 |
| 2 | 잘못된 BR이 CONFIRMED 후 Knowledge로 Promotion | MEDIUM | CRITICAL | HARD | 다음 RQ 또는 정책 분기 발생 시 | 동일 Domain 전체 | Evidence check, duplicate/conflict, stale | 적용범위/유효기간/법인/국가/권한 context가 BR identity에 필수 아님 |
| 3 | Hidden dependency 누락으로 실제 영향 Program 미탐지 | HIGH | HIGH/CRITICAL | HARD | 통합/운영 배치 | 연계 시스템/급여/회계 | Static Analysis First + CHECK_REQUIRED | Trigger/Dynamic SQL/file/polling/reflection/runtime topology에 대한 completeness contract 부재 |
| 4 | Partial Failure로 Source와 Canonical 상태 불일치 | MEDIUM | CRITICAL | HARD | 다음 `/work`, merge, 문서 재생성 | RQ/Branch 전체 | Optimistic revision, branch delta | Work Unit transaction, journal, compensation, idempotency key 부재 |
| 5 | Semantic Merge는 성공했지만 merged Source 의미와 Canonical 불일치 | MEDIUM | CRITICAL | HARD | regression/운영 | 병렬 변경 영역 | Git+Semantic Merge, merge 후 incremental analysis | Source↔Canonical post-merge invariant 및 fail-safe verification 기준이 부족 |
| 6 | Stale Program Summary를 CURRENT로 재사용 | MEDIUM | HIGH | HARD | 잘못된 구현 후 | 동일 PGM 관련 후속 RQ | Source hash | hash 생성/갱신 실패 자체, indirect dependency freshness, generated summary provenance 검증 없음 |
| 7 | CRITICAL Assumption 누적 상태에서 코드가 정상 완료/병합 | HIGH | HIGH | MEDIUM/HARD | 정책 반대 확정 또는 운영 | 해당 RQ 및 재사용 Knowledge | Alert+Assumption, rejected 시 STALE | Assumption debt ceiling, contradiction check, merge/release eligibility 분리 없음 |
| 8 | Source/Schema/Prompt/실데이터가 외부 LLM/로그로 유출 | MEDIUM | CRITICAL | HARD | 보안감사/사고 후 | 회사/고객 전체 | Prompt 원문 미저장 원칙, 위험 DB 작업 block | trust zone, model allowlist, secret redaction, data classification, RBAC, retention 미정의 |
| 9 | Test PASS가 실제 Business/Batch regression을 숨김 | HIGH | CRITICAL | HARD | 운영 배치/월마감 | 급여/정산 등 후행 업무 | AC→TC, VERIFY_ONLY, trace | risk-based coverage, hidden consumer coverage, runtime contract, release verification 부재 |
| 10 | Metric Gaming으로 AI ROI/생산성 잘못 보고 | HIGH | HIGH | HARD | 분기/투자 의사결정 후 | 프로젝트/조직 투자 | Human effort 필요 명시, usage≠productivity | metric governance, denominator integrity, audit sample, baseline/control design 부족 |

---

# C. Silent Failure Top 10

| Rank | Silent Failure | 왜 즉시 보이지 않는가 | 대표 결과 |
|---:|---|---|---|
| 1 | Wrong Target이 HIGH confidence로 선택됨 | 컴파일과 단위 테스트가 통과할 수 있음 | 엉뚱한 서비스 변경, 실제 대상 미수정 |
| 2 | 실제 영향 Program 누락 | 변경 대상이 아니므로 테스트조차 안 함 | 야간 Batch/급여/정산 regression |
| 3 | Scope 없는 Knowledge Promotion | 문장 자체는 맞아 보임 | 특정 법인 Rule이 Global Rule로 재사용 |
| 4 | Stale Program Summary CURRENT 오인 | Context Pack은 일관돼 보임 | 오래된 책임/호출관계로 구현 |
| 5 | Partial Traceability | 문서 생성은 정상 | RQ→AC→TC 중 일부 링크만 끊김 |
| 6 | Semantic Merge false pass | Git conflict 없음 | 서로 다른 BR/transaction 의미가 한 main에 공존 |
| 7 | VERIFY_ONLY 오분류 | 수정 파일이 없으므로 안전해 보임 | 실제 수정 필요 프로그램 누락 |
| 8 | Assumption contradiction 누적 | 각 assumption은 개별적으로 plausible | 서로 양립 불가능한 설계가 동시에 존재 |
| 9 | 제한된 Test Coverage로 PASS | 수행된 TC만 보면 100% PASS | 미탐지 consumer/기간/권한 조합 실패 |
| 10 | Productivity Metric 왜곡 | 대시보드 숫자는 정상 | Task 쪼개기/공수 누락으로 ROI 과대평가 |

Silent Failure는 컴파일 오류보다 우선해서 다뤄야 한다. 특히 `CURRENT`, `COMPLETE`, `PASS`, `HIGH`가 실제 안전성을 보증하는 것처럼 보이는 순간 위험이 커진다.

---

# D. Architecture Attack by Area

## 1. Truth/Evidence Model — WEAK

### Attack Scenario 1 — 잘못된 GIVEN이 상위 Truth로 고착
**Attack Scenario**: 요구사항 담당자가 “월 마감 후 누구도 수정 불가”라고 입력했지만 실제로 HR 관리자 예외가 있다.

**Failure Mechanism**: `GIVEN`은 출처 분류일 뿐 신뢰도/권한/적용범위가 아니다. 이후 인터뷰가 없거나 같은 문구를 반복하면 잘못된 premise가 설계의 축이 된다.

**User-visible Symptom**: 정상 사용 가능한 관리자 예외가 제거된다.

**Root Cause**: provenance type과 authority/validity/scope를 동일 축처럼 취급.

**Detection Difficulty**: HARD.

**Impact**: HIGH.

**Current Design Defense**: Source만으로 BR 확정 금지, `CONFIRMED/OPEN`, conflicting confirmed truth hard block.

**Defense Gap**: 누가 확인할 권한이 있는지, 어느 법인/기간/role에 적용되는지, confirmation expiry가 없음.

**Recommended Countermeasure**: Truth에 `authority`, `scope`, `effective_from/to`, `jurisdiction`, `confirmed_at`, `review_by`, `supersedes`를 추가한다.

### Attack Scenario 2 — 운영자 A/B 상충
A는 “월 마감 후 수정 금지”, B는 “HR 관리자는 가능”이라고 말한다. 두 문장을 서로 다른 scope rule로 분해해야 하지만 Agent가 하나를 예외가 아닌 모순으로 처리하거나, 반대로 둘을 섞어 “관리자는 항상 가능”으로 추론할 수 있다.

### Attack Scenario 3 — 공식 문서가 Source보다 오래됨
정책 문서는 2024년, Source는 2026년 긴급패치가 반영되어 있다. 문서는 `CONFIRMED`, Source는 `OBSERVED`라면 오래된 문서가 우선할 위험이 있다. 반대의 경우 Source 버그를 정책으로 오해할 수 있다.

### Attack Scenario 4 — CONFIRMED의 시간부패
2026-01 정책을 확인한 BR이 2026-07 정책 변경 후에도 `CONFIRMED`로 남는다. CR이 Harness 밖에서 처리되면 freshness trigger가 없다.

### Attack Scenario 5 — Evidence Type 오분류
Agent가 운영 로그의 특정 예외처리를 `CONFIRMED`로 기록하거나 회의 메모를 공식 정책문서로 분류한다. 이후 Knowledge Promotion pipeline이 잘못된 evidence를 정상 통과한다.

### Business Truth Poisoning Scenario 최소 5개
1. 잘못된 GIVEN + 확인자 권한 부재.
2. 서로 다른 운영조직의 상충 답변을 Global BR 하나로 축약.
3. 특정 법인/국가 Rule을 scope 없이 Promotion.
4. 과거 정책의 CONFIRMED 상태가 만료되지 않음.
5. 장애 우회코드를 Business Rule로 잘못 분류 후 사람의 피상적 확인으로 Promotion.
6. “현재 이렇게 운영한다”와 “정책상 이렇게 해야 한다”를 같은 Truth로 합침.
7. 임시 Hotfix 운영절차가 K1로 승격되어 영구 정책처럼 재사용.

**판정**: 모델의 축은 타당하지만 `Truth Type ≠ Truth Authority ≠ Scope ≠ Freshness` 분리가 필요하다.

---

## 2. Canonical Model — FAIL

### Attack Scenario — Multi-file Partial Update
**Attack Scenario**: Source 수정 성공 → Canonical entity 수정 성공 → relation 갱신 중 process crash → Generated MD는 이전 상태.

**Failure Mechanism**: 각 Registry/파일의 성공 여부가 분리되어 있고 commit marker가 없다.

**User-visible Symptom**: `/check`는 DONE을 보이지만 traceability에는 이전 PGM이 남는다.

**Root Cause**: Canonical이 논리적 SoT이지만 물리적 transaction boundary가 없음.

**Detection Difficulty**: HARD.

**Impact**: CRITICAL.

**Current Design Defense**: UID, optimistic revision, branch delta, validator.

**Defense Gap**: atomic write-set, write-ahead/recovery journal, commit/abort marker, idempotency가 없음.

**Recommended Countermeasure**: `Work Execution Unit`을 정의하고 `PREPARED → APPLIED → VERIFIED → COMMITTED/ABORTED` journal을 둔다.

### Canonical Corruption / Drift Scenarios
- 동일 사실이 BR/PROC/PGM Summary/Generated MD에 중복 표현되고 일부만 갱신.
- Relation row가 누락되었지만 entity와 MD가 정상 생성되어 orphan을 숨김.
- Canonical은 최신이나 `source_commit`이 이전 commit을 가리킴.
- Branch materialized view가 main update를 반영하지 않아 오래된 관계로 Source 수정.
- Process crash로 entity만 생성되고 relation/ID index는 미생성.
- 순환 relation이 traversal을 폭증시키거나 STALE propagation infinite loop를 유발.
- 삭제 entity를 가리키는 dangling relation이 남음.
- 동일 PGM에 두 RQ가 서로 다른 responsibility/summary를 기록.
- Derived state가 recalculation 전에 읽혀 `CURRENT` false positive 발생.

### 필수 Canonical Invariant
- 모든 relation endpoint 존재.
- published display ID uniqueness.
- source-bound entity는 `source_revision` 또는 `evidence_revision` 보유.
- generated artifact는 canonical revision을 기록.
- `CURRENT`는 dependency freshness 검증을 통과해야 함.
- branch delta는 base revision과 merge target revision을 모두 기록.

---

## 3. Workflow Router — WEAK

### Wrong Workflow Routing Scenario 1 — Ready Task 복수
`/work RQ-0012`에 Ready Task가 3개이고 모두 같은 priority인 경우, Source write는 중단하지만 분석/문서 stage는 임의로 하나를 진행하여 사용자 의도와 다른 작업의 state가 바뀔 수 있다.

### Scenario 2 — Active Context 잔존
Branch가 변경되었는데 context invalidation hook이 실패한다. 사용자의 “계속해줘”가 이전 branch의 TASK를 가리킨다.

### Scenario 3 — Explicit 자연어와 stale context 충돌
사용자가 “급여 쪽 계속”이라고 했지만 명시 ID가 없고 Active Context가 근태 TASK다. Resolver 우선순위 때문에 이전 task가 선택될 수 있다.

### Scenario 4 — COMPLETE + STALE
이전 Stage의 artifact는 `COMPLETE/STale`인데 Router가 progress만 보고 다음 Stage를 계속한다.

### Scenario 5 — Wrong Stage Completion
Impact stage가 candidate output 존재만으로 COMPLETE. 실제 critical consumer가 누락되어도 PROGRAM/DEVELOPMENT로 진행한다.

### Scenario 6 — Context loss 후 재실행
`/work` 재실행 시 이전 run의 side effect가 기록되지 않아 같은 source patch를 두 번 적용.

### Scenario 7 — 자동판단 과잉
사용자는 문서 갱신만 의도했지만 router가 다음 DEVELOPMENT stage까지 자동 진행하는 구현이 생기면 autonomy가 의도손실로 변한다.

**Current Defense**: explicit ID 우선, branch 변경 시 context 무효화, 여러 Development Task 자동 선택 금지.

**Gap**: router의 read-only action과 mutating action 경계, stale prerequisite policy, run resume token이 없다.

**Countermeasure**: `/work` 결과를 `READ/ANALYZE/DRAFT/MUTATE/VERIFY/PROMOTE` action class로 나누고, mutation은 current run intent와 대상 fingerprint를 기록한다.

---

## 4. Target Resolver — FAIL

### Worst Case — HIGH confidence Wrong Target Source Modification
**Attack Scenario**: `AttendanceService`가 두 모듈에 존재. stale Program Summary, exact-name bias, static graph 누락 때문에 구버전 모듈이 HIGH score를 받는다.

**Failure Mechanism**: confidence가 같은 evidence family에서 만들어지면 여러 signal이 있어도 독립성이 없다. 예: exact name, program summary, canonical relation 모두 같은 오래된 indexing 결과에 의존.

**User-visible Symptom**: Agent가 자신 있게 잘못된 파일을 수정하고 단위 테스트도 통과.

**Root Cause**: confidence score와 evidence independence를 구분하지 않음.

**Detection Difficulty**: HARD.

**Impact**: CRITICAL.

**Current Design Defense**: explicit target 우선, top1/top2 유사하면 write 중단, MEDIUM 이상만 write, scope expansion.

**Defense Gap**: HIGH confidence false positive, source revision freshness, runtime evidence, write target invariant 부족.

**Recommended Countermeasure**:
- Source write 전 `Target Write Proof` 생성.
- 최소 2개의 독립 evidence family 중 하나는 current source evidence여야 함.
- explicit TASK↔PGM↔ART relation + current revision 검증.
- Dynamic/reflective 영역은 HIGH 상한을 금지하거나 `UNVERIFIED_DYNAMIC` flag.
- wrong-target metric은 correction뿐 아니라 post-edit file ownership 검증으로 측정.

**중요**: 사용자 Workflow 자체를 강제로 막을 필요는 없다. 분석/설계/patch draft는 계속할 수 있고, 불충분한 proof의 변경은 `UNVERIFIED_WRITE`로 표시하여 merge/release 단계에서 명시적 human override가 필요하도록 한다.

---

## 5. Alert/Assumption — FAIL

### Alert Fatigue
- WARNING이 20~50개 누적되면 개발자는 severity를 읽지 않고 `/work`를 반복한다.
- 동일 원인에서 파생된 alert가 여러 artifact에 중복 발생하면 숫자만 증가한다.
- CRITICAL도 진행 가능하므로 시간이 지나면 실제 위험과 informational warning의 행동 차이가 사라진다.

### Assumption Debt
- 서로 상충하는 ASM이 다른 stage에서 각각 사용될 수 있다.
- rejected assumption이 downstream 전체를 STALE로 만들면 과도한 폭발, 너무 좁게 추적하면 누락.
- assumption 기반 source가 merge된 후 rejection되면 rollback 대상과 knowledge contamination을 정확히 찾기 어렵다.

**Current Defense**: severity, related alert, rejected→STALE.

**Gap**: debt budget, contradiction graph, assumption lineage depth, dedup, expiry, resolution SLA, merge/release eligibility가 없음.

**Countermeasure**:
- `Assumption Set`별 contradiction validator.
- RQ별 `critical_open_count`, `assumption_depth`, `assumption_age`를 표시.
- alert 원인 dedup 및 parent/child aggregation.
- 진행은 허용하되 `CRITICAL unresolved`가 사용된 source는 release eligibility를 별도 표시.

---

## 6. Static Analysis — FAIL

| Brownfield Scenario | Miss Probability | Impact | Detection Mechanism | Fallback Strategy |
|---|---|---|---|---|
| 1. Call Graph에 실제 영향 PGM 미연결 | MEDIUM/HIGH | HIGH | changed table/procedure reverse index, runtime trace sample | adjacent domain search + operator checklist |
| 2. Table Trigger 숨은 영향 | HIGH if trigger index 없음 | CRITICAL | DB metadata trigger inventory, DDL parse | 변경 table의 trigger/trigger-called objects 강제 후보화 |
| 3. Procedure Dynamic SQL | HIGH | HIGH/CRITICAL | PL/SQL string construction heuristic, SQL trace | dynamic SQL 발견 시 confidence cap + runtime verification |
| 4. Batch file 교환 | HIGH | HIGH | file path/config/scheduler manifest scan | batch/interface registry + ops interview |
| 5. DB Table polling interface | HIGH | HIGH | table consumer inventory, scheduler/job scan | READ consumer reverse lookup + runtime DB activity evidence |
| 6. Reflection/DI/Configuration | MEDIUM/HIGH | HIGH | framework/config parser, bean/name resolution | unresolved dynamic edge marker + full-text search/runtime trace |
| 7. Business 영향 있으나 technical dependency 없음 | VERY HIGH | HIGH | business process/knowledge relation | mandatory business impact review independent of call graph |
| 8. 공통 Procedure 수백 consumer | LOW miss / HIGH noise | HIGH | reverse dependency fan-out | risk-tier sampling, consumer classification, release regression suite |

**핵심 공격**: Static Analyzer가 찾지 못한 edge는 confidence 계산에도 존재하지 않는다. “HIGH confidence”는 실제로는 “관찰된 graph 안에서 HIGH”일 뿐 complete하지 않다.

**필수 보완**: Impact 결과에 `coverage_basis`, `blind_spots`, `unresolved_dynamic_edges`, `runtime_evidence_used`를 포함한다.

---

## 7. Impact Analysis — FAIL

### 주요 실패
- Technical relation이 있어도 Business impact는 없는 단순 consumer를 MODIFY로 과대선정.
- technical edge는 없지만 동일 월마감 정책을 공유하는 다른 process가 실제 business impact를 가짐.
- 실제 수정 프로그램을 VERIFY_ONLY로 분류하면 해당 code patch 자체가 생성되지 않음.
- 공통 procedure fan-out 수백 건에서 candidate overload로 alert fatigue 발생.
- candidate reduction을 과도하게 최적화하면 Recall 희생을 숨길 수 있음.

### 기존 Metric 공격
`Impact Recall`, `Impact Precision`, `Candidate-to-Actual Ratio`만으로는 부족하다.

추가 필요:
- `Critical Impact Recall`: 고위험 영향 누락률을 별도 측정.
- `Hidden Dependency Discovery Rate`.
- `Wrong MODIFY Rate` / `Wrong VERIFY_ONLY Rate`.
- `Impact Correction After Development`.
- `Coverage Evidence Mix`: static/runtime/human/business evidence 비율.
- `Miss Severity Weighted Score`.

---

## 8. Program Model — WEAK

### Logical Program Classification Drift
- 하나의 Java Service가 10개 업무를 처리하면 사람마다 PGM 경계가 달라진다.
- 한 Procedure가 여러 PGM responsibility를 수행하면 1:N relation이 필요하며 “ownership”과 “usage”를 구분해야 한다.
- Shared Utility를 PGM으로 분류하면 business ownership이 오염되고, 제외하면 impact fan-out을 놓칠 수 있다.
- PGM ID는 immutable이어도 responsibility는 시간에 따라 이동한다. ID 의미의 domain code가 현재 책임과 불일치할 수 있다.
- summary가 책임 이동을 반영하지 못하면 target resolver가 오래된 domain bias를 가진다.

**Countermeasure**: `PGM classification version`, `responsibility effective period`, `primary_domain/current_domain`, `role = OWNER/SHARED/CONSUMER`를 분리한다. Display ID의 domain code는 역사적 label일 수 있음을 명시한다.

---

## 9. Context Pack — FAIL

### Context Underfitting
변경 method만 제공했지만 class-level interceptor/transaction annotation, XML namespace, package-local convention이 빠져 잘못 구현.

### Summary Error Amplification
잘못된 Program Summary가 RQ-A, RQ-B, RQ-C에서 반복 재사용되어 오류가 confidence signal로 누적.

### Token Optimization Bias
Budget overflow에서 low-confidence candidate를 제거하는 정책은 바로 hidden dependency recall을 낮출 수 있다.

### Stale Summary
Source hash 갱신 pipeline이 실패하거나 generated source/dependency가 바뀌어도 primary file hash만 같으면 stale를 놓친다.

### Cross-program Rule Loss
직접 PGM만 읽어 global 월마감/권한/감사 규칙 누락.

### Historical Context Loss
과거 장애가 K3에만 남아 retrieval 우선순위가 낮아 regression 재발.

### Full Source를 안 읽는 것이 위험한 경우
- Transaction/annotation/AOP가 class/file scope에 존재.
- overload/inner class/generic dispatch가 symbol snippet 밖에서 결정.
- PL/SQL package state, trigger, dynamic SQL.
- Mapper resultMap/include/sql fragment가 분산.
- JSP include/taglib/global JavaScript side effect.
- security/auth check가 공통 wrapper에 있음.
- change risk가 HIGH/CRITICAL 또는 wrong-target cost가 큰 경우.

### Context Escalation Policy 필요 — YES
Risk와 uncertainty에 따라 `Snippet → Symbol Neighborhood → Full File → Related Files → Runtime/History`로 escalates 해야 한다. Token Budget은 hard cap이 아니라 soft optimization이어야 한다.

---

## 10. Knowledge — FAIL

### Knowledge Poisoning
잘못된 BR이 K1이면 다음 RQ의 설계 질문 자체가 줄어들어 오류가 “재사용 효과”로 측정될 수 있다.

### Stale Knowledge
Harness 외부 정책 변경을 감지하지 못하면 CR가 없으므로 business freshness가 영구 CURRENT.

### Duplicate Knowledge
의미가 유사하나 scope가 다른 rule을 duplicate로 합치면 정보손실, 반대로 같은 rule을 표현 차이로 여러 개 만들면 conflict noise.

### Contradictory Knowledge
조직 A/B가 실제로 다른 rule을 쓰는데 conflict entity로만 만들면 필요한 scope 분해가 되지 않는다.

### Scope-dependent Rule
법인/국가/조직/권한별 조건이 key에 없으면 Global Rule contamination.

### Temporal Rule
`effective_from/to`가 없으면 과거와 현재 정책이 모두 CURRENT처럼 retrieval.

### Promotion Bias
Agent가 reusable로 보이는 내용을 과도하게 promotion해 지식량과 contradiction 증가.

### Historical Misuse
K3 historical evidence가 current architecture 근거처럼 prompt에 재등장.

**Current Defense**: K1/K2/K3, evidence, duplicate/conflict, source hash, business CR/interview/policy freshness, stale 재확인.

**Defense Gap**: scope/temporal/authority, expiry, promotion blast-radius review, retrieval-time applicability predicate.

**Required fix**:
- Knowledge key에 scope/effective period.
- `applicability` predicate 없는 K1은 global로 취급하지 않음.
- high blast-radius K1 promotion은 two-source evidence 또는 human confirmation.
- K3는 generation context에서 기본 비활성, regression investigation에 우선 사용.

---

## 11. Standards — WEAK

### Standard Drift / Deviation Abuse
- artifact type 오분류 → 잘못된 standard injection.
- 조직 MUST와 프로젝트 MUST 충돌 시 resolver가 silent precedence 선택.
- legacy deviation이 누적되면 사실상 SHOULD가 됨.
- 개발자가 매번 deviation을 생성해 표준 회피.
- MUST 자체가 outdated여도 validator가 “준수”만 검사.
- code style pass지만 architecture responsibility가 잘못될 수 있음.
- local pattern이 anti-pattern인데 “기존 architecture 우선” 원칙이 강화할 수 있음.

**Countermeasure**: precedence contract, standard effective version, deviation owner/expiry/reason/risk, deviation rate metric, architecture responsibility check를 별도 운영.

---

## 12. Git/Semantic Merge — FAIL

| Scenario | Git Detection | Canonical Detection | Auto Resolution | User Decision | Rollback Strategy |
|---|---|---|---|---|---|
| A. 두 Branch가 같은 BR을 다르게 수정 | 파일 위치에 따라 conflict 가능/없음 | Human Scalar conflict 가능 | NO | YES | 한 branch delta revert + dependent artifacts stale |
| B. 같은 PGM 다른 Source, 의미상 충돌 | 보통 없음 | PGM/transaction/BR relation diff로 일부 가능 | 제한적 | 보통 YES | merge commit revert + regenerated artifacts |
| C. Git conflict 없음, Process 의미 충돌 | NO | process/BR semantic diff가 있어야 탐지 | NO | YES | semantic merge abort 또는 revert |
| D. Canonical merge 성공, Source 결과 불일치 | NO | 현재 설계만으로 false pass 가능 | NO | YES if invariant fail | source+canonical paired rollback |
| E. Generated Doc 재생성 중 Human Section 소실 | NO 또는 diff로 사후 발견 | 보통 NO | NO | YES | generation backup/section checksum restore |
| F. Merge 후 새 dependency 발견 | NO | incremental analysis로 가능 | candidate 추가만 가능 | risk에 따라 | merge revert 또는 follow-up task |
| G. 오래된 Branch | 일부 conflict | base_revision 차이 탐지 | 단순 field만 | 고위험은 YES | rebase/refresh delta 후 재검증 |
| H. Knowledge candidate 충돌 promotion | NO | KCF 생성 가능 | NO | YES | promotion rollback/version supersede |

**핵심 Gap**: Merge 후 `Source ↔ Canonical ↔ Test ↔ Knowledge` 일관성을 하나의 검증 결과로 묶는 contract가 없다.

---

## 13. PM/Task — WEAK

### 공격
- Program 기준 task가 너무 세분화되면 PM overhead와 metric gaming 증가.
- 하나의 transaction change가 여러 PGM에 걸치면 1 Task≈1 PGM가 오히려 원자적 책임을 깨뜨림.
- 긴급 장애/hotfix에서 RQ 작성이 먼저면 대응이 늦다.
- 개발 중 impact가 발견되면 새 Task Candidate가 계속 늘어 일정이 흔들림.
- assignee 변경이 잦으면 branch/context ownership과 실제 담당 불일치.
- 동일 PGM 병렬 작업의 policy가 미결정.
- 하나의 test task가 여러 RQ를 검증하는 N:M이 필요.

### Production 변경은 반드시 기존 RQ/TASK 연결 정책
원칙은 필요하지만 **사전 연결 강제는 긴급 운영에서 비현실적**이다.

권장: `INCIDENT/HOTFIX temporary work item`을 자동 발급하여 즉시 작업을 허용하고, 사후 RQ/CR linkage를 SLA 내 보강한다. Production DB 위험행위/배포는 별도 release control을 유지한다.

---

## 14. Metrics — FAIL

### Goodhart's Law
| Metric | Gaming | 위험 |
|---|---|---|
| Verified Task / MD | task를 작게 쪼갬 | 생산성 과대평가 |
| First Pass Success | 쉬운 작업만 AI, TC 최소화 | 품질 과대평가 |
| Rework Rate | rework를 신규 task로 등록 | 재작업 은폐 |
| Token / Verified Task | session 분할/외부 context 누락 | 비용 과소평가 |
| AI Cost / Verified Task | 고비용 model usage 누락 | ROI 과대평가 |
| Cycle Time | 대기시간 제외/작업 시작 늦게 기록 | 시간 단축 과대평가 |
| Knowledge Reuse Rate | 불필요 knowledge를 강제 include | reuse 성과 과대평가 |

### 경영진 오보고 가능성 — HIGH
AI 사용군이 쉬운 작업에 편향되고 human review/cleanup 공수가 빠지면 “AI가 30% 생산성 향상” 같은 결론이 쉽게 생성된다.

**필수**: workload complexity bucket, assisted/unassisted baseline, sampled human audit, rework lineage, denominator freeze, metric definition versioning.

---

## 15. Design Continuity — WEAK

### False PASS Continuity Validation
- capability ID는 남았지만 실제 behavior semantics가 달라짐.
- decision ACTIVE지만 code path가 우회.
- contract가 presence만 검사하고 semantic invariant는 검사하지 않음.
- contract가 너무 엄격해 안전한 migration을 regression으로 오인.
- registry update 누락 자체를 자동으로 알기 어려움.
- agent가 capability와 implementation mapping을 동시에 잘못 수정하면 validator가 self-consistent false pass.
- old baseline schema migration이 부분 적용되어도 현재 schema validator만 통과.

**Countermeasure**: golden scenario tests, behavior contract, baseline diff approval, migration replay test, independent immutable test fixture가 필요하다.

---

## 16. Security — FAIL

현재 Privacy section은 telemetry 원문 저장 최소화에 집중되어 있다. Enterprise 적용에는 다음이 부족하다.

- Prompt/Context data classification 및 outbound policy.
- 외부 model/provider allowlist와 closed-network mode.
- secret/API key scanner/redaction before context pack.
- RBAC: 누가 어느 RQ/Source/Knowledge/Generated Doc을 볼 수 있는지.
- 운영 DB read/query capability의 credential/role/sandbox.
- 실제 개인정보가 포함된 test data의 masking/synthetic policy.
- hook/log retention, deletion, audit access.
- tenant/project isolation.
- dev/test/prod environment separation.
- generated document ACL.

**PoC 전 최소**: `NO_PROD_WRITE`, `NO_SECRET_EXPORT`, `DATA_CLASSIFICATION`, `MODEL_ENDPOINT_POLICY`, `LOG_RETENTION`, `PROJECT_ISOLATION` contract.

---

## 17. Recovery — FAIL

| Failure | 현재 위험 | 필요한 Recovery Flow |
|---|---|---|
| LLM API 실패 | run state 불명확 | run journal에 last safe step 기록, resume |
| Static Analyzer 실패 | partial graph를 정상 graph로 오인 | analysis snapshot status=FAILED/PARTIAL, 이전 verified snapshot fallback |
| Context Pack 실패 | stale pack 재사용 | pack revision invalidation, rebuild idempotently |
| Source Edit 중단 | half patch/dirty workspace | pre-edit fingerprint, patch journal, git restore/patch retry |
| Test 실패 | source/canonical update가 이미 진행 가능 | uncommitted work unit 유지, DONE 금지, repair task |
| Canonical Update 실패 | source와 SoT divergence | compensation 또는 retry with idempotency key |
| Knowledge Promotion 실패 | VERIFY 완료와 knowledge 상태 분리 | promotion queue retry, no duplicate entity |
| Merge 실패 | branch delta 일부 반영 위험 | merge prepare/commit separation |
| Document Generation 실패 | canonical은 최신, view stale | regenerate queue, doc validity=STALE |
| Hook Collector 실패 | metric 누락 | local append replay, sequence/idempotency key |

### `/work` 재실행 멱등성
현재 설계만으로는 동일 source patch, entity 생성, alert 생성, knowledge candidate가 중복될 수 있다.

필수 key 예:
`execution_id + action_type + target_uid + base_revision + intent_hash`

Scripts 중 최소 멱등 필요:
`update_canonical`, `propagate_change`, `promote_knowledge`, `merge_canonical`, `regenerate_artifacts`, `generate_docs`, `sync_excel`, hook flush.

---

# E. Failure Chain — RQ-0042

## Chain 1 — Conflicting Interview → Global Knowledge Poisoning

```text
운영자 A: 월 마감 후 수정 금지
→ 운영자 B: HR 관리자는 가능
→ Agent가 B를 예외 scope로 모델링하지 않고 한 문장으로 축약
→ BR-ATT-0013을 “HR 관리자는 마감 후 가능”으로 CONFIRMED
→ Functional Design에 global 예외 반영
→ PGM-ATT-0016 수정
→ 일반 사용자/다른 법인 role matrix TC 누락
→ Test PASS
→ BR-ATT-0013 K1 Promotion
→ 다음 RQ가 질문 없이 BR 재사용
→ 여러 법인/권한으로 오염 확산
```

가장 위험한 점은 첫 RQ가 정상 PASS로 보이고, 재사용이 “Knowledge Reuse 성공” metric으로 집계될 수 있다는 것이다.

## Chain 2 — Static Blind Spot → Payroll Regression

```text
Static Analyzer가 PayrollBatch dependency 미탐지
→ PGM-PAY-0021을 VERIFY_ONLY로 유지
→ Impact Recall이 실제 ground truth 없이 높게 계산
→ 미마감 취소 + 근태 재계산 transaction 변경
→ Attendance summary timing/shape 변경
→ unit/integration TC는 휴가/근태만 PASS
→ merge 후 야간 PayrollBatch가 이전 state assumption으로 계산
→ 급여 regression
→ verification-result.md는 PASS 상태
→ 장애 시점까지 Silent Failure
```

## Chain 3 — Concurrent Branch + Stale Summary + False Semantic Merge

```text
Branch A: RQ-0042 AttendanceService transaction 수정
→ Branch B: 동일 Service의 다른 source에서 월마감 처리 변경
→ Branch A의 Program Summary hash 갱신 실패
→ A agent가 stale summary로 patch 생성
→ Git conflict 없음
→ Canonical은 relation list set-union으로 merge 성공
→ 두 branch의 의미상 transaction ordering 충돌 미탐지
→ Generated Docs 재생성 성공
→ limited TC PASS
→ Knowledge Promotion
→ main의 Canonical/Docs는 “CURRENT”지만 runtime semantics는 모순
```

---

# F. Architecture Gaps

## Gap 1 — Work Unit Transaction / Recovery Journal
**Why existing design does not cover it**: optimistic revision은 동시수정 탐지이지 다중 side effect atomicity/recovery가 아니다.

**Required before PoC?** YES

**Minimal fix**: execution journal + prepare/apply/verify/commit 상태 + compensation metadata.

**Long-term fix**: durable event/outbox 또는 transactional metadata store.

## Gap 2 — Idempotent Resume Contract
**Why**: `/work` 재실행과 script retry의 중복 side effect 방지 규칙이 없다.

**Required before PoC?** YES

**Minimal fix**: idempotency key와 source/canonical fingerprint.

**Long-term fix**: workflow engine 수준 durable execution.

## Gap 3 — Truth Applicability / Temporal Model
**Why**: GIVEN/OBSERVED/INFERRED/CONFIRMED은 provenance만 표현한다.

**Required before PoC?** YES

**Minimal fix**: authority, scope, effective period, confirmation timestamp.

**Long-term fix**: policy applicability engine + jurisdiction hierarchy.

## Gap 4 — Target Write Proof
**Why**: confidence score가 잘못된 HIGH를 방지하지 못함.

**Required before PoC?** YES

**Minimal fix**: 독립 evidence 2개 + current source revision + TASK↔PGM↔ART invariant.

**Long-term fix**: runtime evidence and learned resolver calibration.

## Gap 5 — Risk-based Context Escalation
**Why**: token soft budget/overflow는 축소는 정의하지만 위험에 따른 확대 기준이 없다.

**Required before PoC?** YES

**Minimal fix**: HIGH risk/dynamic/transaction/security change는 full-file/related-file escalation.

**Long-term fix**: outcome-calibrated adaptive context planner.

## Gap 6 — Impact Completeness / Blind-spot Registry
**Why**: trace graph의 알려지지 않은 영역을 result에 명시하지 않는다.

**Required before PoC?** YES

**Minimal fix**: trigger/dynamic SQL/batch file/polling/reflection blind-spot checklist와 coverage basis.

**Long-term fix**: runtime trace + DB metadata + scheduler/config integration.

## Gap 7 — Security Trust Boundary
**Why**: telemetry privacy 원칙은 있으나 data/model/secret/authorization boundary가 없음.

**Required before PoC?** YES

**Minimal fix**: data classification, endpoint allowlist, redaction, RBAC, no-prod-write.

**Long-term fix**: enterprise policy enforcement gateway and audit store.

## Gap 8 — Release / Rollback / Hotfix / Incident Workflow
**Why**: Delivery와 Merge 이후 Production lifecycle이 비어 있다.

**Required before PoC?** NO for offline code-only PoC; YES before user pilot touching real release process.

**Minimal fix**: temporary HOTFIX task, release eligibility, rollback link.

**Long-term fix**: deployment integration, feature flag, incident feedback loop.

## Gap 9 — Schema Evolution + Migration Replay
**Why**: DCON-008은 migration 누락을 말하지만 실제 migration transaction/replay/rollback contract는 없음.

**Required before PoC?** YES if canonical schema changes during PoC.

**Minimal fix**: schema version + forward migration + fixture replay test.

**Long-term fix**: backward compatibility windows and automated migration verifier.

## Gap 10 — Environment / Project Isolation
**Why**: multi-project/DEV/TEST/PROD state가 canonical/knowledge/runtime key에 필수로 정의되지 않음.

**Required before PoC?** YES for shared repository or real enterprise data.

**Minimal fix**: project_id/environment mandatory partition key.

**Long-term fix**: tenant-isolated metadata/service architecture.

---

# G. Overengineering

| 대상 | 분류 | Red Team 판단 |
|---|---|---|
| Canonical Entity 전체 | PILOT LATER | RQ/FR/BR/PGM/TASK/AC/TC/ALT/ASM 최소 core만 먼저. 모든 entity를 한 번에 구현하지 않음 |
| Capability Registry | PILOT LATER | 최소 manifest/critical capability만. 4인 Pilot에서 full registry maintenance는 부담 |
| Decision Registry | NEEDED NOW | 위험한 선택과 continuity를 남기는 최소 registry는 필요 |
| Branch Delta | PILOT LATER | 단일 vertical slice 이후 concurrency spike에서 검증 |
| Semantic Merge | PILOT LATER | 핵심 장기기능이지만 첫 coding blocker로 만들지 않음 |
| Knowledge Promotion | NEEDED NOW | Harness 핵심 가설이므로 RQ-A→RQ-B 검증에 필수 |
| Knowledge Conflict | NEEDED NOW | poisoning 방지용 최소 conflict/scope 처리 필수 |
| Standards Resolver | PILOT LATER | 초기에는 명시 standard mapping으로 충분 |
| Token Budget | PILOT LATER | 먼저 quality baseline 측정, 이후 비용 최적화 |
| PM Scheduling | PILOT LATER | Optional tracking은 필요하지만 first vertical slice blocker 아님 |
| Hook Metrics | NEEDED NOW | Pilot 평가/kill criteria를 위해 최소 telemetry 필수 |
| Operations Knowledge View | PILOT LATER | 운영 usability 평가 시 도입 |

`REMOVE` 판정은 없다. 장기적으로 가치가 있으나 Pilot sequence를 조정해야 하는 항목이 대부분이다.

---

# H. Required Fixes Before Coding

| Priority | Fix | 최소 완료 조건 |
|---|---|---|
| P0 | Work Unit Transaction + Recovery Journal | Source/Canonical/Test/Doc 상태를 하나의 execution journal로 추적 |
| P0 | Idempotent `/work` Resume | 동일 intent 재실행 시 duplicate patch/entity/alert 없음 |
| P0 | Truth Scope/Temporal/Authority | K1/BR에 적용범위와 유효기간 없는 Global Promotion 금지 |
| P0 | Target Write Proof | mutating action 전 independent evidence + current revision 검증 |
| P0 | Security Trust Boundary | secret redaction, endpoint policy, no-prod-write, project isolation |
| P1 | Risk-based Context Escalation | HIGH risk는 budget보다 completeness 우선 |
| P1 | Static/Impact Blind-spot Registry | 8개 brownfield blind spot을 result에 명시/보강 |
| P1 | Canonical Invariant Validator | orphan/dangling/revision/generated-doc consistency 검사 |
| P1 | Assumption Debt/Contradiction | duplicate/contradiction/expiry/lineage 관리 |
| P2 | Metric Integrity Contract | complexity bucket, rework lineage, human effort audit |

---

# I. Required Fixes Before Pilot

1. **Quick Start + 역할별 Guide**: 비숙련 설계/개발자가 `/work /change /check`만으로 시작할 수 있고, 각 문서 상단에 목적/다음 행동/시각화 workflow가 있어야 한다.
2. **Legacy/New Project Bootstrap Profile**: 기존 Source/guide/static analyzer를 읽어 repository profile과 standard mapping을 추천하여 customizing을 최소화한다.
3. **Non-blocking UX 명문화**: 분석/설계/patch draft는 계속 진행 가능. 위험 상태는 Alert/Override로 남기되 production release/unsafe action만 hard block.
4. **직관적 파일명/Index**: 전체 작업 목록을 한눈에 보는 `work-items.md` 또는 canonical generated view를 제공하고 RQ/설계/개발/Test 상태를 연결한다.
5. **MD↔Excel 양방향 변환 Contract**: 사용자 컬럼은 한글명, stable internal key는 숨김/보조 컬럼으로 유지. round-trip loss test 필요.
6. **PM Optional Tracking**: assignee/schedule 미입력도 허용하되 입력 시 RQ→WP→Task breakdown 조회 가능.
7. **Administrator Customizing Layer**: stage, template, standard, folder, artifact 사용 여부를 config로 조절하고 code fork를 최소화.
8. **Hotfix/Incident Flow**: RQ 선등록 없이 임시 HOTFIX work item으로 시작하고 사후 linkage 가능.
9. **Pilot Evaluation Corpus**: 동일 domain 2건이 아니라 normal/hidden-dependency/conflicting-rule/failure case를 포함.
10. **Human Factors Test**: PM/설계자/개발자/운영자 각각 task completion time과 질문수/override율을 측정.

### Adoption Failure Scenario 최소 5개
1. PM이 Canonical entity 용어를 이해해야만 status를 볼 수 있어 기존 Excel로 회귀.
2. 설계자가 Agent 초안 review가 직접 작성보다 오래 걸려 `/work`를 우회.
3. 개발자가 stale PGM spec을 한 번 경험한 뒤 Harness confidence를 전반적으로 불신.
4. 운영자가 질문/Knowledge 정리 부담 때문에 인터뷰를 회피하여 assumption만 증가.
5. 장애 시 Harness route가 느려 Source/DB 직접 확인이 빨라져 incident에서 사용 중단.
6. Alert가 너무 많아 사용자가 severity와 관계없이 모두 dismiss.
7. PM 도구와 Harness 일정이 이중관리되어 한쪽이 stale.

---

# J. Decision Required

## DECISION_REQUIRED 1 — CRITICAL Business Uncertainty 상태의 Source Write

**Question**: CRITICAL unresolved business assumption을 사용한 상태에서 Source patch를 어디까지 허용할 것인가?

### Option A — Source Write 자체를 차단
**Pros**: semantic risk 최소화.

**Cons**: 사용자가 요구한 non-blocking 업무 진행 원칙과 충돌. Brownfield 인터뷰 지연 시 개발이 정지.

### Option B — Branch/Draft Write 허용, Merge/Release eligibility 제한
**Pros**: 업무 진행은 유지하면서 잘못된 변경의 main/production 확산을 막음.

**Cons**: draft code rework가 생길 수 있고 override UX가 필요.

**Red Team Recommendation**: **Option B**.

**Why final choice still belongs to user**: 조직의 승인문화, release authority, 긴급성에 따라 허용 가능한 semantic risk가 다르다.

---

## DECISION_REQUIRED 2 — 동일 PGM 병렬수정

**Question**: 같은 Logical Program에 대한 두 Task의 병렬 Source modification을 허용할 것인가?

### Option A — Serial ownership
**Pros**: merge/semantic conflict 감소.

**Cons**: 병렬 개발성과 긴급 hotfix 대응성 저하.

### Option B — Optimistic concurrency + semantic merge
**Pros**: 병렬성 유지.

**Cons**: false-pass semantic merge 위험, 구현 복잡도 증가.

**Red Team Recommendation**: Pilot은 **Option A를 기본**, 예외적으로 B를 허용해 concurrency spike를 별도 측정.

**Why final choice still belongs to user**: 실제 팀 규모와 변경 빈도에 따라 비용구조가 달라진다.

---

## DECISION_REQUIRED 3 — K1 High-blast Knowledge Promotion 승인 수준

**Question**: 법인/국가/월마감/권한 같은 고영향 Business Rule을 자동 Promotion할 것인가?

### Option A — Evidence 조건 충족 시 자동
**Pros**: automation/reuse 극대화.

**Cons**: poison blast radius 큼.

### Option B — Candidate 자동 생성 + 사람이 scope/temporal 확인 후 K1
**Pros**: poisoning 감소.

**Cons**: review overhead.

**Red Team Recommendation**: Pilot은 **Option B**, low-blast technical K2는 자동화 범위를 넓힌다.

**Why final choice still belongs to user**: Knowledge review 책임을 누가 질 수 있는지가 조직마다 다르다.

---

## DECISION_REQUIRED 4 — PM Task SoT

**Question**: Harness와 Jira/기존 관리도구 중 일정/담당의 최종 SoT를 어디에 둘 것인가?

### Option A — Harness SoT
**Pros**: traceability 단순.

**Cons**: 조직 PM 도구와 중복.

### Option B — External PM Tool SoT + Harness cached view
**Pros**: 기존 운영 정합성.

**Cons**: connector/동기화 failure 처리 필요.

**Red Team Recommendation**: 실제 Pilot 조직에 기존 PM 도구가 있으면 **Option B**.

**Why final choice still belongs to user**: 프로젝트별 PM governance가 다르다.

---

# K. Kill Criteria

다음은 단순 metric warning이 아니라 Harness 아이디어를 중단하거나 범위를 크게 줄여야 하는 기준이다.

| Kill Criterion | 제안 Threshold | 조치 |
|---|---:|---|
| Wrong Target Source Modification | **HIGH confidence 자동수정 오판 1건이라도 main/release까지 통과** | auto-write 중단, resolver를 advisory-only로 축소 |
| Critical Impact Recall | **< 95%** 또는 CRITICAL consumer miss 1건 | static-first 자동 impact 확정 중단, human/runtime review 강화 |
| Overall Impact Recall | **< 90%** 반복 | candidate strategy 재설계 |
| Knowledge Poisoning | 잘못된 K1이 다음 RQ에 재사용되어 rework 발생 1건 | K1 auto-promotion 중단 |
| Knowledge Reuse 효과 | reuse group rework가 no-reuse보다 **15% 이상 증가** | reuse 범위 축소/quality gate 재설계 |
| Human Review Cost | 학습기간 후에도 기존 수작업 대비 **20% 이상 증가** | 문서/Canonical scope 대폭 축소 |
| Target Correction Rate | **>10%**, 또는 HIGH false-positive **>2%** | semantic auto-resolution 축소 |
| Token Economy | quality 동일 조건에서 token 절감 **<20%** | token budget/summary subsystem 우선순위 낮춤 |
| Assumption Debt | RQ 종료 시 unresolved CRITICAL assumption **>0**가 release에 반복 통과 | release eligibility 모델 재설계 |
| Verification False PASS | pilot ground truth failure 중 PASS 판정 **>5%** 또는 production-grade regression 1건 | verify automation을 advisory로 강등 |
| Metric Integrity | audit sample 오차 **>10%** | ROI/생산성 대외보고 중단 |
| Voluntary Adoption | 4주 후 eligible task의 자발적 사용 **<50%** | UX/산출물/프로세스 scope 축소 |

### PoC Evaluation 개선
- RQ 2건만으로 Knowledge 효과 검증은 부족하다.
- 최소 6~10개 case: simple, cross-program, hidden dependency, conflicting interview, dynamic SQL/trigger, concurrency, failed/rework case 포함.
- Ground Truth Impact는 senior developer + operator + runtime/static evidence로 사전에 blind adjudication.
- AI assisted vs manual/standard-tool baseline을 complexity bucket으로 비교.
- 실패한 RQ도 corpus에 포함.
- Human audit 필수 metric: actual impact, wrong target, rework lineage, human review effort, business-rule correctness.

---

# L. Final Recommendation

## RUN ARCHITECTURE SPIKE FIRST

현재 v1.4를 폐기할 필요는 없다. 그러나 바로 Full Vertical Slice coding으로 가기 전에 아래 4개 Spike를 먼저 통과시켜야 한다.

1. **Execution Safety Spike** — transaction/recovery/idempotency와 `/work` 재실행.
2. **Semantic Safety Spike** — conflicting Truth + scope/temporal Knowledge + assumption debt.
3. **Target/Impact Spike** — wrong HIGH target, dynamic/hidden dependency, risk-based context escalation.
4. **Security/Operational Spike** — trust boundary, hotfix/release/rollback, environment isolation.

이 Spike가 통과되면 `FIX AND START VERTICAL SLICE`로 전환한다.

최종 질문에 대한 답은 다음과 같다.

> **현재 v1.4 그대로라면 “잘못된 분석을 더 빠르고 일관되게 확산시키는 시스템”이 될 위험이 더 크다.**
>
> 다만 위험의 중심은 Canonical/Knowledge/JIT/`/work`라는 방향 자체가 아니라, **semantic uncertainty와 partial failure를 정상 상태처럼 보이게 만드는 계약 부재**다. 위 P0/P1 보완을 먼저 하면 Harness는 개발자를 더 안전하고 빠르게 만드는 쪽으로 전환 가능하다.

---

# Appendix A. Review-to-Design Continuity Notes

이번 Review는 새 Architecture baseline을 선언하지 않는다. v1.4의 기존 ACTIVE decision/capability는 유지한다.

다음 항목은 기존 결정을 대체하는 것이 아니라 보완이 필요한 후보다.

- Alert-driven Workflow → `ENHANCED`: 진행 가능성과 release eligibility 분리.
- Target Resolver → `ENHANCED`: confidence + independent write proof.
- Knowledge Promotion → `ENHANCED`: scope/temporal/authority/applicability.
- Context Pack → `ENHANCED`: risk-based escalation.
- Semantic Merge → `ENHANCED`: post-merge source/canonical/test invariant.
- Canonical Optimistic Revision → `ENHANCED`: work-unit transaction/recovery/idempotency.
- Hook Metrics → `ENHANCED`: integrity/audit/Goodhart controls.

새 Baseline을 만들 때는 v1.4 전체를 상속한 **Current Full Design** 형태로 작성하고 continuity validator 대상으로 삼아야 한다.

# Appendix B. User Experience Acceptance Constraints

후속 Full Design은 다음을 acceptance constraint로 취급한다.

1. Agent 비숙련 설계/개발 인력도 전체 구조를 따라갈 수 있어야 한다.
2. Brownfield/Greenfield 모두 적용하고 기존 Source/Guide를 이용해 bootstrap customizing을 줄인다.
3. 업무 진행을 일반적으로 hard block하지 않으며 나중에 변경/보정 가능해야 한다. 단 unsafe production/release 행위는 별도 안전 경계로 둔다.
4. 파일명만으로 내용이 직관적이어야 한다.
5. 전체 작업 목록 파일이 있어야 하며 Excel과 양방향 변환 가능해야 한다.
6. MD↔Excel 사용자 컬럼명은 한글로 직관적이어야 한다.
7. PM은 요구/설계/개발을 breakdown해 볼 수 있고 담당/일정은 optional tracking 가능해야 한다.
8. Harness 관리자가 프로젝트별 불필요 기능 제거/추가/수정을 config 중심으로 쉽게 할 수 있어야 한다.
9. SDLC 구조, Skill, Template, 단계별 작업 가이드는 구조화된 문서로 제공하고 각 단락 workflow 시각화와 문서 상단 Quick Start를 포함해야 한다.
