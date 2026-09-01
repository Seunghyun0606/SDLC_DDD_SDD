# /change

자연어 변경을 `CLARIFICATION / BEHAVIOR_CHANGE / TECHNICAL_CHANGE / NEW_REQUIREMENT`로 구조화한다. 실제 실행 Runtime은 `sdlc/scripts/run_change.py`이며 일반 사용자는 다음 단일 진입점을 사용한다.

```bash
python sdlc/scripts/harness.py change \
  --target <RQ/PGM/TASK/기타 ID> \
  --change '<변경 요청 원문>'
```

## 실행 원칙
1. Target과 변경 원문을 보존한다.
2. Target 중심 Canonical relation graph만 변경 권한 범위로 사용한다.
3. 변경 요청을 분류하되 분류 자체가 Business Truth 확정 권한을 만들지 않는다.
4. Source 관찰과 고객/업무 확정을 구분한다.
5. 확정 Business Truth 변경은 명시적 승인 없이 적용하지 않는다.
6. Provider 실행은 `/work`와 같은 Git HEAD/branch/dirty/write-scope Guard 안에서 수행한다.
7. 변경 결과는 Stage Result Validator를 통과한 뒤에만 locked/atomic Canonical Runtime으로 반영한다.
8. 실패하면 이번 Provider 실행이 만든 Git working-tree 변경을 rollback한다. 자동 Merge/commit은 하지 않는다.

## Plan Only
실제 Provider 실행 전에 변경 범위와 기준점을 확인할 수 있다.

```bash
python sdlc/scripts/harness.py change \
  --target RQ-001 \
  --change '환불 상태 조회를 추가한다' \
  --plan-only
```

Plan에는 최소 다음이 들어간다.
- Target graph
- Canonical base revision
- Git commit/branch baseline
- 변경 원문
- 허용된 기존 Canonical entity 범위
- Source write root
- Business Truth Guard

## 변경 Stage Result 검증
변경 분석도 `/work`와 동일한 Machine 실행 경계를 사용한다.

```json
{
  "schema_version": 1,
  "stage": "CHANGE",
  "artifact_path": "sdlc/runtime/change/RQ-001/CHANGE_change-analysis.md",
  "canonical_delta": {},
  "quality_gate": {"status": "PASS", "failures": []},
  "alerts": [],
  "uncertainty": []
}
```

검증:

```bash
python sdlc/scripts/validate_agent_stage_result.py \
  --result <change-result.json> \
  --store sdlc/canonical/store.json \
  --out <validation-result.json>
```

- `validation.status = PASS`이면서 `validation.executable = true`인 경우에만 Canonical 적용 단계로 이동한다.
- Artifact/Delta Stage 불일치, source_artifact 불일치, stale revision, 미해결 Template placeholder가 있으면 적용하지 않는다.
- 동일 변경의 반복 실행 의미를 비교할 때는 `--compare`와 semantic fingerprint를 사용할 수 있다.
- 이 비교는 **LLM 자체의 결정론을 보장하지 않으며** 실제 생성 결과의 의미 차이를 검출하기 위한 것이다.

## Canonical 변경 적용
검증된 Delta는 `sdlc/scripts/apply_canonical_delta.py`의 locked atomic write 경계를 사용한다.

지원 Operation:
- `UPSERT_ENTITY`
- `UPSERT_RELATION`
- `ADD_PROVENANCE`

DELETE는 자동 지원하지 않는다.

### Business Truth 안전 규칙
- 기존 `CONFIRMED_BUSINESS`를 바꾸려면 `evidence_class: CONFIRMED`가 필요하다.
- `/change`에서도 사용자가 실제 업무 확정을 명시하지 않았다면 `--allow-business-truth-change`를 사용하지 않는다.
- Source가 기존 업무정책과 다르게 동작해도 Source 관찰을 Business Truth로 자동 승격하지 않는다.
- 값 변경 없이 현행 근거를 연결할 때는 `ADD_PROVENANCE`를 우선한다.

## Source Version / Write Guard
`run_change.py`는 공통 `/work` executor를 사용하므로 다음 Guard를 공유한다.

- 기본 `main/master` 직접 쓰기 금지
- 실행 시작 시 Git HEAD/branch 기록
- 이미 dirty working tree이면 기본 중단
- Provider가 HEAD를 변경하면 중단
- 허용 Source root/선택 Artifact 밖의 파일 변경 차단
- DEVELOPMENT Source write는 build/test command가 없으면 기본 중단
- Stage/Canonical 실패 시 이번 실행에서 생긴 Git 변경 rollback
- Canonical은 file lock → 최신 revision 재읽기 → atomic replace

Repository hosting의 Branch Protection 설정까지 이 Script가 대신하는 것은 아니다. 프로젝트 GitHub/GitLab 정책에서도 default branch 보호를 별도로 활성화한다.

## Source Drift Reverse 처리
외부에서 Source가 변경됐거나 Merge/Rebase 이후 기준점이 바뀐 경우:

```bash
python sdlc/scripts/run_source_reverse_check.py \
  --source-root <source-root> \
  --artifact-root <artifact-root> \
  --source-ref <commit-or-ref> \
  --baseline sdlc/runtime/reverse/baseline.json \
  --output sdlc/runtime/reverse/result.json
```

- `STALE_SOURCE_EVIDENCE`: 직접 Source evidence가 달라진 산출물
- `STALE_PROPAGATED`: 명시적 stale propagation
- `CHECK_REQUIRED_REVERSE`: 상위 업무/설계가 다시 확인되어야 하는 후보
- Source 변경은 자동 Business Truth 변경이 아니다.

## Program Spec Semantic Reverse Candidate
Program Binding과 before/after impact graph가 있으면:

```bash
python sdlc/scripts/generate_program_spec_reverse_candidate.py \
  --baseline-impact <before-impact.json> \
  --observed-impact <after-impact.json> \
  --program-bindings <program-bindings.json> \
  --output <program-reverse-candidate.json>
```

Candidate는 실제 Program Spec 파일을 자동 수정하지 않는다.
- `review_required: true`
- `auto_apply: false`
- 구현 Target/Mapping/Query/Table/Transaction/Integration/기술 제어만 후보화
- 업무 시나리오/업무 규칙/Business Truth 자동 변경 금지

## Customer Decision Round Trip
고객 문서 검토 결과를 다시 근거로 남겨야 할 때:

```bash
python sdlc/scripts/capture_customer_decision.py \
  --input <customer-decision.json>
```

고객 `ACCEPT/REJECT/REQUEST_CHANGE/ACKNOWLEDGE`는 CONFIRMED provenance로 남길 수 있다. 실제 업무 필드 변경은 `field_updates`와 명시적 `--apply-business-change`가 함께 있을 때만 허용한다.

## Do Not
- Source hash 변화만으로 업무 규칙이 바뀌었다고 판단하지 않는다.
- Change classification만으로 권한을 획득했다고 간주하지 않는다.
- 자동 Merge/commit으로 동시 작업 충돌을 숨기지 않는다.
- 실패한 Provider의 Source 변경을 working tree에 남겨 성공처럼 보이지 않는다.
