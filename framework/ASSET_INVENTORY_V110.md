# v1.10 Repository Asset Inventory

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0`

이 문서는 Repository 안의 자산을 **실제 프로젝트 배포 대상**과 **SDLC Framework 개발/검증 자산**으로 분리하기 위한 기준이다.

## 1. 분류값

- `PROJECT_REQUIRED`: 기본 프로젝트 Scaffold에서 반드시 필요
- `PROJECT_OPTIONAL`: 특정 기능/고객/브라운필드/도구를 사용할 때만 필요
- `FRAMEWORK_ONLY`: Framework 개발, Pilot, Test, 비교 Sample, CI, 설계이력. 프로젝트에 배포하지 않음
- `COMPATIBILITY_ONLY`: 신규 기본 구조에는 필요 없지만 Legacy 입력/실행 호환 때문에 아직 제거하지 못함
- `MOVE_CANDIDATE`: 역할은 명확하나 현재 물리 위치가 역할과 맞지 않아 다음 정리 대상

## 2. 최상위 구조 판정

| 경로 | 판정 | 설명 / 조치 |
|---|---|---|
| `.cursor/rules/` | PROJECT_REQUIRED(Cursor) | Cursor host가 직접 읽는 Rule adapter. Cursor 프로젝트에서는 필요 |
| `.cursor/skills/` | PROJECT_REQUIRED(Cursor) | Cursor host용 Skill adapter. `sdlc/agent/skills`와 역할 중복이 아니라 host adapter 역할 |
| `sdlc/agent/skills/` | PROJECT_REQUIRED | Vendor-neutral Agent 실행 지침의 Core. 현재 work/change와 공통 reference가 존재 |
| `sdlc/config/` | MIXED | Runtime policy, optional profile, example, framework test config가 섞여 있어 파일별 분류 필요 |
| `sdlc/custom/` | PROJECT_OPTIONAL | 프로젝트/도메인별 Overlay, Custom Tailoring, Adapter 위치 |
| `sdlc/design/contracts/` | PROJECT_REQUIRED + OPTIONAL | 이름은 design이지만 일부 Contract를 Runtime/validator가 실제 읽음. 단순 설계문서가 아님 |
| `sdlc/design/baselines/` | FRAMEWORK_ONLY | 과거 Full Design baseline |
| `sdlc/design/candidates/` | FRAMEWORK_ONLY | 설계 변경 이력/RC delta |
| `sdlc/design/reviews/` | FRAMEWORK_ONLY | Framework review 기록 |
| `sdlc/design/validations/` | FRAMEWORK_ONLY | Framework validation 기록 |
| `sdlc/design/CHANGELOG.md`, `branch-version.yaml` | FRAMEWORK_ONLY | Framework release/branch metadata |
| `sdlc/guides/` | REMOVE_CANDIDATE | `docs/00_시작`과 중복된 compatibility link. 신규 SoT가 아니므로 제거 대상 |
| `sdlc/runtime/` | GENERATED | 실행 중 생성되는 machine state. 배포 source가 아님 |
| `sdlc/samples/` | FRAMEWORK_ONLY / MOVE_CANDIDATE | 비교/교육/fixture. Runtime Profile 탐색 경로가 아니므로 `framework/samples/`로 이동 |
| `sdlc/scripts/` | MIXED | Project Runtime / optional extension / framework validation script가 혼재 |
| `sdlc/starter-kits/` | PROJECT_REQUIRED | setup 시 Greenfield/Brownfield 시작 자료 |
| `sdlc/tailoring/standard/` | PROJECT_REQUIRED + COMPATIBILITY | 신규 기본 Profile과 Legacy Profile이 함께 있음 |
| `sdlc/templates/` | PROJECT_REQUIRED + COMPATIBILITY | 신규 Engineering/Customer template과 Legacy template이 함께 있음 |
| `docs/00_시작/` | PROJECT_REQUIRED | 프로젝트 사용자용 Primary Guide SoT |
| `docs/00_관리/` | MIXED / MOVE_CANDIDATE | Project-generated 관리 출력 경로와 Framework 검증/작업목록이 충돌. Framework 파일은 이동 대상 |
| `docs/99_파일럿/` | FRAMEWORK_ONLY / MOVE_CANDIDATE | Pilot evidence. 프로젝트 Scaffold에서는 제외하며 장기적으로 `framework/pilots/` 이동 |
| `tests/` | FRAMEWORK_ONLY | Framework regression/contract/pilot test. 일반 프로젝트에 배포하지 않음 |
| `.github/` | FRAMEWORK_ONLY | Framework CI. 일반 프로젝트 Scaffold에서 제외 |
| `framework/` | FRAMEWORK_ONLY | 이 Branch부터 명시적인 Framework-only 물리 경계 |

## 3. `.cursor/skills` vs `sdlc/agent/skills`

현재 의도는 다음과 같다.

```text
sdlc/agent/skills       = vendor-neutral Core
        ↓ host adaptation / compatibility
.cursor/skills          = Cursor가 직접 읽는 Host adapter
```

`work/references/*`는 두 경로가 동일해야 한다는 parity test가 이미 존재한다. 반면 Skill 본문은 host별 adapter 내용이 달라질 수 있다.

현재 Gap:

- `sdlc/agent/skills`: work, change 중심
- `.cursor/skills`: work, change 외 setup/check/open-resolve/sop-extract도 존재

따라서 **둘 중 하나를 지금 삭제하면 안 된다.** 후속 목표는 모든 vendor-neutral Skill을 `sdlc/agent/skills`에 두고 `.cursor/skills`는 thin adapter/생성 mirror로 제한하는 것이다.

## 4. `sdlc/config` 파일별 분류

| 파일 | 판정 | 이유 |
|---|---|---|
| `change-execution-policy.json` | PROJECT_REQUIRED | Change Level / Fast Path 실행 정책 |
| `program-spec-readiness.json` | PROJECT_REQUIRED | Program Spec readiness validator/runtime 사용 |
| `customer-document-profile.example.json` | PROJECT_REQUIRED(현재) | `render_customer_document.py`의 기본 profile 경로. 이름은 example이지만 현재 default runtime dependency이므로 향후 이름 변경 필요 |
| `architecture-rules.json` | PROJECT_OPTIONAL | `arch-check` enhancement 사용 시 필요 |
| `impact-adapter-profile.example.yaml` | PROJECT_OPTIONAL | Brownfield impact adapter 구성 예시 |
| `requirement-intake-columns.example.yaml` | PROJECT_OPTIONAL | 비표준 고객 요구사항 컬럼 매핑 시 사용 |
| `open-resolution-profile.example.yaml` | PROJECT_OPTIONAL | OPEN resolution customizing 시 참조 |
| `terminology-profile.example.json` | PROJECT_OPTIONAL | 문서/용어 customizing 시 사용 |
| `br-intake-profile.example.json` | PROJECT_OPTIONAL | BR/document ingest 확장용 |
| `project-profile.example.yaml` | COMPATIBILITY_ONLY | `.sdlc/project.yaml` 이전 구조의 참고/legacy profile |
| `source-profile.example.yaml` | COMPATIBILITY_ONLY | 새 프로젝트에서는 effective source profile이 Runtime에서 생성됨 |
| `project.example.yaml` | FRAMEWORK_ONLY | Project Config 예시/테스트. 실제 사용자 SSOT는 `.sdlc/project.yaml` |
| `agent-repeatability-profile.example.json` | FRAMEWORK_ONLY | External Agent repeatability experiment |
| `overlay-resolution.example.json` | FRAMEWORK_ONLY | Overlay resolver test/example |
| `worklist-columns.yaml` | FRAMEWORK_ONLY | Framework worklist/sync 관리도구용 |

정리 후보:

1. `customer-document-profile.example.json`은 실제 기본 dependency인데 이름에 `example`이 붙어 있다. `customer-document-profile.json` 같은 Runtime 이름으로 바꾸는 것이 맞다.
2. `*.example.*`는 자동 실행 dependency가 아니라면 `framework/examples/config/` 또는 `sdlc/custom/project/...example`로 이동한다.

## 5. `sdlc/design`

`design` 전체를 Framework-only로 보면 안 된다.

### 실제 Runtime/Project dependency

`sdlc/design/contracts/` 중 다음 계열은 실제 Runtime/validator가 읽는다.

- `agent-execution-contract.json`
- `business-scenario-sixw-contract.json`
- `developer-spec-contract.json`
- `customer-document-contract.json`
- Brownfield/Source Drift/Document Extraction 등 선택 Extension Contract

따라서 `contracts/`는 구현 과정에서 사용된다.

### Framework-only

- `baselines/`
- `candidates/`
- `reviews/`
- `validations/`
- `CHANGELOG.md`
- `branch-version.yaml`
- 이전 `config-usage-inventory.json`

장기적으로 `sdlc/design/contracts`를 `sdlc/contracts`로 옮기면 의도가 가장 명확하지만 참조 범위가 넓으므로 별도 major cleanup으로 수행한다.

## 6. `sdlc/scripts` 분류

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
```

### PROJECT_REQUIRED — 기본 Customer Projection을 사용하는 현재 Scaffold

```text
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

### FRAMEWORK_ONLY — Project Scaffold에서 제외해야 함

```text
build_project_scaffold.py                 # Framework → Project 배포 도구; 배포된 Project 자체에는 불필요
generate_tailoring_profile_comparison.py  # Tailoring 구조 비교
empirical_pilot_runtime.py
run_agent_repeatability_experiment.py
run_work_repeatability_experiment.py
run_greenfield_e2e_pilot.py
validate_public_brownfield_pilot.py
validate_empirical_pilot_evidence.py
validate_canonical_projection_invariant.py
validate_document_experience.py
validate_harness_structure.py
normalize_mermaid.py                       # Framework docs/CI quality
sync_worklist.py                           # Framework 관리 Worklist
```

### COMPATIBILITY_ONLY — 아직 삭제 금지

```text
runtime_config_v19.py
```

`runtime_config_v19.py`는 현재 business rule 구현체가 아니라 `project_config.py`를 re-export하는 compatibility wrapper지만 여러 기존 Runtime import가 남아 있어 즉시 삭제하면 안 된다. 후속 단계에서 import를 `project_config.py`로 직접 전환한 뒤 제거한다.

## 7. `sdlc/samples/tailoring` vs `sdlc/tailoring/standard`

두 폴더의 목적은 다르다.

```text
sdlc/tailoring/standard/
  = Runtime이 실제 Profile ID로 탐색하는 Framework Standard Profile

sdlc/custom/project/tailoring/
  = 프로젝트별 Custom Profile

sdlc/samples/tailoring/
  = 비교/교육/검증용 fixture. Runtime은 이 경로를 Profile search root로 사용하지 않음
```

즉 `.sdlc/project.yaml`에서 `profile: STANDARD_5`라고 쓰면 `sdlc/tailoring/standard/STANDARD_5.yaml`을 찾는다. `sdlc/samples/tailoring/project-standard-5.example.yaml`을 읽는 것이 아니다.

따라서 `sdlc/samples/tailoring`은 `framework/samples/tailoring`로 이동한다.

## 8. `docs/00_관리`

현재 두 의미가 충돌한다.

1. Runtime이 `요구사항_인입결과.md` 같은 **Project-generated 관리 View**를 생성하는 위치
2. Framework Repository가 Pilot 검증보고서/실증결과/전체작업목록을 커밋해 둔 위치

이 상태는 유지하지 않는 것이 맞다.

목표:

```text
docs/00_관리/          = Project-generated / PM-facing output만
framework/pilots/      = Pilot 결과
framework/validation/  = Framework 검증보고서
framework/management/  = Framework 자체 worklist
```

기존 `docs/00_관리`의 Framework 파일은 참조/바이너리 이동 영향 확인 후 순차 이동한다. Generated `요구사항_인입결과.md`는 Framework source repository에 고정 sample로 남기지 않는 것이 원칙이다.

## 9. `docs/00_시작` vs `sdlc/guides`

현재 Primary SoT는 `docs/00_시작`이다.

`sdlc/guides/01~04`는 이미 상세내용을 제거한 compatibility link일 뿐이며 신규 Project Scaffold의 필수파일도 아니다. 따라서 중복 경로를 유지할 이유가 없고 **삭제 대상**으로 분류한다.

`docs/00_시작`에서도 성격을 다시 나눈다.

- 프로젝트 사용 가이드: `START_HERE`, `02`, `03`, `04`, `05`, `07`
- Framework 배포/Scaffold 관리자 가이드: `01_STANDARD_SCAFFOLD`, `06_CUSTOM_SCAFFOLD` → 향후 `framework/guides/` 이동 후보

## 10. Default Tailoring Profile 분류

### 신규 기본

- `ENGINEERING_SDD_COMPACT`
- `CUSTOMER_STANDARD_3`
- `CUSTOMER_WATERFALL_FULL` (Customer Full 선택)
- `PM_STANDARD`

### Legacy Compatibility

- `STANDARD_3`
- `STANDARD_5`
- `STAGE_ORIENTED_FULL`

Legacy Profile과 `sdlc/templates/tailoring/standard/` Legacy template은 기본 Project Scaffold에서 제외하고 `--include-legacy-compatibility`일 때만 포함하는 것이 목표다.

## 11. 실제 Project Scaffold에 포함하지 않을 것

```text
framework/**
tests/**
.github/**
docs/99_파일럿/**
Framework repo에 커밋된 docs/00_관리 validation/pilot evidence
sdlc/design/baselines/**
sdlc/design/candidates/**
sdlc/design/reviews/**
sdlc/design/validations/**
Legacy comparison sample
Framework validation/pilot scripts
```

## 12. 정리 순서

1. `sdlc/guides` 삭제
2. `sdlc/samples/tailoring` → `framework/samples/tailoring` 이동
3. Project Scaffold에서 Framework 배포도구/Legacy 기본자산 제외 강화
4. `docs/00_관리`의 Pilot/Framework 관리파일 이동
5. `docs/99_파일럿` → `framework/pilots` 이동
6. `sdlc/design`의 History와 Runtime Contract 물리 분리 검토
7. `.cursor/skills` thin host adapter화 후 vendor-neutral Skill을 `sdlc/agent/skills`에 완성
8. `runtime_config_v19.py` import 제거 후 compatibility wrapper 삭제
