# Development Reference

## Purpose
허용 Scope만 수정하고 변경 파일/심볼/검증 명령/차이를 기록한다.

## Required Input
- Stage: `DEVELOPMENT`
- TASK + PGM Spec + Source + Standards

## Optional Input
- Existing tests / Build convention / Domain Overlay

## Retrieval Strategy
1. TASK/PGM direct relation
2. Relevant symbols
3. Applicable Standards
4. Nearby tests

## Steps
1. Target confidence와 Guard를 확인한다.
2. 필요한 Source만 수정한다.
3. Build/Static Check를 수행한다.
4. 실제 변경 Evidence와 설계 대비 차이를 기록한다.

## Output
- Source change + implementation result
- Template: `sdlc/templates/core/implementation-result.md`

## Quality Check
- 변경 범위가 TASK/PGM에 한정되는가
- 관련 AC/TC와 연결되는가

## Alert Conditions
- Ambiguous write
- Security/MUST violation
- Scope expansion
- Build failure

## Token Strategy
PGM Spec + relevant symbol + test + applicable standard만 사용한다.

## Do Not
- 관련 없는 Refactoring을 하지 않는다.
- 위험 Action을 Guard 없이 실행하지 않는다.
