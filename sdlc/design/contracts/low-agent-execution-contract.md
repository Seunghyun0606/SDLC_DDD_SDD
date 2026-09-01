# Low-Agent Execution Contract — P0

상태: `ACTIVE_P0_CANDIDATE`

## 목적

Stage 산출물 품질이 Agent의 암묵적 추론 능력에 과도하게 의존하지 않도록 모든 Stage Skill을 재현 가능한 Procedure로 실행한다.

## 모든 Stage Skill의 필수 구조

1. Purpose
2. Required Input
3. Optional Input
4. Precondition
5. Retrieval Strategy
6. Atomic Steps
7. Decision Rules
8. Output Schema
9. Quality Check
10. Alert Conditions
11. Stop Conditions
12. Escalation Conditions
13. Do Not
14. 정상 예제와 OPEN/Escalation 예제

필수 항목이 없는 Skill은 `LOW_AGENT_CONTRACT_INCOMPLETE`다.

## Truth 결정 규칙

- 사람이 명시적으로 제공: `GIVEN`
- Source, DB, Log에서 직접 관찰: `OBSERVED`
- 여러 근거를 결합한 판단: `INFERRED`
- 권한 있는 사람 또는 공식 정책으로 확인: `CONFIRMED`
- 근거 부족: `OPEN`

`OBSERVED`나 `INFERRED`를 자동으로 `CONFIRMED`로 승격하지 않는다.

## Requirement Boundary

- 원본 ID를 먼저 보존한다.
- `sdlc/config/rq-boundary.yaml`의 Decision만 사용한다.
- 독립 Business Outcome 근거가 없으면 `UNRESOLVED` 또는 Candidate로 유지한다.
- CRUD 이름 유사성만으로 Merge/Split하지 않는다.
- Boundary가 Scope, Owner, Release, AC를 바꾸면 Escalate한다.

## 공통 Stop Rule

다음 중 하나면 현재 Agent 실행을 종료하고 현재까지 결과를 저장한다.

- Required Output이 값 또는 명시적 OPEN으로 채워졌다.
- Configured Retrieval 범위를 모두 탐색했다.
- 다음 탐색이 새로운 권한, Tool, Runtime 접근을 요구한다.
- 다음 판단이 Business Decision을 요구한다.
- 동일 Evidence가 반복되어 추가 정보 이득이 없다.
- Context Budget을 넘기기 직전이다.

전체 Repository나 전체 문서를 무기한 읽는 것은 Stop Rule이 아니다.

## Escalation

다음은 임의 완료하지 않는다.

- EVIDENCE_CONFLICT
- BOUNDARY_AMBIGUOUS
- AMBIGUOUS_TARGET
- MISSING_REQUIRED_SOURCE
- HIGH_BLAST_RADIUS
- SECURITY_CRITICAL
- CROSS_SYSTEM_TRANSACTION
- BUSINESS_RULE_CHANGE_CANDIDATE
- UNKNOWN

처리 순서는 `현재 결과 저장 → OPEN/Alert → 필요한 Evidence 명시 → L2/L3/Human 대상 지정 → 비차단 작업 계속`이다.

## Deterministic Guard 우선

다음은 LLM reasoning보다 Schema/Validator를 우선한다.

- Required Field
- ID Format / Duplicate
- Revision 존재 여부
- Source Requirement ID 보존
- RQ→FR / FR→BR·AC / PGM→Source / AC→TC Reference
- OPEN Preservation
- Boundary Decision Cardinality
- Status Transition

## Agent Capability Routing

| 작업 | 기본 | 상향 조건 |
|---|---|---|
| 문서 Parsing / Template Fill | L1 | Parser/Evidence conflict |
| Trace / CRUD / Data Dictionary | L1 | Relation ambiguity |
| 6W / FR Draft | L1-L2 | Contradictory sources |
| RQ Boundary | L2 | Cross-domain → L3/Human |
| Source Discovery | L2 | Dynamic/runtime-only → L3 |
| Impact | L2 | High blast radius → L3 |
| Design Draft | L2 | Architecture decision → L3/Human |
| Source Change | L2 | Security/Tx/Ambiguous target → L3/Human |
| Test Generation | L1-L2 | AC unclear → upstream |
| Verification | L2 | Evidence conflict → L3/Human |
| Reverse Sync | L2 | Business rule/unknown → Human review |

## Stage Handoff 성공 조건

다음 Agent가 이전 Conversation History 없이 `Stage Input Pack + 현재 Artifact + Config`만으로 아래를 답할 수 있어야 한다.

1. 현재 Target은 무엇인가?
2. 원본 Requirement ID는 무엇인가?
3. 확정된 사실과 OPEN은 무엇인가?
4. 어떤 Evidence가 사용되었는가?
5. 무엇을 하면 안 되는가?
6. 다음 Action과 Escalation은 무엇인가?
