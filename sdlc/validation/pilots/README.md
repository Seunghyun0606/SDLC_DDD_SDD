# v1.9 실제 실증 Pilot 실행 가이드

이 디렉터리는 CI/Fixture/구조 검증과 **실제 관찰 Evidence**를 분리하기 위한 실행 패키지다.

가장 중요한 원칙은 다음 세 가지다.

1. 실행하지 않은 Pilot은 `NOT_RUN`이다.
2. `provider_class: EXTERNAL_AGENT` 같은 선언만으로 실제 Agent 실행을 증명하지 않는다.
3. Public Source 분석만으로 고객의 Business Truth를 확인하거나 수정하지 않는다.

## 1. 공통 실행 절차

각 Pilot은 `.example.json`을 복사해 실제 관찰 결과 파일을 만든다.

```bash
cp sdlc/validation/pilots/external-agent-tailoring-pilot.example.json /tmp/external-agent-pilot.json
python sdlc/scripts/validate_empirical_pilot_evidence.py \
  --input /tmp/external-agent-pilot.json \
  --output /tmp/external-agent-pilot-result.json
```

실행 전 상태에서는 정상적으로 다음과 같이 판정되어야 한다.

```text
verdict = NOT_RUN
empirical_pass = false
```

관찰하지 않은 상태에서 `claims.*_pass=true`만 설정하면 `FAIL_OVERCLAIMED_PASS`가 되어야 한다.

---

## 2. External Agent 3/5/Full 의미보존 Pilot

대상 파일:

- `external-agent-tailoring-pilot.example.json`
- 구조 비교 기준: `sdlc/samples/tailoring/PROFILE_COMPARISON_3_5_FULL.md`

### 목적

동일 Canonical `RQ-COMP-001`을 실제 External Agent가 다음 세 Profile로 작성했을 때 문서 수가 달라져도 업무 의미가 보존되는지 관찰한다.

- `STANDARD_3`
- `STANDARD_5`
- `STAGE_ORIENTED_FULL`

### 반드시 기록할 것

- 관찰 일시와 관찰자
- 실제 Provider/Agent 식별 정보
- 관찰자가 확인 가능한 Session/Run/Provider Identity Evidence
- 세 Profile별 실제 생성 Artifact 경로
- 각 Profile에 대한 Human Semantic Review
  - `meaning_preserved`
  - `unsupported_business_fact_count`
  - `material_omission_count`
  - reviewer

### PASS의 의미

이 Pilot의 PASS는 **관찰된 한 Pilot 범위에서 세 Profile의 의미보존 기준을 만족했다**는 뜻이다.
LLM 결정성, 모든 프로젝트에 대한 일반화, Production Ready를 의미하지 않는다.

---

## 3. Human First-use Pilot

대상 파일:

- `human-first-use-pilot.example.json`
- 사용자 시작점: `docs/00_시작/START_HERE.md`

### 대상자

Framework 설계자가 아닌 일반 SI/SM 프로젝트 참여자를 사용한다.
Controlled Pilot 최소 표본은 3명으로 한다.

### 참여자별 기록

- `participant_id`: 개인정보 대신 Pilot 내부 식별자 사용
- `role`: 예) 업무분석, 설계/개발, PM
- `started_from_start_here`: START_HERE만 안내하고 시작했는지
- `completed_without_framework_designer`: Framework 설계자의 개입 없이 지정 흐름을 완료했는지
- `critical_blocker_count`: 진행을 막아 외부 설명이 필요했던 문제 수
- `review_burden_rating_1_to_5`: 산출물 검토부담 체감값

### PASS의 의미

최소 3명의 실제 참여자가 START_HERE에서 시작하고 Framework 설계자의 개입 없이 완료하며 Critical Blocker가 없어야 한다.
Review burden 값은 비교/개선 지표이며 단독 PASS 기준으로 사용하지 않는다.

현재 `tests/test_wp5_first_use_evidence.py`의 Fixture는 Runtime 동작 검증이며 실제 Human 관찰 Evidence가 아니다.

---

## 4. Brownfield Reconciliation Pilot

대상 파일:

- `brownfield-reconciliation-pilot.example.json`
- 권위 기준: `sdlc/design/contracts/brownfield-authority-reconciliation-contract.json`

### 반드시 함께 존재해야 하는 Evidence

1. `CURRENT_SOURCE_DB_CONFIG_RUNTIME_EVIDENCE`
2. `CONFIRMED_HUMAN_BUSINESS_TRUTH`
3. Reviewer Decision

Source가 Business Truth와 다르더라도 Source가 Canonical Business Truth를 자동 수정해서는 안 된다.
Conflict를 발견하고 사람이 결정을 내려 안전하게 Reconciliation한 경우에도 Pilot 수행 자체는 PASS가 될 수 있다. 즉 `ALIGNED`만 성공이고 `CONFLICT`는 실패라는 의미가 아니다.

### Public Brownfield Pilot과의 관계

`.github/workflows/public-brownfield-pilot.yml`은 실제 공개 Repository의 Source 관계를 관찰하는 Integration Evidence다.
그러나 공개 Repository에는 고객의 Confirmed Business Truth가 없으므로 **그 Workflow만으로 Brownfield Reconciliation Empirical PASS를 주장할 수 없다.**

---

## 5. 검증 명령

```bash
python sdlc/scripts/validate_empirical_pilot_evidence.py --input <pilot-evidence.json>
```

가능한 주요 Verdict:

- `NOT_RUN`: 아직 실제 관찰 안 함
- `PASS_OBSERVED_EMPIRICAL_PILOT`: 필요한 실제 Evidence가 있고 Pilot 기준 충족
- `FAIL_OBSERVED_EMPIRICAL_PILOT`: Evidence는 충분하지만 관찰 결과가 기준 미충족
- `FAIL_INSUFFICIENT_EVIDENCE`: 관찰을 주장했으나 필수 Evidence 부족
- `FAIL_OVERCLAIMED_PASS`: 필수 Evidence가 없는데 PASS Claim을 설정함

## 6. Branch / Release 경계

Pilot Evidence는 `SDLC_DESIGN_SESSION_FIRST/...` Branch에서 수집한다.
실증 PASS가 나오더라도 자동으로 `main` merge 또는 Production Ready 판정을 하지 않는다.
