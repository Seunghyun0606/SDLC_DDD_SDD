# v1.10 Repository Asset Inventory

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0`

이 문서는 Repository 자산을 **실제 Project 배포 대상**과 **Framework 개발/검증/설계이력 자산**으로 구분하는 현재 기준이다.

## 1. 분류값

- `PROJECT_REQUIRED`: 기본 Project Scaffold에 포함되고 기본 실행 경로에 필요한 자산
- `PROJECT_BUNDLED_OPTIONAL`: 기본 Scaffold에 동봉되지만 해당 기능/Profile을 선택할 때만 사용하는 자산
- `PROJECT_OPTIONAL`: 별도 Extension/고객/프로젝트 선택 시에만 배포하거나 추가하는 자산
- `FRAMEWORK_ONLY`: Framework 개발, Test, Pilot, Validation, Sample, Design History
- `COMPATIBILITY_ONLY`: 신규 기준은 아니지만 기존 참조 때문에 남은 호환 자산
- `GENERATED`: 프로젝트 실행 중 생성되는 상태/문서
- `ARCHIVED`: 현재 SoT가 아닌 과거 metadata/inventory snapshot

`PROJECT_BUNDLED_OPTIONAL`은 “기본 기능으로 반드시 실행한다”는 뜻이 아니다. Public Harness command와 표준 선택 Profile을 별도 설치 절차 없이 사용할 수 있도록 파일만 기본 Scaffold에 동봉한다.

## 2. 최상위 경계

| 경로 | 판정 | 현재 역할 |
|---|---|---|
| `.cursor/rules/` | PROJECT_REQUIRED(Cursor) | Cursor host rule adapter |
| `.cursor/skills/` | PROJECT_REQUIRED(Cursor) | Cursor host skill adapter |
| `sdlc/agent/skills/` | PROJECT_REQUIRED | Vendor-neutral Agent Core skill |
| `sdlc/config/` | MIXED | Runtime policy + bundled/optional config + compatibility debt |
| `sdlc/custom/` | PROJECT_OPTIONAL | Project/Domain customization |
| `sdlc/design/contracts/` | PROJECT_REQUIRED + OPTIONAL | Runtime/validator executable contract |
| `sdlc/scripts/` | MIXED | Project Runtime + bundled optional command support + Extension + Framework utility |
| `sdlc/starter-kits/` | PROJECT_REQUIRED | Greenfield/Brownfield starter assets |
| `sdlc/tailoring/standard/` | PROJECT_REQUIRED + BUNDLED_OPTIONAL + COMPATIBILITY | 신규 기본 Profile + 선택 표준 Profile + Legacy/Formal Profile |
| `sdlc/templates/semantic/` | PROJECT_REQUIRED | Stage Semantic Template 유일 원본 |
| `sdlc/templates/engineering/` | PROJECT_REQUIRED | Engineering Projection Template |
| `sdlc/templates/customer/` | PROJECT_REQUIRED/BUNDLED_OPTIONAL | Customer Projection Template |
| `sdlc/templates/management/` | PROJECT_REQUIRED | PM/관리 View Template |
| `sdlc/templates/tailoring/standard/` | COMPATIBILITY_ONLY | Legacy/Formal 3/5/Full Projection Template |
| `sdlc/runtime/` | GENERATED | 실행 중 Machine State |
| `docs/00_시작/` | PROJECT_REQUIRED | 사용자 Guide Primary SoT |
| `docs/00_관리/` | GENERATED | Project-generated PM/User View |
| `framework/` | FRAMEWORK_ONLY | Framework 개발/검증/설계이력 경계 |
| `tests/` | FRAMEWORK_ONLY | Framework regression/contract/pilot tests |
| `.github/` | FRAMEWORK_ONLY | Framework CI |

## 3. Framework 물리 구조

```text
framework/
├─ README.md
├─ ASSET_INVENTORY_V110.md
├─ design/
│  ├─ README.md
│  ├─ branch-version.yaml       # ACTIVE v1.10 metadata
│  ├─ CHANGELOG.md              # ACTIVE version history
│  ├─ current/                  # ACTIVE design summary
│  ├─ baselines/                # HISTORICAL
│  ├─ candidates/               # HISTORICAL
│  ├─ reviews/                  # HISTORICAL
│  ├─ validations/              # HISTORICAL design-era validation
│  └─ session/                  # ACTIVE session governance
├─ archive/                     # ARCHIVED superseded metadata/inventory
├─ management/                  # Framework worklist/관리자료
├─ pilots/                      # Pilot/history
├─ samples/                     # 비교/교육/검증 fixture
└─ validation/                  # Current validation reports + assets
```

## 4. Design / Archive Governance

### `framework/design`

현재 설계와 설계 진화 이력을 보관한다.

현재 설계 SoT:

1. `framework/design/branch-version.yaml`
2. `framework/design/current/V110_PROJECTION_SEPARATION_DESIGN.md`
3. `framework/design/CHANGELOG.md`
4. `framework/ASSET_INVENTORY_V110.md`
5. `framework/validation/*V110*.md`

`baselines/`, `candidates/`, `reviews/`, `validations/`의 과거 문서는 현재 Runtime SoT가 아니다.

### `framework/archive`

현재 경로에 남아 있으면 최신 상태로 오해되는 과거 active metadata/inventory/migration snapshot만 보관한다.

- `config-usage-inventory-v19.json`: v1.9 Config inventory snapshot
- `design-metadata/branch-version-v1.9.0.yaml`: v1.9 active branch metadata snapshot

Archive 목록과 대체 SoT는 `framework/archive/INDEX.md`에서 관리한다.

## 5. 완료된 물리 정리

- `sdlc/design/baselines|candidates|reviews|session|validations` → `framework/design/`
- `docs/99_파일럿` → `framework/pilots/history/`
- Framework validation/pilot/worklist/sample → `framework/validation|pilots|management|samples`
- `sdlc/samples` 비교/교육 fixture → `framework/samples/`
- `sdlc/validation` 실내용 → `framework/validation/assets/`
- 중복 `sdlc/guides` 제거
- Stage Template 원본 `sdlc/templates/semantic/`으로 통합
- 구 Stage Template alias/symlink/fallback 제거

## 6. Compatibility Debt

Stage Semantic Template에는 compatibility alias가 없다.

별도 기능 영역에는 다음 기존 compatibility debt가 남아 있다.

- `sdlc/validation`: 과거 validation asset 참조 경로
- `sdlc/config/customer-document-profile.example.json`: Customer config 이름 전환 전 참조 경로
- `runtime_config_v19.py`: v1.9 config thin wrapper
- `documents.internal.profile`: migration input only
- `STANDARD_3`, `STANDARD_5`, `STAGE_ORIENTED_FULL`: Legacy/Formal Projection Profile

신규 Runtime/Guide/Project Scaffold는 정식 v1.10 경로와 개념을 사용한다.

## 7. `sdlc/config` 판정

### PROJECT_REQUIRED

- `change-execution-policy.json`
- `program-spec-readiness.json`
- `customer-document-profile.json`

### PROJECT_BUNDLED_OPTIONAL

- `architecture-rules.json`: `arch-check`를 선택할 때 사용하는 기본 규칙. Standard Scaffold에는 동봉되지만 일반 `/work`의 필수 입력은 아니다.

### PROJECT_OPTIONAL

- `impact-adapter-profile.example.yaml`
- `requirement-intake-columns.example.yaml`
- `open-resolution-profile.example.yaml`
- `terminology-profile.example.json`
- `br-intake-profile.example.json`

### COMPATIBILITY / FRAMEWORK REFERENCE

- `project-profile.example.yaml`
- `source-profile.example.yaml`
- `project.example.yaml`
- repeatability/overlay/worklist 계열 config

## 8. Script 분류

### PROJECT_REQUIRED

`harness.py`, `bootstrap_project.py`, `project_config.py`, `runtime_config.py`, `intake_explainable.py`, `intake_requirements.py`, `import_requirements.py`, `tailored_work.py`, `interactive_work.py`, `work_handoff.py`, `run_work.py`, `review_work.py`, `interactive_change.py`, `run_change.py`, `change_execution_runtime.py`, `tailored_check.py`, `run_check.py`, `tailoring_runtime.py`, `apply_canonical_delta.py`, `projection_lifecycle_runtime.py`, `validate_agent_stage_result.py`, `validate_program_spec.py`, `delivery_status_runtime.py`, `capture_customer_decision.py`, `customer_projection_runtime.py`, `render_customer_document.py`.

### PROJECT_BUNDLED_OPTIONAL

Standard Scaffold의 Public Harness command를 별도 설치 없이 사용할 수 있도록 동봉하지만 실행은 선택 사항이다.

- `component_state_runtime.py` — `component`
- `impact_learning_runtime.py` — `impact-history`
- `unexpected_discovery_runtime.py` — `discover-impact`
- `architecture_check.py` — `arch-check`
- `sdlc_metrics_runtime.py` — `metrics`

### PROJECT_OPTIONAL

별도 Brownfield/Document ingest/외부도구/Promotion 기능을 사용할 때 추가하는 자산이다.

`build_reverse_inputs.py`, `detect_source_drift.py`, `run_source_reverse_check.py`, `generate_program_spec_reverse_candidate.py`, `extract_document_evidence.py`, `normalize_external_evidence.py`, `resolve_overlay.py`, `run_knowledge_promotion.py`.

### FRAMEWORK_ONLY

`build_project_scaffold.py`, `generate_tailoring_profile_comparison.py`, `empirical_pilot_runtime.py`, `run_agent_repeatability_experiment.py`, `run_work_repeatability_experiment.py`, `run_greenfield_e2e_pilot.py`, `validate_public_brownfield_pilot.py`, `validate_empirical_pilot_evidence.py`, `validate_canonical_projection_invariant.py`, `validate_document_experience.py`, `validate_harness_structure.py`, `normalize_mermaid.py`, `sync_worklist.py`.

### COMPATIBILITY_ONLY

- `runtime_config_v19.py`

## 9. Tailoring / Template 경계

신규 기본:

- Engineering: `ENGINEERING_SDD_COMPACT`
- Customer: `CUSTOMER_STANDARD_3`
- PM: `PM_STANDARD`

기본 Scaffold 동봉 선택형:

- Customer Full: `CUSTOMER_WATERFALL_FULL` — Config로 선택할 수 있도록 동봉하지만 기본 Profile은 아니다.

Legacy/Formal:

- `STANDARD_3`
- `STANDARD_5`
- `STAGE_ORIENTED_FULL`
- `sdlc/templates/tailoring/standard/`

Stage Semantic Template과 Legacy/Formal Projection Template을 같은 것으로 취급하지 않는다.

## 10. Guide SoT

현재 핵심 Guide:

- `START_HERE.md`
- `02_PROJECT_설정가이드.md`
- `03_TAILORING_설정가이드.md`
- `04_TEMPLATE_및_산출물_가이드.md`
- `05_이해관계자별_작업가이드.md`
- `07_BROWNFIELD_SSOT_현행화가이드.md`
- `11_INPUT_자료_준비가이드.md`

`01_STANDARD_SCAFFOLD_사용가이드.md`, `06_CUSTOM_SCAFFOLD_적용가이드.md`는 Framework compatibility notice이며 신규 Project Scaffold에서 제외한다.

## 11. Project Scaffold 배포 규칙

기본 Project Scaffold에는 `PROJECT_REQUIRED`와 `PROJECT_BUNDLED_OPTIONAL`을 포함한다. `PROJECT_BUNDLED_OPTIONAL`은 파일이 동봉될 뿐 기능 활성화를 강제하지 않는다.

기본 Project Scaffold에는 다음을 넣지 않는다.

```text
framework/**
tests/**
.github/**
Framework validation/pilot/sample/design/archive assets
sdlc/validation compatibility path
sdlc/guides removed path
Legacy STANDARD_3/STANDARD_5/STAGE_ORIENTED_FULL
Legacy tailoring templates
Framework distribution tool 자체
별도 Brownfield/Document-ingest/External-tool Extension
```

## 12. Generated 경계

```text
sdlc/runtime/**
sdlc/canonical/store.json
docs/00_관리/**
docs/10_engineering/**
docs/20_customer/** 또는 Customer Profile output root
```

## 13. v1.10 판정

- Framework-only 자산 물리 분리: 완료
- Stage Semantic Template 용어/경로 통합: 완료
- Guide SoT 현행화: 완료
- Design active metadata v1.10 갱신: 완료
- Design current/history 역할 문서화: 완료
- v1.9 active metadata Archive 보존: 완료
- Archive index/governance 추가: 완료
- Standard Scaffold의 동봉 선택형 기능과 별도 Extension 분류 명시: 완료
- 남은 compatibility debt는 별도 기능 영역의 명시적 항목으로 제한
- 최신 자동 회귀 결과는 `framework/validation/LATEST_COMMIT_REVIEW_V110.md`와 PR #67 current-head CI를 근거로 판정
