# SDLC_DESIGN_SESSION_SECOND Branch Cleanup Status

- Date: 2026-09-02
- Active cumulative branch: `SDLC_DESIGN_SESSION_SECOND/p2/representative-brownfield-slice-v1`
- Main merge: **DENY / NOT PERFORMED**

## Decision Rules

- `MERGED_BY_ANCESTRY`: all commits are already reachable from the active P2 branch; do not start new work from this branch.
- `SUPERSEDED_CLOSED`: divergent alternative design; intentionally not merged because it overlaps/conflicts with the active cumulative runtime.
- `ACTIVE`: current continuation branch.

## Branch Status

| Branch | Status | Action |
|---|---|---|
| `SDLC_DESIGN_SESSION_SECOND/base` | MERGED_BY_ANCESTRY | Archived checkpoint; no new work |
| `SDLC_DESIGN_SESSION_SECOND/p0/usability-simplification-v1` | MERGED_BY_ANCESTRY | Archived checkpoint; no new work |
| `SDLC_DESIGN_SESSION_SECOND/p0.1/legacy-normalizer-v1` | MERGED_BY_ANCESTRY | Archived checkpoint; no new work |
| `SDLC_DESIGN_SESSION_SECOND/p0.2/review-publish-v1` | MERGED_BY_ANCESTRY | Archived checkpoint; no new work |
| `SDLC_DESIGN_SESSION_SECOND/p0.3/source-discovery-reverse-sync-v1` | MERGED_BY_ANCESTRY | Archived checkpoint; no new work |
| `SDLC_DESIGN_SESSION_SECOND/p0.4/test-verify-contract-v1` | MERGED_BY_ANCESTRY | Archived checkpoint; no new work |
| `SDLC_DESIGN_SESSION_SECOND/p0.5/e2e-orchestration-v1` | MERGED_BY_ANCESTRY | Archived checkpoint; no new work |
| `SDLC_DESIGN_SESSION_SECOND/p0.6/runtime-provider-boundary-v1` | MERGED_BY_ANCESTRY | Archived checkpoint; no new work |
| `SDLC_DESIGN_SESSION_SECOND/p0.7/provider-adapter-conformance-v1` | MERGED_BY_ANCESTRY | Archived checkpoint; no new work |
| `SDLC_DESIGN_SESSION_SECOND/p0.8/runtime-invocation-recovery-v1` | MERGED_BY_ANCESTRY | Archived checkpoint; no new work |
| `SDLC_DESIGN_SESSION_SECOND/p0.9/command-runtime-integration-v1` | MERGED_BY_ANCESTRY | Archived checkpoint; no new work |
| `SDLC_DESIGN_SESSION_SECOND/p0.final/design-baseline-exit-v1` | MERGED_BY_ANCESTRY | Archived checkpoint; no new work |
| `SDLC_DESIGN_SESSION_SECOND/p1/foundation-knowledge-bootstrap-v1` | MERGED_BY_ANCESTRY | Archived checkpoint; no new work |
| `SDLC_DESIGN_SESSION_SECOND/p0-p1/structural-redesign-v1` | MERGED_BY_ANCESTRY | Direct parent of P2; archived checkpoint |
| `SDLC_DESIGN_SESSION_SECOND/review/usability-simplification-red-team-v1` | MERGED_BY_ANCESTRY | Review findings already reachable from P2; archived |
| `SDLC_DESIGN_SESSION_SECOND/p0.redesign/runtime-core-v1` | SUPERSEDED_CLOSED | PR #54 closed without merge; preserve only as historical alternative |
| `SDLC_DESIGN_SESSION_SECOND/p2/representative-brownfield-slice-v1` | ACTIVE | All new SESSION_SECOND work continues here or on a child branch |

## Divergent Branch Decision

`p0.redesign/runtime-core-v1` has 60 commits that are not in P2. Those commits implement an alternate Runtime Core (`stage-procedures.yaml`, alternate stage routing/command runtime, source-write capability, status/handoff builders) that overlaps with the active Structural Redesign/P2 runtime. Blind merge would create duplicate authorities and conflicting execution contracts.

Therefore it is intentionally **not merged**. PR #54 records the superseded decision and is closed.

## Operational Rule

Agents and humans must not select `MERGED_BY_ANCESTRY` or `SUPERSEDED_CLOSED` branches as a base for new implementation. New work must branch from the active P2 branch and remain under `SDLC_DESIGN_SESSION_SECOND/`.

## Physical Branch Deletion

The connected GitHub tool currently exposes branch create/update but not branch-ref deletion. Therefore historical branch refs remain physically visible. Their lifecycle state is defined by this document and PR #54; no additional merge to `main` is permitted.
