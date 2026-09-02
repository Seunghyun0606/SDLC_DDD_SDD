# AI-SDLC Harness

## 사용자 최초 진입점

**처음 Repository를 받은 PM / BA / 개발자 / Tester / 저수준 Agent는 먼저 [`sdlc/START_HERE.md`](START_HERE.md)만 읽는다.**

`design/`, Runtime YAML Template, Validation History는 일반 사용자의 시작 경로가 아니다.

## 사용자 Contract

- 진행: `python sdlc/scripts/ai_sdlc.py work <ID>`
- 변경: `python sdlc/scripts/ai_sdlc.py change <ID> "내용"`
- 조회: `python sdlc/scripts/ai_sdlc.py check <ID>`
- 초기화: `python sdlc/scripts/ai_sdlc.py init --project-root .`

내부 Lifecycle:

```text
INTAKE → DECOMPOSE → CLARIFY → PROCESS → DISCOVERY → IMPACT
→ DESIGN → PROGRAM → DEVELOPMENT → TEST → VERIFY → KNOWLEDGE_PROMOTION → COMPLETE
```

Stage Authority: `sdlc/config/stage-routing.yaml`

Human Artifact Authority: `sdlc/config/human-artifacts.yaml`

Provider Authority: 프로젝트가 선택한 Provider Registry

## Safety Invariants

- Human Truth != Source Evidence
- Candidate != Canonical
- Source Behavior != Business Truth
- Test Design != Runtime PASS
- Missing Provider != Success
- OPEN은 추정으로 닫지 않음
- Source write는 actual Revision/Ownership/Permission/Idempotency Guard 필요
- Shared Source는 Atomic Claim 필요
- Reverse Sync는 Confirmed Trace 중심 Candidate 생성 후 Human Review

## Production Candidate 기능

이 Branch는 P0 개선으로 다음 실행 primitive를 제공한다.

- `sdlc/adapters/production/git_worktree_source.py`
  - 실제 Git HEAD/branch 재조회
  - bounded read/search/diff
  - source.write 직전 revision 재검증
  - atomic local write lock
  - optional object hash guard
- `sdlc/adapters/production/subprocess_test.py`
  - exact argv allowlist
  - `shell=False`
  - actual exit/stdout/stderr evidence
- `sdlc/scripts/analyze_interface_contract.py`
  - OpenAPI/Swagger/AsyncAPI/WSDL
- `sdlc/scripts/manage_source_claims.py`
  - local filesystem atomic multi-agent claim
- `sdlc/scripts/render_human_artifact.py`
  - 8종 고객용 Human Artifact template
  - missing value → OPEN
  - provenance sidecar

이 구현들은 **Production Candidate**다. 실제 고객 Repository/Build/Test/Interface/DB를 사용한 E2E 검증이 끝나기 전 `Production Project Ready`라고 판정하지 않는다.

## 프로젝트 규모

- `LITE`: 사람 문서 최소화, Safety 내부 계약 유지
- `STANDARD`: 기본
- `ENTERPRISE`: 병렬개발/고위험/규제 시 추가 Guard

Config: `sdlc/config/artifact-profiles.yaml`

## Harness 검증

```bash
python sdlc/scripts/test_structural_redesign.py
python sdlc/scripts/test_p2_representative_slice.py
python sdlc/scripts/test_p0_production_readiness.py
```

Self-test PASS는 Harness primitive의 검증이며 실제 고객 Source 검증을 대체하지 않는다.

## Harness 관리자 문서

- `sdlc/guides/01_SDLC_전체가이드.md`
- `sdlc/guides/02_SKILL_사용가이드.md`
- `sdlc/guides/03_TEMPLATE_산출물가이드.md`
- `sdlc/guides/04_HARNESS_커스터마이징가이드.md`
- `sdlc/design/contracts/`
- `sdlc/design/validation/`

## P1 Operational Usability

P1부터 운영 Contract Authority는 `sdlc/config/contract-authority.yaml`에서 단일화한다.

추가 사용자 명령:

```bash
python sdlc/scripts/ai_sdlc.py sync-worklist --project-root .
python sdlc/scripts/ai_sdlc.py promote-knowledge <candidate.yaml> --project-root .
```

Project Decision은 `sdlc/config/project-decisions.yaml`이 정의하고 `init`이 `.ai-sdlc/project-decisions.yaml`을 생성한다. Overlay는 기존 Base key만 변경할 수 있으며 임의 key 생성, type 변경, stale base overwrite를 거부한다.
