# Harness 커스터마이징 가이드

> Primary Authority: `sdlc/config/contract-authority.yaml` → `overlay_schema` / `project_decisions` / Provider Runtime Authority

## Quick Start

프로젝트 시작 전에 모든 차이를 설정하지 않는다. Core Default + Project Profile로 먼저 시작하고, **실제 차이가 관찰된 항목만** Overlay로 추가한다.

우선순위는 `LOCAL_OVERRIDE > DOMAIN_OVERLAY > PROJECT_OVERLAY > PROJECT_PROFILE > PRESET > CORE_DEFAULT`다.

## 1. 무엇이 Config이고 무엇이 구현인가

| 변경 유형 | 방법 | Core 수정 |
|---|---|---|
| Project Mode / Artifact Profile | `ai-sdlc.yaml` | 불필요 |
| Provider Registry / Adapter Config 경로 | `ai-sdlc.yaml` | 불필요 |
| 프로젝트 경로 / 용어 Alias / Provider binding | `project-overlay.yaml` + `overlay-schema.yaml` | 불필요 |
| Worklist 한글 컬럼 | `worklist-columns.yaml` | 불필요 |
| Human Artifact 범위 | `artifact-profiles.yaml` | 불필요 |
| Stage Routing/Stage 자체 변경 | `stage-routing.yaml` Harness Config 변경 + 검증 | Project Overlay로 임의 변경하지 않음 |
| 신규 Source/Test/DB/API/Batch/Messaging 연동 | Adapter 구현 + Provider/Analyzer Registry 등록 | Core Router 수정 불필요가 원칙 |
| Truth/Test/Revision/Write Guard 약화 | 허용하지 않음 | Project Customization 대상 아님 |

“설정 가능”과 “Adapter 구현 필요”를 혼동하지 않는다.

## 2. Overlay 생성 조건

다음 경우에만 Overlay를 만든다.

- Core/Profile과 실제 프로젝트 구조가 충돌함
- 프로젝트 고유 경로/용어/Provider binding이 실제 작업에 필요함
- 공식 Project Standard 근거가 존재함

다음은 생성 사유가 아니다.

- 나중에 필요할 것 같음
- Sample/Pilot 값이 있었음
- 근거 없는 개인 선호

## 3. ACTIVE Overlay Fail-Closed 조건

Authority: `sdlc/config/overlay-schema.yaml`

ACTIVE Overlay는 다음을 만족해야 한다.

- Project Scope
- Trigger Reason
- 양의 Revision
- GIVEN/OBSERVED/CONFIRMED 근거와 Source/Evidence
- `activated_by`, `activated_at`
- 허용된 `target_key`
- 값 Type 일치
- `core_or_profile_value`가 현재 Base와 일치

Unknown key, Type 변경, stale base value, Safety/Truth invariant 대상은 DENY한다.

```bash
python sdlc/scripts/resolve_project_overlay.py \
  ai-sdlc.yaml \
  sdlc/custom/project/example.yaml \
  -o .ai-sdlc/resolved-project-config.yaml
```

## 4. Project Profile의 Overlay 확장 지점

`project-profile-user.yaml`은 다음 빈 Map을 제공한다.

```yaml
paths: {}
terminology:
  aliases: {}
provider_bindings: {}
```

`overlay-schema.yaml`이 허용한 Prefix만 이 Map 아래에 추가할 수 있다. 임의 중간 Map 생성은 허용하지 않는다.

## 5. Project Decision은 Overlay가 아니다

Greenfield 기술 선택은 `project-decisions.yaml` Authority를 사용한다.

- 개발언어 / Framework / Architecture
- Directory / Module
- DB / Transaction / API
- Error / Logging / Security
- Test / CI-CD
- 문서 / Naming / Coding / Branch

미확정은 OPEN으로 유지하며 관련 없는 분석을 막지 않는다. Side-effect에 필요한 결정만 해당 Action Scope를 Guard한다.

## 6. Provider / Adapter 확장

MCP/APM/Jira/DB Catalog/API Catalog/Batch/Scheduler/Messaging 등 외부 Tool 추가는 다음 순서를 따른다.

1. Capability를 정의한다.
2. Adapter를 구현한다.
3. Provider/Analyzer Registry에 등록한다.
4. unavailable/timeout/retry/evidence 상태를 구현한다.
5. Conformance/Synthetic/Real-source 검증 수준을 구분한다.

특정 Provider 규칙을 Core Router에 hard-code하지 않는다.

## 7. Knowledge와 Overlay 구분

- Overlay: Harness 동작/경로/표준/용어/Provider binding의 프로젝트 차이
- Knowledge: 업무규칙/프로세스/Data/Interface/운영 제약 등 재사용 사실

Source 관찰은 OBSERVED다. 명시적 Review 없이 Business Truth로 승격하지 않는다.

## 8. 검증

```bash
python sdlc/scripts/test_p1_usability_authority.py
python sdlc/scripts/test_structural_redesign.py
python sdlc/scripts/test_p0_production_readiness.py
```

Validation/Experiment/Design 문서는 검증·설계 이력이며 Runtime Authority가 아니다.
