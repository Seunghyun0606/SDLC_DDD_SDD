# v1.10 Template Role Boundary 및 Script 영향 점검

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0`

## 1. 정리 결과

Template과 Tailoring Profile의 역할을 다음과 같이 분리했다.

| 경로 | 역할 | 상태 |
|---|---|---|
| `sdlc/templates/semantic/` | SDLC Stage Semantic Template | PRIMARY |
| `sdlc/templates/engineering/` | Engineering Projection Template | PRIMARY |
| `sdlc/templates/customer/` | Customer Projection Template | PRIMARY |
| `sdlc/templates/management/` | PM/관리 View Template | PRIMARY |
| `sdlc/templates/br-intake/` | BR Intake 보조 Template | OPTIONAL |
| `sdlc/templates/tailoring/standard/` | 기존 3/5/Full 산출물 Template | COMPATIBILITY_ONLY |
| `sdlc/tailoring/standard/*.yaml` | Stage/Canonical → 최종 문서 조립 Profile | PROFILE, NOT TEMPLATE |
| `sdlc/templates/core` | `semantic`을 가리키는 경로 호환 alias | COMPATIBILITY_ONLY |

기존 `sdlc/templates/core/*.md` 본문은 `sdlc/templates/semantic/*.md`로 이동했고 두 위치에 실제 본문을 중복 보관하지 않는다.

## 2. Script 영향 점검

### 직접 영향 및 수정

#### `sdlc/scripts/run_work.py`

기존에는 Stage Template 경로를 `sdlc/templates/core/...`로 직접 생성했다.

현재는:

1. `sdlc/templates/semantic/`이 있으면 이를 우선 사용
2. 구형 프로젝트처럼 `semantic/`이 없으면 `sdlc/templates/core/`로 fallback

따라서 신규 v1.10 Project와 v1.9 호환 Project가 모두 실행 가능하다.

#### `sdlc/scripts/validate_document_experience.py`

Stage Template 품질 검증 대상을 `sdlc/templates/semantic/`으로 변경했다.

#### `sdlc/scripts/validate_harness_structure.py`

Stage Contract의 Template 구조 검증 대상을 `sdlc/templates/semantic/`으로 변경했다.

#### `sdlc/scripts/build_project_scaffold.py`

신규 Project에는 `semantic/` 실제 파일을 배포한다. `core`는 기존 Contract/외부 참조를 위해 compatibility alias로만 materialize한다. Symlink가 허용되지 않는 Host에서는 실행 호환을 위해 copy fallback을 사용한다.

### 직접 경로 영향 없음

#### `sdlc/scripts/tailored_work.py`

Engineering/Customer 최종 Template 경로를 Tailoring Profile에서 받아 사용하므로 Semantic 폴더 rename에 직접 의존하지 않는다.

#### `sdlc/scripts/run_change.py`

`run_work.py`의 공통 실행 Runtime을 재사용하며 `templates/core`를 직접 조립하지 않는다.

#### `sdlc/scripts/customer_projection_runtime.py`

Customer Profile의 `template` 값을 사용하므로 `semantic/`과 독립이다.

#### `sdlc/scripts/tailoring_runtime.py`

Profile의 Template 경로를 해석하는 역할이며 `semantic` Stage Template 이름에 직접 의존하지 않는다.

## 3. Profile 영향

신규 기본 Profile은 Stage Semantic Template을 최종 문서 Template으로 사용하지 않는다.

- `ENGINEERING_SDD_COMPACT` → `sdlc/templates/engineering/standard/*`
- `CUSTOMER_STANDARD_3` → `sdlc/templates/customer/standard/*`
- `CUSTOMER_WATERFALL_FULL` → Customer Template

Legacy Profile만 `sdlc/templates/tailoring/standard/*`를 사용한다.

즉 `semantic`은 **Stage 실행 의미 구조**, Tailoring Profile은 **조립 규칙**, Engineering/Customer Template은 **최종 Projection 표현 구조**로 구분된다.

## 4. Compatibility 경계

현재 `harness-package-contract.json`에는 v1.9 compatibility 때문에 일부 `sdlc/templates/core/...` 경로가 남아 있다. 이 경로는 Framework의 실제 Template 복제본이 아니라 `semantic` alias를 통해 해결된다.

따라서 현 단계에서 `core` alias 자체를 삭제하면 다음 호환 범위가 깨질 수 있다.

- v1.9 minimum package contract
- OPEN Resolution workbook 기존 경로
- SOP extraction result 기존 경로
- 외부 프로젝트의 기존 `templates/core` 참조

alias 제거는 이 Contract/외부 경로 migration이 끝난 뒤 별도 Compatibility 제거 단계에서 수행한다.

## 5. 자동 회귀

`tests/test_template_role_boundary_v110.py`에서 다음을 고정한다.

- `semantic`이 실제 원본 디렉터리임
- Framework의 `core`는 symlink alias임
- `run_work.py`가 semantic 우선 + core fallback임
- Framework Validator는 semantic을 직접 검증함
- Engineering/Customer 기본 Profile이 semantic을 최종 Projection Template으로 오용하지 않음
- Legacy Profile은 별도 Tailoring Template 영역을 사용함
- Template README에 역할 경계가 명시됨

최종 CI 결과는 본 변경 최종 Head의 GitHub Actions 결과를 근거로 별도 판정한다.
