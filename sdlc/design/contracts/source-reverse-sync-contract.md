# Source → Documentation Reverse Sync Contract — P0

상태: `ACTIVE_P0_CANDIDATE`

## 목적

요구사항 문서에서 Source로 내려가는 Trace뿐 아니라 Source 변경에서 관련 설계/요구/테스트 문서로 되돌아가는 경로를 표준화한다.

## 기본 Pipeline

```text
Changed File
→ Changed Symbol / SQL / Interface
→ Direct PGM/ART Relation
→ Semantic Change Candidate
→ Related FR/BR/AC/TC
→ STALE Candidate
→ Human Truth 보호
→ Re-analysis / Regenerate
```

## Semantic Change Class

- `TECHNICAL_ONLY`: Refactor, logging, non-behavioral implementation detail
- `FUNCTIONAL_BEHAVIOR`: 사용자 관찰 동작 변화 후보
- `BUSINESS_RULE_CANDIDATE`: 조건/정책/예외 의미 변화 가능성
- `DATA_CONTRACT`: Table/Column/Query semantics 또는 schema 계약 변화
- `INTERFACE_CONTRACT`: API/File/Message 계약 변화
- `SECURITY_BEHAVIOR`: Auth/AuthZ/Security policy 구현 변화
- `UNKNOWN`: 근거 부족

## Evidence Priority

1. Commit/PR에 연결된 RQ/TASK/CR
2. Canonical direct PGM/ART relation
3. Changed symbol / SQL / table relation
4. Test delta
5. Runtime/Static evidence
6. Semantic inference

Name similarity만으로 BR/FR을 확정하지 않는다.

## 자동 처리 가능 범위

- 변경 ART/PGM 직접 관계 갱신
- 관련 Technical Knowledge의 `STALE_CANDIDATE`
- 관련 Test 재실행 후보 생성
- Generated Summary 재생성 후보 생성

## 자동 처리 금지

- Human Truth 문구 자동 overwrite
- `OBSERVED Source Change`를 `CONFIRMED Business Rule`로 승격
- `BUSINESS_RULE_CANDIDATE`, `SECURITY_BEHAVIOR`, `UNKNOWN`을 검토 없이 Current Truth로 반영
- Direct relation 없는 FR/BR/AC를 단순 키워드로 STALE 확정

## STALE 규칙

- Direct PGM/ART relation: `STALE_CANDIDATE` 자동 가능
- Confirmed FR/BR/AC relation + behavior change evidence: `STALE_CANDIDATE` 가능
- Business Rule 변경 후보: Human Review 필요
- UNKNOWN: Related Candidate만 기록하고 확정 STALE 금지

## Reverse Sync Candidate 필수 항목

- change_id
- source_revision_before / after
- changed_files
- changed_symbols
- direct_program_ids
- semantic_change_class
- evidence
- related_rq/fr/br/ac/tc 후보
- stale_candidates
- protected_human_truth
- required_review
- status

## 완료 조건

Reverse Sync는 모든 문서를 자동 수정했을 때 완료되는 것이 아니다. 다음이 충족되면 해당 실행은 완료 가능하다.

1. Source Diff가 Evidence로 저장됨
2. 직접 Trace가 해석됨
3. 의미 변경 Class가 값 또는 `UNKNOWN`으로 존재함
4. STALE 후보가 명시됨
5. Human Truth 보호 여부가 명시됨
6. 필요한 Reviewer가 명시됨
