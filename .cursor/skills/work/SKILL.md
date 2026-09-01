# /work

현재 Target(RQ/PGM/TASK)의 다음 실행 가능한 Stage를 선택하고 해당 Reference Contract를 수행한다.

## Routing

`INTAKE → DECOMPOSE → CLARIFY → PROCESS → DISCOVERY → IMPACT → DESIGN → PROGRAM → DEVELOPMENT → TEST → VERIFY → KNOWLEDGE PROMOTION`

## Rules

- Stage 전체를 승인 대기로 막지 않는다. 미확정은 Alert/Assumption으로 이월한다.
- Source가 연결된 경우 DISCOVERY 이후 결과에는 file/symbol/line-or-locator/source-hash 중 가능한 Evidence locator를 남긴다.
- Source write 전 Target confidence와 Execution Guard를 확인한다.
- Output은 Canonical relation을 갱신하고 해당 Template 기반 Artifact를 생성/갱신한다.

## References

- `references/requirement.md`
- `references/clarify.md`
- `references/process.md`
- `references/discovery.md`
- `references/impact.md`
- `references/design.md`
- `references/program.md`
- `references/development.md`
- `references/test.md`
- `references/verify.md`
