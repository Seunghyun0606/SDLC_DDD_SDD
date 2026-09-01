---
document_type: rq_boundary_card
candidate_id: {{candidate_id}}
revision: {{revision}}
status: {{CANDIDATE|REVIEW_REQUIRED|PUBLISHED}}
legacy_source_ids: {{legacy_source_ids}}
---

# {{candidate_name}}

## 1. Business Goal — REQUIRED

- Value: {{business_goal}}
- Truth: {{GIVEN|OBSERVED|INFERRED|CONFIRMED|OPEN}}
- Evidence: {{evidence}}

## 2. Actor / Trigger — REQUIRED FOR PUBLISH

- Actor: {{actor}}
- Trigger: {{trigger}}
- Truth: {{truth}}

## 3. Observable Outcome — REQUIRED FOR PUBLISH

- Outcome: {{observable_outcome}}
- Truth: {{truth}}

## 4. Policy / State Scope — CONDITIONAL

- Policy scope: {{policy_scope}}
- States/Lifecycle: {{states}}
- Truth: {{truth}}

## 5. Acceptance / Release Scope — REQUIRED FOR PUBLISH

- Can be accepted independently: {{yes|no|open}}
- Can be released independently: {{yes|no|open}}
- Truth: {{truth}}

## Included Raw Items

| Legacy ID | 원문 요약 | Candidate FR | Trace |
|---|---|---|---|
| {{legacy_id}} | {{raw_summary}} | {{fr_candidate}} | {{trace}} |

## Split Signals

- [ ] Different Business Goal
- [ ] Independent Actor/Trigger
- [ ] Independent Observable Outcome
- [ ] Different Policy/Authority Scope
- [ ] Different Lifecycle/State Machine
- [ ] Independent Acceptance/Release

Technical-only signals:

- [ ] Different PGM
- [ ] Different Table
- [ ] API/Batch/Interface boundary

> Technical-only signal은 RQ Split의 단독 근거가 아니다.

## Agent Proposal

- Recommendation: {{KEEP|SPLIT_REVIEW_REQUIRED|MERGE_REVIEW_REQUIRED}}
- Reason: {{reason}}
- Proposed children: {{candidate_children}}

## Human Review

- Decision: {{KEEP|SPLIT|MERGE|DEFER}}
- Reviewer: {{optional}}
- Comment: {{comment}}
- Decision evidence: {{evidence}}

## Downstream Handoff

- Published RQ ID: {{rq_id_or_null}}
- Scope revision: {{revision}}
- OPEN items: {{open_items}}
- Next stage: {{next_stage}}
