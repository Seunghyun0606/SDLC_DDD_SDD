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

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | TASK, PGM Spec, 실제 Target Symbol, 적용 Standard, 관련 Test/Build 명령을 확인한다. |
| 근거 분류 | 실제 Source/Build/Test 결과는 OBSERVED, 승인된 설계는 CONFIRMED/GIVEN, 구현 선택은 INFERRED로 구분한다. |
| 실행 순서 | Target/Scope 확인 → Guard/Confidence 확인 → 최소 Source 변경 → Build/Static Check → 관련 Test → 변경 Evidence/설계 차이 기록 순서로 수행한다. |
| 계속/중단 조건 | 문서 미확정은 PARTIAL로 계속할 수 있으나 Target ambiguity, 위험 Action, DoR Guard 조건은 해당 Source write를 중단한다. |
| 출력 필드 매핑 | changed file/symbol, before/after hash, TASK/PGM, build/test evidence, design deviation, alert를 Implementation Result에 기록한다. |
| 품질 게이트 | 변경 파일이 TASK/PGM Scope에 포함되고, 실제 변경 hash가 기록되며, 실행하지 않은 검증을 PASS로 쓰지 않아야 한다. |
| 미확정/실패 처리 | Build/Test 실패는 FAILURE Evidence, 예상 밖 변경은 SCOPE_ALERT, 설계와 Source가 달라진 경우 reverse drift 대상으로 표시한다. |

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
