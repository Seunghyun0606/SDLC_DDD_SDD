# Low-Agent Skill Procedure Contract v1

> 상태: `DECISION_REQUIRED`

좋은 Skill은 설명문이 아니라 **재현 가능한 Procedure**여야 한다. 표현 품질은 Agent 수준에 따라 달라도 되지만 ID, Required Field, Evidence, OPEN, Trace는 안정적이어야 한다.

## 1. 필수 Skill 구조

모든 Stage Skill은 최소 다음 순서를 가진다.

1. **Purpose** — 한 번의 실행에서 해결할 단일 목적
2. **Required Input** — 없으면 정상 실행할 수 없는 입력
3. **Optional Input** — 없더라도 OPEN으로 진행할 입력
4. **Precondition** — Stage 진입 전 deterministic check
5. **Retrieval Strategy** — 탐색 시작점과 우선순위
6. **Steps** — 번호가 있는 원자적 작업
7. **Decision Rules** — Agent가 선택해야 하는 분기와 기준
8. **Output Schema** — 자유형 문서 선택 금지
9. **Quality Check** — Output 저장 전 checklist
10. **Alert Conditions** — 진행은 가능하지만 확인이 필요한 상태
11. **Stop Conditions** — 언제 탐색/분석을 멈추는가
12. **Escalation Conditions** — 상위 Agent/Human으로 넘길 조건
13. **Do Not** — 추론/쓰기 금지사항
14. **Example** — 정상 1개 + OPEN/Escalation 1개

## 2. 공통 Decision Rule

### Truth

- 사람이 명시한 원문: `GIVEN`
- Source/DB/Log에서 직접 확인: `OBSERVED`
- 여러 근거를 결합한 판단: `INFERRED`
- 권한 있는 사람/공식 정책 확인: `CONFIRMED`
- 근거 부족: `OPEN`

`OBSERVED` 또는 `INFERRED`를 `CONFIRMED`로 자동 승격하지 않는다.

### Requirement Boundary

1. 원본 Requirement ID는 먼저 `source_requirement_id`로 보존한다.
2. 원본 행이 독립 Business Outcome인지 명확하지 않으면 Canonical RQ를 자동 확정하지 않는다.
3. 여러 원본 행이 같은 목적을 공유해도 CRUD 이름 유사성만으로 Merge하지 않는다.
4. Split/Merge가 downstream Scope/Test/Owner를 바꾸면 `BOUNDARY_AMBIGUOUS`로 Escalate한다.

### Source Target

1. Exact ID/Symbol direct relation을 우선한다.
2. Name similarity는 Candidate만 생성한다.
3. Write Target은 current revision과 직접 Evidence가 있어야 한다.
4. Top candidates가 유사하면 임의 선택하지 않는다.

## 3. 공통 Stop Rule

다음 중 하나면 현재 실행을 종료한다.

- Output Required Field가 값 또는 명시적 OPEN으로 모두 채워짐
- Direct/Configured Retrieval 범위를 모두 탐색함
- 다음 탐색이 새로운 Tool/권한을 요구함
- 다음 판단이 Business Decision을 요구함
- Context Budget을 넘기 전에 동일 Evidence가 반복됨

`모든 정보를 알 때까지 전체 Repository를 계속 읽는다`는 Stop Rule로 허용하지 않는다.

## 4. Fail-safe Escalation

다음 상태는 임의 완료하지 않는다.

- `UNKNOWN`
- `EVIDENCE_CONFLICT`
- `BOUNDARY_AMBIGUOUS`
- `AMBIGUOUS_TARGET`
- `MISSING_REQUIRED_SOURCE`
- `HIGH_BLAST_RADIUS`
- `SECURITY_CRITICAL`
- `CROSS_SYSTEM_TRANSACTION`

처리:

```text
현재까지 결과 저장
→ OPEN/Alert 기록
→ 필요한 Evidence 명시
→ L2/L3/Human 대상 지정
→ 다른 비차단 작업은 계속 가능
```

## 5. Deterministic Guard 우선

다음은 LLM reasoning에 맡기지 않는 것을 기본으로 한다.

- Required Field Check
- ID Format / Duplicate Check
- Revision Match
- RQ→FR Link
- FR→BR/AC Link
- PGM→ART/Source Link
- AC→TC Coverage
- OPEN Preservation
- Status Transition
- Source Hash Match

원칙:

> Mechanical Work → Schema / Rule / Validator
>
> Guided Analysis → L1/L2 Agent + Skill
>
> Complex Reasoning → L3 Agent
>
> Business Decision → Human

## 6. Stage Capability Routing

| Stage/작업 | 기본 등급 | 상향 조건 |
|---|---|---|
| Document Parsing / Template Fill | L1 | Parser conflict |
| Trace/CRUD/Data Dictionary | L1 | relation ambiguity |
| 6W Merge / FR draft | L1/L2 | contradictory sources |
| RQ Boundary | L2 | cross-domain split/merge → L3/Human |
| Source Discovery | L2 | dynamic/runtime-only path → L3 |
| Impact | L2 | high blast radius/cross-system → L3 |
| Design Draft | L2 | architecture decision → L3/Human |
| Source Change | L2 | security/transaction/ambiguous target → L3/Human |
| Test Generation | L1/L2 | unclear AC → upstream escalation |
| Verification | L2 | evidence conflict → L3/Human |
| Reverse Sync Classification | L2 | BUSINESS_RULE_CHANGE/UNKNOWN → Human review |

## 7. Quality Check 공통 질문

- 원본 ID가 사라지지 않았는가?
- 모든 중요한 값에 Truth/Evidence가 있는가?
- 모르는 항목을 OPEN으로 남겼는가?
- Source Behavior를 Business Rule로 확정하지 않았는가?
- 다음 Stage가 이전 대화 없이 이해할 수 있는가?
- 다음 Action과 Escalation 대상이 명확한가?
