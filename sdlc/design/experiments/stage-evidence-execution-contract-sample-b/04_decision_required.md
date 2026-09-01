# 04. DECISION_REQUIRED

> 상태: `OPEN`
> 원칙: 아래 선택은 Candidate B에서 임의 확정하지 않는다. Red Team Recommendation은 안전성 관점의 권고이며 최종 선택은 사용자에게 있다.

# DECISION_REQUIRED 1 — CRITICAL Business Uncertainty 상태의 실제 Source Write

## Question

CRITICAL unresolved business assumption을 사용한 상태에서 short-lived Branch의 실제 Source 파일 변경을 허용할 것인가?

## Option A — 실제 Source Write 차단, Patch Proposal만 허용

### Pros

- 잘못된 업무가 코드에 들어갈 가능성 최소화
- Work Unit/Recovery 범위 단순
- Review 시 Source가 변경되지 않아 의미 혼동이 적음

### Cons

- 인터뷰가 늦으면 개발 준비 속도가 떨어짐
- Patch Proposal을 다시 실제 patch로 적용하는 재작업 발생
- Non-blocking 원칙의 체감 효과가 낮아질 수 있음

## Option B — Short-lived Branch Draft Write 허용, Merge/Release Eligibility 제한

### Pros

- 분석과 개발 병렬화 가능
- 실제 코드 형태로 빠르게 검증 가능
- Red Team의 기존 권고와 일치

### Cons

- 잘못된 가정 기반 코드가 Branch에 존재
- rework/rollback lineage 필요
- Git commit이 존재한다는 이유로 사용자가 완료로 오해할 수 있음

## Red Team Recommendation

**Option B**, 단 다음 조건을 전제로 한다.

- Work Unit journal 필수
- `assumption_lineage` 필수
- Merge/Release eligibility는 DENY
- 사용자 View에 `가정 기반 Draft` 표시

## Why final choice still belongs to user

조직의 Branch 보호정책, Code Review 문화, 개발 병렬화 요구와 규제 수준에 따라 허용 가능한 semantic risk가 다르다.

---

# DECISION_REQUIRED 2 — Stage `COMPLETE` 의미

## Question

Evidence가 부족해 actual action이 DENY인 Stage에서도 `progress=COMPLETE`를 사용할 것인가?

## Option A — COMPLETE는 산출물 작성 완료만 의미, action permission 별도

### Pros

- 기존 v1.5.1 Progress/Quality/Validity 모델과 호환
- migration 비용 낮음
- 문서 작성 완료와 검증 가능 상태를 분리할 수 있음

### Cons

- 사용자/Agent가 COMPLETE를 안전성으로 오해할 수 있음
- Dashboard가 progress만 읽으면 Silent False Complete 재발

## Option B — COMPLETE를 Evidence 기준으로 강화하고 Draft 완료는 별도 상태 사용

예: `DRAFT_COMPLETE`, `EVIDENCE_COMPLETE`.

### Pros

- 의미가 더 명확함
- Dashboard/Automation의 잘못된 COMPLETE 해석 감소

### Cons

- 기존 상태계약 변경 폭이 큼
- 모든 Stage/PM View/Metric migration 필요
- 상태 수 증가로 비숙련 UX가 복잡해질 수 있음

## Red Team Recommendation

Pilot은 **Option A + 강제 Contract**를 권고한다.

- `progress`만으로 Stage 안전성 판단 금지
- 모든 mutating/verification action은 `action_permissions` 필수 조회
- 사용자 View의 `완료` 표시는 VERIFY-grade 의미일 때만 사용하고 내부 progress는 숨긴다.

## Why final choice still belongs to user

현재 구현체가 progress 필드를 얼마나 광범위하게 사용하는지에 따라 migration 비용과 Silent Failure 위험의 균형이 달라진다.

---

# DECISION_REQUIRED 3 — 동일 PGM 병렬 수정

## Question

같은 Logical Program에 대한 두 Task의 실제 Source Write를 병렬 허용할 것인가?

## Option A — Serial Ownership

### Pros

- Work Unit target revision 충돌 감소
- Semantic merge false pass 위험 감소
- Pilot의 원인분석이 쉬움

### Cons

- 병렬성 저하
- Hotfix/긴급 대응과 충돌 가능

## Option B — Optimistic Concurrency + Post-merge Invariant

### Pros

- 병렬 개발 유지
- 장기 Enterprise 사용 패턴과 가까움

### Cons

- semantic conflict 검증 구현 필요
- Work Unit recovery와 Merge recovery가 결합돼 복잡도 증가

## Red Team Recommendation

Pilot은 **Option A 기본**, 별도 Spike Branch에서 Option B를 검증한다.

## Why final choice still belongs to user

팀 규모, 동일 PGM 변경 빈도, 긴급 Hotfix 비율에 따라 병렬성의 가치가 다르다.

---

# DECISION_REQUIRED 4 — High-blast K1 Promotion

## Question

법인/국가/권한/월마감처럼 Blast Radius가 큰 Business Rule의 K1 Promotion을 자동화할 것인가?

## Option A — Evidence Contract 충족 시 자동 Promotion

### Pros

- Knowledge Reuse 최대화
- Human Review 부담 감소

### Cons

- scope 분류 오류 시 poisoning blast radius 큼
- 겉으로는 evidence가 충족돼도 authority 해석 오류 가능

## Option B — Candidate 자동 생성 + Human Scope/Temporal 확인 후 K1

### Pros

- Knowledge poisoning 감소
- 적용범위와 유효기간을 사람이 명시적으로 확인

### Cons

- 운영/업무 담당 Review 필요
- Knowledge Promotion 속도 저하

## Red Team Recommendation

Pilot은 **Option B**.

## Why final choice still belongs to user

업무 Knowledge에 대한 공식 확인권한과 책임자가 프로젝트마다 다르다.

---

# DECISION_REQUIRED 5 — PM Task SoT

## Question

담당자/일정/공수의 최종 SoT를 Harness가 가질지 기존 PM 도구가 가질지 선택해야 한다.

## Option A — Harness SoT

### Pros

- RQ→FR→PGM→TASK Trace 단순
- Work Unit과 PM 상태 직접 연결

### Cons

- Jira/사내 PM 도구와 이중관리 위험

## Option B — External PM Tool SoT + Harness Cached View

### Pros

- 기존 조직 Governance 유지
- PM 사용자 도입 저항 감소

### Cons

- Connector/Sync/Conflict/Offline failure 설계 필요

## Red Team Recommendation

기존 PM 도구가 있는 Pilot이면 **Option B**.

## Why final choice still belongs to user

이 선택은 Harness Architecture보다 조직의 PM Governance와 기존 시스템 투자에 더 크게 좌우된다.

---

# DECISION_REQUIRED 6 — Recovery Journal 저장소

## Question

Work Unit Recovery Journal을 Pilot부터 중앙 Durable Store로 둘 것인가?

## Option A — Project-local Journal(JSONL/SQLite 등) + Git Ignore

### Pros

- PoC 구현이 빠름
- 외부 인프라 의존 최소
- branch/workspace 단위 복구 검증에 충분

### Cons

- multi-user/multi-runner recovery 어려움
- local loss 가능
- 중앙 감사/검색 제한

## Option B — Central Durable Metadata Store

### Pros

- multi-user/runner 복구와 감사에 유리
- transactional outbox/event 모델로 발전 가능

### Cons

- Pilot 인프라 복잡도 증가
- tenant/security/availability 설계가 즉시 필요

## Red Team Recommendation

Offline/단일-runner PoC는 **Option A**, 실제 multi-user Pilot 전에 Option B 재평가.

## Why final choice still belongs to user

Pilot 실행환경과 중앙 인프라 사용 가능 여부가 현재 자료에 정의되어 있지 않다.
