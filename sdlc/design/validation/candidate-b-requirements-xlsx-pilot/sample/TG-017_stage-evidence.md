# TG-017 Stage Evidence — Candidate B

> Subject Type: `LEGACY_TOPIC_GROUP`
> Canonical RQ: `NONE`
> Raw Items: 39
> 제목: `10분단위 근무계획 개선 근태마감 반영을 구현`

## INTAKE

```yaml
progress: COMPLETE
quality: WARNING
workflow_exit: OPEN
output: legacy_evidence_inventory
canonical_publish: REQUIRES_INTAKE_CONTRACT
source_write: DENY
```

## DECOMPOSE

```yaml
progress: COMPLETE
quality: WARNING
output: legacy_bucket_review
canonical_rq: null
canonical_fr: 0
canonical_publish: REQUIRES_INTAKE_CONTRACT
```

해석: B안만으로는 이 39행을 1 RQ인지 여러 RQ인지 결정하지 않는다.

## CLARIFY

생성되는 질문 예:

- 일/월/전사/강제/선택적 근로마감은 동일 State Machine인가?
- 마감 후 수정/재오픈 정책은?
- 전자결재 반려/취소/재요청 정책은?
- 강제마감 권한은?
- 어떤 흐름이 독립 배포 가능한가?

```yaml
progress: COMPLETE
quality: WARNING
next_stage_draft: ALLOW
business_truth_confirmation: DENY
```

## DISCOVERY

```yaml
progress: COMPLETE
quality: CRITICAL
missing_evidence:
  - source_repository
  - static_index
outputs:
  - discovery_query_plan
source_write: DENY
```

## DEVELOPMENT

```yaml
progress: COMPLETE
quality: CRITICAL
target_write_proof: FAIL
draft_source_write: DENY
merge_release: DENY
```

B1이 Option B라도 Source Target 자체가 없기 때문에 Draft Write를 허용하지 않는다.

## VERIFY

```yaml
progress: COMPLETE
quality: CRITICAL
verify_pass: DENY
reason:
  - no_canonical_requirement
  - no_implementation_result
  - no_executed_test
```

이것이 B2 Option A의 실제 모습이다. 내부 산출물 작성 progress와 안전한 실행/검증 권한은 별개다.
