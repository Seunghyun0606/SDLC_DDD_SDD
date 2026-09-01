# Verify Reference

## Purpose
Requirement→Source→Test evidence chain을 확인하고 미검증 항목을 명시한다.

## Required Input
- Stage: `VERIFY`
- RQ/FR/AC/TC + Source/Build/Test Evidence

## Optional Input
- Runtime evidence / Operations review / Knowledge candidates

## Retrieval Strategy
1. Canonical trace
2. Implementation result
3. Test result
4. Source hash/freshness

## 실행 계약(Agent Execution Contract)
| 항목 | 실행 규칙 |
|---|---|
| 입력 필드 | RQ/FR/PGM/TASK/AC/TC relation, 현재 Source hash, Build/Test Evidence를 확인한다. |
| 근거 분류 | 실제 Build/Test/Source 상태는 OBSERVED, 승인 Requirement/AC는 GIVEN/CONFIRMED, 미검증 연결은 INFERRED로 둔다. |
| 실행 순서 | Canonical chain 확인 → Source freshness 대조 → Build/Test evidence 대조 → 미검증/Deferred 식별 → Knowledge Candidate 추출 순서로 수행한다. |
| 계속/중단 조건 | 일부 검증이 없어도 결과 문서는 생성한다. Release/위험 실행만 Guard하며 미검증 항목은 숨기지 않는다. |
| 출력 필드 매핑 | 각 chain segment의 status/evidence, VERIFIED/UNVERIFIED/DEFERRED, stale source 여부, Knowledge Candidate를 기록한다. |
| 품질 게이트 | VERIFIED 항목은 실제 Evidence chain이 끊기지 않아야 하며 Source hash가 최신이어야 한다. |
| 미확정/실패 처리 | Source hash mismatch는 STALE, Test 미수행은 UNVERIFIED, 실패는 FAILED, 정책 충돌은 CONFLICT로 기록한다. |

## Steps
1. RQ→FR→PGM→ART/SYMBOL→TASK→AC→TC 관계를 확인한다.
2. Source/Build/Test Evidence를 대조한다.
3. Unverified/Deferred 항목을 명시한다.
4. 재사용 가능한 Knowledge Candidate를 추출한다.

## Output
- Verification Result + Knowledge candidates
- Template: `sdlc/templates/core/verification-result.md`

## Quality Check
- Evidence chain이 끊기지 않는가
- 미검증 항목이 숨겨지지 않았는가

## Alert Conditions
- Source freshness mismatch
- Test failure
- Confirmed truth conflict
- Release 위험

## Token Strategy
Canonical relation과 Verification evidence만 우선한다.

## Do Not
- Evidence 없는 항목을 VERIFIED로 표시하지 않는다.
- Release 위험 외 일반 Workflow 전체를 Hard Block하지 않는다.
