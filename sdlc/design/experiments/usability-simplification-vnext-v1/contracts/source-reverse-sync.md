# Source → Documentation Reverse Sync Contract v1

> 상태: `DECISION_REQUIRED`

## 목적

개발/Hotfix/Procedure 변경 이후 Source가 문서보다 앞서 변경되더라도 관련 PGM/FR/BR/AC/Design의 현재성을 안전하게 재평가한다.

## 기본 흐름

```text
Source Diff
→ Changed File / Symbol / SQL / Table / Procedure
→ ART / PGM / DATA relation resolve
→ Semantic Change Classification
→ Related FR / BR / AC / Design Candidate
→ STALE Candidate
→ Human/L2 Review
→ Document/Canonical Revision
→ Re-Verify
```

## 1. 입력

Required:
- base revision/commit
- changed revision/commit
- changed files
- current ART/PGM/DATA relation

Optional:
- executed test evidence
- runtime trace
- change request / incident / hotfix reason
- developer implementation result

## 2. Mechanical Detection

Agent reasoning 없이 우선 처리할 수 있는 항목:

- file added/modified/deleted
- changed symbol/method/function
- mapper statement change
- SQL table/column CRUD change
- procedure/package change
- interface endpoint/schema change
- source hash/revision mismatch

결과는 `OBSERVED`다.

## 3. Semantic Change Classification

각 changed unit은 다음 중 하나다.

### NO_BUSINESS_CHANGE

예:
- formatting
- comment
- variable rename with verified equivalent behavior
- generated metadata only

기본 처리:
- technical knowledge hash 갱신
- FR/BR/AC 전체 STALE 금지

### TECHNICAL_CHANGE

예:
- 동일 behavior를 유지하는 framework/config/refactoring
- index/logging/telemetry 변경

기본 처리:
- PGM/ART technical document candidate update
- 관련 regression test 선택
- Business artifact STALE은 자동 생성하지 않음

### BEHAVIOR_CHANGE

예:
- validation 조건 변경
- response/result/state transition 변경
- transaction/error handling이 외부 관찰 결과를 변경

기본 처리:
- Functional Design / AC 영향 Candidate
- 관련 FR/TC review

### BUSINESS_RULE_CHANGE

예:
- 업무 허용/금지 조건 변경
- 마감 기준/권한/계산 규칙 변경

기본 처리:
- BR / Process / Customer View STALE Candidate
- Human confirmation 필요
- Source observation만으로 BR를 CONFIRMED하지 않음

### UNKNOWN

의미 변화 판정 근거 부족.

기본 처리:
- 임의 분류 금지
- Evidence 요구사항 기록
- L2/L3/Human Escalation

## 4. Candidate Propagation

```text
Changed ART
→ PGM
→ Direct FR/FTR
→ Direct BR/AC/PROC
→ TC
```

원칙:

1. Direct relation부터 탐색한다.
2. 모든 transitive relation을 무조건 STALE 처리하지 않는다.
3. `NO_BUSINESS_CHANGE`는 business graph blast를 차단한다.
4. `TECHNICAL_CHANGE`는 PGM/ART/Test 중심으로 제한한다.
5. `BEHAVIOR_CHANGE`부터 FR/AC/Design을 candidate로 올린다.
6. `BUSINESS_RULE_CHANGE`는 Customer/BR/Process를 Human review한다.
7. `UNKNOWN`은 Candidate를 넓힐 수 있으나 자동 확정하지 않는다.

## 5. Procedure/DB Case

DB Procedure가 별도 변경된 경우:

1. changed package/procedure 확인
2. caller Mapper/Service/Batch/Interface 역참조
3. READ/WRITE Table 및 Code 영향 확인
4. PGM relation resolve
5. input/output/state/validation 변화 비교
6. semantic class 부여 또는 UNKNOWN
7. 관련 AC/TC 선택

Procedure relation이 없으면 `MISSING_TRACE_RELATION` Alert를 만든다.

## 6. 구현 중 신규 Validation 발견

Source에서 새 Validation을 발견한 경우:

- 바로 BR CONFIRMED로 승격 금지
- `OBSERVED_BEHAVIOR_CANDIDATE`로 기록
- Functional Design / BR Candidate / AC Candidate 연결
- Business 정책이면 Human 확인

## 7. Hotfix-first

Change Request 없이 Source가 먼저 변경된 경우:

```text
Source Diff
→ reverse sync candidate
→ missing CR alert
→ semantic classification
→ document stale candidate
→ test/reverify
```

Hotfix 자체를 이유로 전체 RQ를 INVALID 처리하지 않는다.

## 8. 출력

최소 필드:

- reverse_sync_id
- base_revision
- changed_revision
- changed_units[]
- resolved_pgm_ids[]
- resolved_data_ids[]
- semantic_class
- evidence[]
- affected_artifact_candidates[]
- stale_candidates[]
- tests_to_run[]
- open_items[]
- escalation
- reviewed_by
- final_disposition

## 9. Deterministic Validation

- base/current revision 존재
- changed unit locator 존재
- PGM/ART relation ID format
- candidate trace link 유효성
- OPEN preservation
- reviewed classification 없이 `BUSINESS_RULE_CHANGE` 확정 금지

## 10. Stop / Escalation

Stop:
- direct relations와 configured reverse depth를 모두 확인
- semantic class 또는 UNKNOWN이 기록됨
- candidate artifact/test가 기록됨

Escalate:
- BUSINESS_RULE_CHANGE
- UNKNOWN
- high blast radius
- cross-system transaction
- security/auth semantics change
- missing PGM/ART relation
