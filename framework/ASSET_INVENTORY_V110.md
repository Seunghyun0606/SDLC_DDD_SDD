# v1.10 Repository Asset Inventory

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0`

이 문서는 Repository 자산을 **실제 프로젝트 배포 대상**과 **SDLC Framework 개발/검증 자산**으로 구분하는 현재 기준이다. 과거 경로 설명이 아니라 **현재 물리 구조**를 기준으로 한다.

## 1. 분류값

- `PROJECT_REQUIRED`: 기본 Project Scaffold에 반드시 포함
- `PROJECT_OPTIONAL`: 선택 기능/고객/Brownfield/Extension을 사용할 때만 포함
- `FRAMEWORK_ONLY`: Framework 개발, Test, Pilot, Validation, 비교 Sample, 설계이력
- `COMPATIBILITY_ONLY`: 신규 기본 구조에는 필요 없지만 기존 참조 호환 때문에 남아 있음
- `GENERATED`: 프로젝트 실행 중 생성되는 상태/문서

## 2. 최상위 경계

| 경로 | 판정 | 현재 역할 |
|---|---|---|
| `.cursor/rules/` | PROJECT_REQUIRED(Cursor) | Cursor host rule adapter |
| `.cursor/skills/` | PROJECT_REQUIRED(Cursor) | Cursor host skill adapter |
| `sdlc/agent/skills/` | PROJECT_REQUIRED | Vendor-neutral Agent Core skill |
| `sdlc/config/` | MIXED | Runtime policy + optional project config + compatibility alias |
| `sdlc/custom/` | PROJECT_OPTIONAL | Project/Domain overlay, custom tailoring, adapter |
| `sdlc/design/contracts/` | PROJECT_REQUIRED + OPTIONAL | Runtime/validator가 실제 읽는 Contract |
| `sdlc/scripts/` | MIXED | Project Runtime + Extension + Framework utility |
| `sdlc/starter-kits/` | PROJECT_REQUIRED | Greenfield/Brownfield starter assets |
| `sdlc/tailoring/standard/` | PROJECT_REQUIRED + COMPATIBILITY | 신규 기본 Profile + Legacy Profile |
| `sdlc/templates/` | PROJECT_REQUIRED + COMPATIBILITY | Engineering/Customer template + Legacy template |
| `sdlc/runtime/` | GENERATED | 실행 중 machine state |
| `docs/00_시작/` | PROJECT_REQUIRED | 프로젝트 사용자 가이드의 Primary SoT |
| `docs/00_관리/` | GENERATED | Project-generated / PM-facing 관리 출력 전용 |
| `framework/` | FRAMEWORK_ONLY | Framework 개발/검증 자산의 물리 경계 |
| `tests/` | FRAMEWORK_ONLY | Framework regression/contract/pilot tests |
| `.github/` | FRAMEWORK_ONLY | Framework CI |

## 3. Framework-only 물리 구조

```text
framework/
├─ README.md
├─ ASSET_INVENTORY_V110.md
├─ design/                  # baseline/candidate/review/session/validation 설계 이력
├─ management/              # Framework 자체 worklist/관리자료
├─ pilots/                  # Pilot 및 과거 pilot history
├─ samples/                 # 비교/교육/검증 fixture
└─ validation/              # validation report + assets/provider/fixture
```

이동 완료 항목:

- 기존 `sdlc/design/baselines|candidates|reviews|session|validations` → `framework/design/`
- 기존 `docs/99_파일럿` → `framework/pilots/history/`
- 기존 `docs/00_관리`의 Framework validation/pilot/worklist/sample → `framework/validation|pilots|management|samples`
- 기존 `sdlc/samples` 비교/교육 fixture → `framework/samples/`
- 기존 `sdlc/validation` 실내용 → `framework/validation/assets/`
- 중복 `sdlc/guides` → 제거

## 4. Compatibility 경계

과거 참조를 살리기 위해 **내용 복제를 다시 만들지 않는다**.

현재 compatibility 경계:

```text
sdlc/validation
  -> framework/validation/assets

sdlc/config/customer-document-profile.example.json
  -> customer-document-profile.json
```

신규 Runtime과 신규 Project Scaffold는 항상 정식 경로를 사용한다. Compatibility 경로는 Project Scaffold에서 제외한다.

## 5. `sdlc/config` 판정

### PROJECT_REQUIRED

- `change-execution-policy.json`
- `program-spec-readiness.json`
- `customer-document-profile.json`

`customer-document-profile.json`이 Customer Projection Runtime의 정식 기본 Config다. `.example.json`은 호환 alias일 뿐 신규 배포 의존성이 아니다.

### PROJECT_OPTIONAL

- `architecture-rules.json`
- `impact-adapter-profile.example.yaml`
- `requirement-intake-columns.example.yaml`
- `open-resolution-profile.example.yaml`
- `terminology-profile.example.json`
- `br-intake-profile.example.json`

### COMPATIBILITY_ONLY / FRAMEWORK_ONLY

- `project-profile.example.yaml`: legacy project profile 참고
- `source-profile.example.yaml`: legacy/effective source profile 참고
- `project.example.yaml`: Framework test/example
- repeatability/overlay/worklist 계열 config: Framework validation/management 용도

## 6. Runtime Contract 경계

`sdlc/design/contracts/`는 이름과 달리 단순 설계문서가 아니다. 다음과 같은 Contract는 Runtime/validator가 직접 사용하므로 Project 배포 대상이다.

- Agent execution
- Business scenario 6W
- Developer specification
- Customer document projection
- Open resolution
- Starter kit
- Brownfield/source drift
- Document extraction
- Project scaffold/package contract 중 배포 선택용 Contract는 Framework distribution tool과 함께 Framework에서 관리

설계 이력은 모두 `framework/design/`으로 분리한다.

## 7. Script 분류

### PROJECT_REQUIRED — 기본 실행 경로

```text
harness.py
bootstrap_project.py
project_config.py
runtime_config.py
intake_explainable.py
intake_requirements.py
import_requirements.py
tailored_work.py
interactive_work.py
work_handoff.py
run_work.py
review_work.py
interactive_change.py
run_change.py
change_execution_runtime.py
tailored_check.py
run_check.py
tailoring_runtime.py
apply_canonical_delta.py
projection_lifecycle_runtime.py
validate_agent_stage_result.py
validate_program_spec.py
delivery_status_runtime.py
capture_customer_decision.py
customer_projection_runtime.py
render_customer_document.py
```

### PROJECT_OPTIONAL — Enhancement/Brownfield/Document ingest

```text
architecture_check.py
component_state_runtime.py
impact_learning_runtime.py
unexpected_discovery_runtime.py
sdlc_metrics_runtime.py
build_reverse_inputs.py
detect_source_drift.py
run_source_reverse_check.py
generate_program_spec_reverse_candidate.py
extract_document_evidence.py
normalize_external_evidence.py
resolve_overlay.py
run_knowledge_promotion.py
```

### FRAMEWORK_ONLY

```text
build_project_scaffold.py
generate_tailoring_profile_comparison.py
empirical_pilot_runtime.py
run_agent_repeatability_experiment.py
run_work_repeatability_experiment.py
run_greenfield_e2e_pilot.py
validate_public_brownfield_pilot.py
validate_empirical_pilot_evidence.py
validate_canonical_projection_invariant.py
validate_document_experience.py
validate_harness_structure.py
normalize_mermaid.py
sync_worklist.py
```

### COMPATIBILITY_ONLY

- `runtime_config_v19.py`: `project_config.py`를 re-export하는 thin compatibility wrapper. 신규 business rule 구현 위치가 아니다.

## 8. Tailoring/Profile 경계

신규 기본:

- Engineering: `ENGINEERING_SDD_COMPACT`
- Customer: `CUSTOMER_STANDARD_3`
- Customer Full 선택: `CUSTOMER_WATERFALL_FULL`
- PM: `PM_STANDARD`

Legacy compatibility:

- `STANDARD_3`
- `STANDARD_5`
- `STAGE_ORIENTED_FULL`
- `sdlc/templates/tailoring/standard/` Legacy templates

Legacy profile/template은 기본 Project Scaffold에서 제외하고 명시적 compatibility opt-in일 때만 배포한다.

## 9. Guide SoT

프로젝트 사용자용 문서의 SoT는 `docs/00_시작/`이다.

현재 핵심 문서:

- `START_HERE.md`
- `02_PROJECT_설정가이드.md`
- `03_TAILORING_설정가이드.md`
- `04_TEMPLATE_및_산출물_가이드.md`
- `05_이해관계자별_작업가이드.md`
- `07_BROWNFIELD_SSOT_현행화가이드.md`
- `11_INPUT_자료_준비가이드.md`

과거 `sdlc/guides`는 제거됐고, 과거 Scaffold 전용 가이드 경로가 꼭 필요할 때만 최소 compatibility notice를 사용한다.

## 10. Project Scaffold 제외 규칙

기본 Project Scaffold에는 다음을 넣지 않는다.

```text
framework/**
tests/**
.github/**
Framework validation/pilot/sample/design-history assets
sdlc/validation compatibility path
sdlc/guides compatibility path
Legacy STANDARD_3/STANDARD_5/STAGE_ORIENTED_FULL
Legacy tailoring templates
Framework distribution tool 자체
```

프로젝트에는 선택된 Runtime/Contract/Profile/Template/User Guide만 배포한다.

## 11. Generated 경계

프로젝트 실행 중 생성되는 대표 경로:

```text
sdlc/runtime/**
sdlc/canonical/store.json
docs/00_관리/**
docs/10_engineering/**
docs/20_customer/**
```

Framework Repository의 source 문서와 Generated 프로젝트 산출물을 같은 폴더 의미로 혼용하지 않는다.

## 12. v1.10 정리 판정

- Framework-only 문서/fixture의 주요 물리 이동: 완료
- `sdlc/guides` 중복 제거: 완료
- Customer Projection 기본 Config 정식 이름 전환: 완료
- Legacy Customer config 이름: compatibility alias로 축소
- `sdlc/validation` 실내용: Framework로 이동, legacy path는 compatibility symlink
- `sdlc/design`: Runtime Contract만 유지, 설계 이력은 Framework로 분리
- Project Scaffold: Framework/Legacy 기본 자산 제외 정책 유지
- 최종 회귀 판정: 최신 PR CI 결과를 별도 Validation Report에서 기록
