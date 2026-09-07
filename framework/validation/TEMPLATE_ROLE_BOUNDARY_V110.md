# v1.10 Template Role Boundary 및 Script 영향 점검

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0`

## 1. 정리 결과

Template과 Tailoring Profile의 역할을 다음과 같이 분리한다.

| 경로 | 역할 | 상태 |
|---|---|---|
| `sdlc/templates/semantic/` | SDLC Stage Semantic Template | PRIMARY |
| `sdlc/templates/engineering/` | Engineering Projection Template | PRIMARY |
| `sdlc/templates/customer/` | Customer Projection Template | PRIMARY |
| `sdlc/templates/management/` | PM/관리 View Template | PRIMARY |
| `sdlc/templates/br-intake/` | BR Intake 보조 Template | OPTIONAL |
| `sdlc/templates/tailoring/standard/` | 기존 3/5/Full 산출물 Template | LEGACY_FORMAL_PROJECTION |
| `sdlc/tailoring/standard/*.yaml` | Stage/Canonical → 최종 문서 조립 Profile | PROFILE, NOT TEMPLATE |

v1.10에서는 Stage Semantic Template 원본을 `sdlc/templates/semantic/*.md`에만 보관한다. 별도 alias/symlink 디렉터리는 두지 않는다.

## 2. Script 영향 점검

### 직접 영향 및 수정

#### `sdlc/scripts/run_work.py`
Stage Template 경로는 `sdlc/templates/semantic/...`만 사용한다. 구 경로 fallback은 제거했다.

#### `sdlc/scripts/validate_document_experience.py`
Stage Template 품질 검증 대상을 `sdlc/templates/semantic/`으로 고정한다.

#### `sdlc/scripts/validate_harness_structure.py`
Stage Contract의 Template 구조 검증 대상을 `sdlc/templates/semantic/`으로 고정한다.

#### `sdlc/scripts/build_project_scaffold.py`
신규 Project에는 `semantic/` 실제 파일만 배포한다. 별도 Template alias/symlink는 materialize하지 않는다.

#### `sdlc/scripts/resolve_overlay.py`
Overlay의 기본 Stage Template root를 `sdlc/templates/semantic/`으로 사용한다.

### 직접 경로 영향 없음

#### `sdlc/scripts/tailored_work.py`
Engineering/Customer 최종 Template 경로를 Tailoring Profile에서 받아 사용하므로 Semantic 폴더명에 직접 결합하지 않는다.

#### `sdlc/scripts/run_change.py`
`run_work.py` 공통 Runtime을 재사용한다.

#### `sdlc/scripts/customer_projection_runtime.py`
Customer Profile의 `template` 값을 사용하므로 Semantic Stage Template과 독립이다.

#### `sdlc/scripts/tailoring_runtime.py`
Profile의 Projection Template 경로를 해석하며 Semantic Stage Template을 최종 산출물 Template으로 사용하지 않는다.

## 3. Profile 영향

신규 기본 Profile은 Stage Semantic Template을 최종 문서 Template으로 사용하지 않는다.

- `ENGINEERING_SDD_COMPACT` → `sdlc/templates/engineering/standard/*`
- `CUSTOMER_STANDARD_3` → `sdlc/templates/customer/standard/*`
- `CUSTOMER_WATERFALL_FULL` → Customer Projection Template

Legacy/Formal Profile만 `sdlc/templates/tailoring/standard/*`를 사용한다.

즉 `semantic`은 **Stage 실행 의미 구조**, Tailoring Profile은 **조립 규칙**, Engineering/Customer Template은 **최종 Projection 표현 구조**다.

## 4. Compatibility 경계

v1.9의 의미/기능은 v1.10에 포함하되 Template 경로 compatibility alias는 유지하지 않는다.

- 기존 Project가 구 Template 경로를 직접 참조한다면 v1.10 적용 시 `sdlc/templates/semantic/...`으로 migration해야 한다.
- Runtime/Contract/Test/Guide는 구 경로를 사용하지 않는다.
- `STANDARD_3`, `STANDARD_5`, `STAGE_ORIENTED_FULL`은 경로 alias가 아니라 별도의 Legacy/Formal Projection Profile로 유지한다.

## 5. 자동 회귀

`tests/test_template_role_boundary_v110.py`에서 다음을 고정한다.

- `semantic`이 유일한 Stage Template 원본 디렉터리임
- 구 Stage Template alias/symlink가 존재하지 않음
- Repository에 구 Stage Template 경로 참조가 없음
- `run_work.py`가 semantic-only임
- Framework Validator가 semantic을 직접 검증함
- Engineering/Customer 기본 Profile이 semantic을 최종 Projection Template으로 오용하지 않음
- Legacy/Formal Profile은 별도 Tailoring Template 영역을 사용함
- Template README에 역할 경계가 명시됨

최종 CI 결과는 본 변경 최종 Head의 GitHub Actions 결과를 근거로 판정한다.
