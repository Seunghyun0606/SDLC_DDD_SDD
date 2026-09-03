# Test Reference

## Purpose
AC→TC Coverage를 유지하고 기존 테스트 관례를 우선 재사용한다.

## Required Input
- Stage: `TEST`
- AC + PGM/TASK + Source/Test Convention

## Optional Input
- Existing tests / Runtime log / Regression scope

## Retrieval Strategy
1. AC direct relation
2. Existing test convention
3. Changed PGM/Source
4. Related regression consumer

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | AC, PGM/TASK, 변경 Source, 기존 Test convention, 실행 가능한 Test command를 확인한다. |
| 근거 분류 | 실제 Test 실행 결과는 OBSERVED, AC는 GIVEN/CONFIRMED, 예상 시나리오는 INFERRED로 구분한다. |
| 실행 순서 | AC 목록화 → 기존 Test 탐색 → TC 설계 → 우선순위/회귀 범위 지정 → 실행 → Evidence 기록 → 실패 원인 연결 순서로 수행한다. |
| 계속/중단 조건 | Test environment가 없어도 TC 설계는 계속한다. 실행 불가 상태는 NOT_EXECUTED로 기록하며 PASS로 간주하지 않는다. |
| 출력 필드 매핑 | AC↔TC relation, test path/symbol, precondition/input/expected, execution status, evidence, uncovered scope를 기록한다. |
| 품질 게이트 | 핵심 AC가 최소 하나의 TC와 연결되고, 실행됨/예상만 함이 분리되며, 실패가 Source/Design/Environment 중 어디와 연결되는지 표시되어야 한다. |
| 미확정/실패 처리 | 미수행은 NOT_EXECUTED, 환경 문제는 ENV_BLOCKED, 기능 실패는 FAILED, 회귀 사각지대는 COVERAGE_GAP으로 유지한다. |

## Steps
1. AC별 TC를 설계한다.
2. 기존 Test를 재사용/확장한다.
3. 실행 Evidence와 미수행 범위를 기록한다.
4. Failure를 Source/Design gap과 연결한다.

## Output
- TC + Test evidence
- Template: `sdlc/templates/core/test-scenario.md`

## Quality Check
- 모든 핵심 AC가 TC로 커버되는가
- 실제 실행 여부와 예상만 한 Test가 구분되는가

## Alert Conditions
- Test environment 없음
- Regression gap
- Compile/Test failure

## Token Strategy
Changed source와 직접 관련 Test부터 선택한다.

## Do Not
- 실행하지 않은 Test를 PASS로 기록하지 않는다.
- 미수행 Test 때문에 다른 분석 작업을 모두 막지 않는다.
