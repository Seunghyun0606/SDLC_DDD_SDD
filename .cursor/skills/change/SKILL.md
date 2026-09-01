# /change

자연어 변경을 `CLARIFICATION / BEHAVIOR_CHANGE / TECHNICAL_CHANGE / NEW_REQUIREMENT`로 구조화한다.

1. Target과 Before/After를 식별한다.
2. RQ/FR/BR/PROC/PGM/TASK/AC/TC 관계를 따라 영향 범위를 계산한다.
3. 기존 Source Evidence와 충돌하면 기존 설계/Knowledge를 `STALE` 또는 `CHECK_REQUIRED` 후보로 분류한다.
4. 확정되지 않은 변경은 Alert/Assumption과 함께 진행하며 위험 Source write만 Guard한다.
5. 변경 원문과 provenance를 보존한다.
6. 변경 분석 Artifact와 Canonical Delta를 하나의 Stage Result Envelope로 묶어 `sdlc/scripts/validate_agent_stage_result.py`로 검증한다.
7. 검증된 Canonical 값/관계/근거 변경만 `sdlc/scripts/apply_canonical_delta.py`로 적용한다. 문서에 “Canonical 반영”이라고 적는 것만으로 갱신 완료로 간주하지 않는다.

## 변경 Stage Result 검증
변경 분석도 `/work`와 동일한 Machine 실행 경계를 사용한다.

```json
{
  "schema_version": 1,
  "stage": "CHANGE",
  "artifact_path": "docs/.../change-analysis.md",
  "canonical_delta": {},
  "quality_gate": {"status": "PASS", "failures": []},
  "alerts": [],
  "uncertainty": []
}
```

검증:
`python sdlc/scripts/validate_agent_stage_result.py --result <change-result.json> --store sdlc/canonical/store.json --out <validation-result.json>`

- `validation.status = PASS`이면서 `validation.executable = true`인 경우에만 Canonical 적용 단계로 이동한다.
- Artifact/Delta Stage 불일치, source_artifact 불일치, stale revision, 미해결 Template placeholder가 있으면 변경을 적용하지 않는다.
- 동일 변경을 반복 실행해 비교할 때는 `--compare`로 semantic fingerprint를 확인할 수 있다.
- 이 비교는 LLM 자체의 결정론을 보장하지 않으며 실제 생성 결과의 의미 차이를 검출하기 위한 것이다.

## Canonical 변경 적용
변경 요청이 Canonical에 영향을 주면 현재 Store revision을 기준으로 최소 Delta를 만든다.

```json
{
  "schema_version": 1,
  "delta_id": "change 요청을 재실행해도 동일한 ID",
  "base_revision": 0,
  "stage": "CHANGE",
  "source_artifact": "변경 원문 또는 변경 분석 산출물",
  "operations": []
}
```

지원 Operation:
- `UPSERT_ENTITY`: 변경으로 새로 생기거나 값이 달라진 Entity만 반영
- `UPSERT_RELATION`: 변경된 관계만 반영
- `ADD_PROVENANCE`: 값은 유지하고 변경 원문/Source 관찰 근거만 연결

실행:
1. Stage Result Validator가 해당 Delta를 현재 Store에서 `APPLIED` 또는 `IDEMPOTENT` 가능하다고 판정했는지 확인한다.
2. `python sdlc/scripts/apply_canonical_delta.py --delta <delta.json> --dry-run`
3. `APPLIED` 후보일 때만 실제 적용한다.
4. `python sdlc/scripts/apply_canonical_delta.py --delta <delta.json> --result-out <result.json>`
5. `CONFLICT`면 Store를 부분 수정하지 않는다. 최신 revision을 다시 읽고 Before/After를 재평가한다.
6. `IDEMPOTENT`면 동일 변경이 이미 반영된 것이므로 중복 적용하지 않는다.

### Business Truth 안전 규칙
- 고객/업무 권한자가 확인한 `CONFIRMED_BUSINESS`를 Source 관찰만으로 변경하거나 상태를 낮추지 않는다.
- 기존 Source에서 다른 동작이 관찰되면 Business Truth 수정이 아니라 우선 `ADD_PROVENANCE`, `CHECK_REQUIRED`, 변경 Proposal 중 하나로 기록한다.
- `CONFIRMED_BUSINESS` 신규/변경은 `evidence_class: CONFIRMED`가 필요하다.
- DELETE는 현재 Canonical Runtime 범위가 아니다. 삭제 요구는 영향분석과 명시적 후속 처리 대상으로 둔다.
- Canonical Delta 적용 성공과 Source Code write 승인은 별개다.

## Source Drift Reverse 처리
Source 기준점이 바뀌었거나 외부에서 Source가 수정된 경우 다음 공통 절차를 사용한다.

1. 기존 산출물과 연결된 `baseline source manifest`를 준비한다.
2. 현재 Source의 `observed source manifest`를 준비한다.
3. Artifact별 Source Evidence와 역방향 전파 관계를 `artifact evidence index`로 준비한다.
4. `python sdlc/scripts/detect_source_drift.py --baseline <baseline.json> --observed <observed.json> --artifact-index <artifact-index.json> --output <reverse-report.json>`을 실행한다.
5. `STALE_SOURCE_EVIDENCE`는 실제 Source hash가 달라진 직접 영향 산출물이다.
6. 명시적 전파 Edge가 `STALE`이면 `STALE_PROPAGATED`, `CHECK_REQUIRED`이면 `CHECK_REQUIRED_REVERSE`로 기록한다.
7. Reverse 결과는 Candidate만 만든다. 기존 문서나 Canonical Business Truth를 자동 덮어쓰지 않는다.
8. 현행 Source 관찰을 Canonical에 연결해야 하면 Business 값을 덮는 `UPSERT_ENTITY`보다 `ADD_PROVENANCE`를 우선 사용한다.
9. 재생성/검토가 끝난 뒤에만 현재 Source Evidence hash로 Artifact를 갱신한다.

## Program Spec Semantic Reverse Candidate
Brownfield Impact Adapter의 기준점/현재 결과가 모두 있고 Program Spec과 Source Node의 Binding이 등록되어 있으면 Source 변화에서 구현 명세 갱신 후보를 만들 수 있다.

실행:
`python sdlc/scripts/generate_program_spec_reverse_candidate.py --baseline-impact <before-impact.json> --observed-impact <after-impact.json> --program-bindings <program-bindings.json> --output <program-reverse-candidate.json>`

규칙:
1. Program Binding은 `program_id / artifact_path / functional_design_ref / source_node_ids`를 가진다.
2. Candidate는 해당 PGM의 Source Node와 실제 변경 Node/Edge가 설정된 hop 범위 안에서 연결될 때만 생성한다.
3. 전역 Coverage 변화만으로 관계 없는 Program Spec Candidate를 만들지 않는다.
4. Candidate가 수정할 수 있는 범위는 Program Spec의 구현 Target, Source 근거, 구현 Mapping/Delta, Query/Table, Transaction, Integration 기술 계약, 기술 제어, TASK/AC/TC/Source, 준비도뿐이다.
5. 업무 시나리오, 업무 규칙, 기능 요구 의미, 업무 예외, Business Truth는 자동 갱신 금지다.
6. 결과는 `review_required: true`, `auto_apply: false`다. Generator는 실제 Program Spec 파일을 수정하지 않는다.
7. 검토자가 Candidate를 수용한 뒤에도 Program Spec 갱신과 Canonical Delta 적용은 별도 Stage Result 검증을 거친다.

### 안전 규칙
- 신규 Source가 생겼다는 이유만으로 관련 없는 기존 문서를 자동 STALE 처리하지 않는다.
- Source-derived 설계/프로그램 문서는 `STALE` 전파가 가능하지만, 고객 승인 Requirement/BR 등 권위 있는 업무 사실은 기본적으로 `CHECK_REQUIRED`가 적절하다.
- 역방향 전파는 명시된 Artifact Edge를 통해서만 수행한다.
- Source 변경은 Business Truth 변경의 증거 후보이지 자동 정책 변경이 아니다.
- Semantic Reverse Candidate는 Program Spec 구현정보 갱신 후보일 뿐 Functional Design 재작성기가 아니다.
