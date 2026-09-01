# Skill — Runtime Provider Orchestration

## Purpose

현재 Stage/Command가 요구하는 Capability를 Provider Registry와 매칭하고 실행 가능한 Provider Runtime Plan을 만든다. Provider 결과나 Business Truth는 생성하지 않는다.

## Required Input
- Project Context (`mode`, `stage`)
- Command (`/work`, `/change`, `/check`)
- Target Work Unit
- Required Capability 목록
- Provider Registry

## Optional Input
- Human Action 목록
- Write Intent
- Expected Revision
- Permission Proof
- Idempotency Key
- Adapter-specific `extensions`

## Precondition
- Provider Registry가 Contract Validation을 통과해야 한다.
- Write는 권한/Revision/Idempotency 조건이 충족되어야 한다.

## Retrieval Strategy
1. Command Router capability exact match
2. Stage가 요청한 capability exact match
3. enabled provider만 후보
4. Write면 READ_WRITE provider만 후보
5. 동일 우선순위 다중 후보는 AMBIGUOUS로 중단

## Atomic Steps
1. Command를 `command.route.*` capability로 변환
2. Caller/Stage가 선언한 required capability를 합친다.
3. Registry에서 exact capability provider를 찾는다.
4. Missing/Ambiguous capability를 OPEN으로 기록한다.
5. Human Action이 있으면 별도 보존한다.
6. Write Guard를 검사한다.
7. `PROVIDER_RUNTIME_PLAN`을 생성한다.
8. 모든 capability가 해소되고 Human Action이 없을 때만 `READY`로 표시한다.

## Decision Rules
- Provider 이름/기술스택으로 capability를 추측하지 않는다.
- Greenfield 초기 단계에서 Existing Source가 없다는 이유만으로 차단하지 않는다.
- Brownfield Source Evidence 필요 Stage는 Source capability 없으면 BLOCKED/OPEN이다.
- Provider Response 없이 실행 성공을 만들지 않는다.
- Core Contract에 업무도메인 필드를 추가하지 않는다. 구현체 고유값은 `extensions`를 사용한다.

## Output Schema
`sdlc/templates/provider-runtime-plan.yaml`

## Quality Check
- 요청 capability가 모두 exact match 되었는가?
- Provider Type/Mode가 capability와 맞는가?
- Missing/Ambiguous provider가 숨겨지지 않았는가?
- Write Guard가 충족됐는가?
- Human Action을 Provider가 대체하지 않았는가?

## Alert Conditions
- MISSING_CAPABILITY
- AMBIGUOUS_PROVIDER
- PROVIDER_UNAVAILABLE
- WRITE_PERMISSION_OPEN
- SOURCE_REVISION_UNKNOWN
- HUMAN_ACTION_REQUIRED

## Stop Conditions
- 모든 Provider가 결정되어 Plan이 READY
- 필요한 Capability가 없어 ACTION_REQUIRED
- Human Decision이 필요해 ACTION_REQUIRED
- Write Guard가 미충족되어 INVALID/BLOCKED

## Escalation Conditions
- Provider 구현/연결 필요 → Engineering Owner
- Business Decision → L2/Human
- Runtime 복합 장애 → L3
- Security/permission boundary → L3_OR_HUMAN

## Do Not
- 특정 업무 샘플을 Core Routing Rule로 하드코딩
- Java/MyBatis/Oracle 등 특정 Stack을 Provider Type으로 사용
- Provider 미지원 기능을 fallback 추측 실행
- Read Capability를 Write Capability로 간주
- Test Provider 결과 없이 PASS 생성
- Canonical Provider 없이 ID 생성

## Examples

Greenfield DESIGN:
`/work + requested_capabilities=[]` → Command Router만 해소되면 READY. Existing Source Provider는 요구하지 않는다.

Brownfield DISCOVERY:
`/work + source.snapshot.read + source.search` → Source Provider exact capability 필요.

미지원 Release 도구:
`deployment.release.execute` capability가 Registry에 없으면 `ACTION_REQUIRED / MISSING_CAPABILITY`. 특정 CI/CD 제품을 자동 추정하지 않는다.
