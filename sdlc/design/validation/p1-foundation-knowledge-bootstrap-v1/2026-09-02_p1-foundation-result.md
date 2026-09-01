# P1 Foundation / Knowledge Bootstrap Result

> Branch: `SDLC_DESIGN_SESSION_SECOND/p1/foundation-knowledge-bootstrap-v1`
> Base: `SDLC_DESIGN_SESSION_SECOND/p0.final/design-baseline-exit-v1`
> Date: 2026-09-02

## Verdict

**P1 FOUNDATION: READY FOR REAL BROWNFIELD ONBOARDING**

Machine state:

`P1_FOUNDATION_READY_REAL_SLICE_REQUIRED`

Production Ready: `false`

P1 전체 Scale-out 완료를 의미하지 않는다. 실제 고객 Source를 연결하고 대표 Requirement 1건의 Vertical Slice를 검토한 뒤 `READY_FOR_SCALE_OUT`으로 승격한다.

## 1. 핵심 정책

프로젝트 시작 전에 모든 Custom 항목을 확정하지 않는다.

```text
CORE DEFAULT
→ PROJECT PROFILE
→ 실제 작업 진행
→ 프로젝트 차이 관찰
→ Overlay PROPOSED
→ 근거/범위 검토
→ 필요한 항목만 ACTIVE
```

다음은 사전 완료 조건이 아니다.
- 전체 Source 경로
- 모든 Build/Test/DB/Interface 위치
- 모든 용어
- 모든 Stage/Artifact 차이
- 모든 Provider 연결
- 모든 개발표준 Override

현재 작업에서 필요해지는 시점에 JIT로 발견하고, Core/Profile과 실제 프로젝트 사실이 충돌할 때만 Overlay를 만든다.

## 2. 구현 완료

- `sdlc/config/p1-foundation.yaml`
- `sdlc/templates/project-bootstrap-manifest.yaml`
- `sdlc/templates/project-overlay.yaml`
- `sdlc/templates/knowledge-candidate.yaml`
- `sdlc/templates/glossary-entry.yaml`
- `sdlc/templates/reference-graph.yaml`
- `sdlc/templates/open-item.yaml`
- `sdlc/design/contracts/p1-foundation-late-customization.md`
- `sdlc/scripts/validate_p1_foundation.py`
- `sdlc/scripts/resolve_project_overlay.py`
- `sdlc/scripts/lint_p1_knowledge.py`
- `sdlc/scripts/evaluate_open_items.py`
- `sdlc/scripts/build_baseline_cache.py`
- `sdlc/scripts/assess_p1_scale_out.py`
- `sdlc/scripts/test_p1_foundation.py`
- `sdlc/scripts/test_p1_runtime.py`
- `sdlc/starter/onboarding-package-v1/skills/project-foundation-bootstrap/SKILL.md`
- `sdlc/guides/04_HARNESS_커스터마이징가이드.md`

## 3. Late-bound Customization

Overlay 생성이 허용되는 경우:
- Core/Profile과 관찰된 실제 프로젝트 구조가 충돌
- 실제 산출물에 프로젝트 용어/파일/Stage 차이가 필요
- Source/Provider/Build/Test path binding이 실제로 필요
- 프로젝트 표준이 Core Default와 실제로 다름

Overlay 생성 사유가 아닌 경우:
- 나중에 필요할 것 같음
- Sample/Pilot에 값이 존재함
- 프로젝트 근거 없는 선호

`ACTIVE` Overlay만 resolver가 적용하며 `PROPOSED`는 자동 적용하지 않는다.

## 4. Knowledge / Glossary

Knowledge는 Candidate로 시작하며 provenance를 요구한다.

Source에서 관찰한 동작은 `OBSERVED`이고 Business Truth 자동 `CONFIRMED`는 금지한다.

Glossary는 stable `term_id`, normalized term, provenance를 가지며 duplicate normalized term을 lint한다.

## 5. Reference Graph

Reference Graph는 RQ/FR/PGM/ART/SYMBOL/DATA/AC/TC/TASK/Knowledge 등을 연결할 수 있다.

모든 Edge는 evidence/source provenance를 가져야 한다. 없는 Node 참조는 조용히 버리지 않고 unresolved OPEN으로 보존해야 한다.

## 6. OPEN runtime

OPEN은 기본적으로 Workflow를 멈추지 않는다.

분석/설계/조회성 작업은 계속할 수 있다.

다만 다음과 같은 부작용 Action은 관련 OPEN Item이 명시적으로 Guard할 수 있다.
- Source write
- DB write
- Canonical publish
- Deploy
- Test execution
- External write

## 7. Baseline Cache

Baseline Cache는 Truth 저장소가 아니다.

`path + sha256 + declared revision`의 derived reference만 만들며 재생성 가능하다.

Source/Authority가 변경되면 Cache를 다시 생성하는 구조다.

## 8. Sample overfitting 방지

첨부 요구사항 샘플은 P1 Foundation 입력으로 사용하지 않았다.

P1 Core Self-test는 다음 Pilot token이 Core에 들어오면 실패하도록 정의했다.
- `REQ_TM_TE`
- `RQG-CAND-6BB6D66548`
- `AttendanceClose`
- `TB_ATT_`
- `10분`

Generic Brownfield fixture는 별도 `DEMO-GENERIC-001`로 만들었다.

## 9. Real Project Scale-out Gate

현재 상태에서는 실제 고객 Source가 없으므로 다음 두 항목이 남는다.

- `REAL_SOURCE_REQUIRED`
- `REPRESENTATIVE_VERTICAL_SLICE_REQUIRED`

실제 프로젝트에서는 다음 순서로 진행한다.

```text
Real Source 연결
→ Project Bootstrap Manifest
→ 실제 RQ 1건 선택
→ JIT Source/Knowledge/Reference bootstrap
→ 필요한 차이만 Overlay
→ Analysis/Impact/Design/Development/Test/Verify
→ Vertical Slice Review
→ READY_FOR_SCALE_OUT
→ 전체 요구사항 확장
```

## 10. Validation Basis / Limitation

Generic positive/negative self-test 정의를 추가했다.

주요 Negative Case:
- upfront customization 강제
- JUST_IN_CASE Overlay
- Sample-only Overlay
- Core Truth copy Overlay
- provenance 없는 graph edge
- dangling reference silent drop
- review 없는 observed knowledge promotion
- duplicate glossary term

현재 세션에서는 GitHub branch를 별도 local checkout한 CI/runtime 실행 증거를 만들지 않았다. 따라서 Repository 전체 Python suite PASS 또는 실제 고객 Project PASS를 주장하지 않는다.

## Final State

```text
P1 Core Foundation = READY
Late-bound Customization = READY
Knowledge/Reference Bootstrap Contract = READY
Real Customer Source = NOT CONNECTED
Representative Real Vertical Slice = NOT RUN
Full Requirement Scale-out = NOT YET
Production Ready = false
```
