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
