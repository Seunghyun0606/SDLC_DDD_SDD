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

전체 Authority Index: `sdlc/config/contract-authority.yaml`

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

P0/P1 Branch는 실제 Git Revision 기반 Source Adapter, actual subprocess Test Adapter, Interface Analyzer, Atomic Claim, 8종 Human Artifact renderer, Project Decision Registry, Worklist MD↔XLSX sync, Reviewed Knowledge Promotion을 제공한다.

이 구현들은 **Production Candidate**다. 실제 고객 Repository/Build/Test/Interface/DB를 사용한 E2E 검증이 끝나기 전 `Production Project Ready`라고 판정하지 않는다.

## 프로젝트 규모

- `LITE`: 사람 문서 최소화, Safety 내부 계약 유지
- `STANDARD`: 기본
- `ENTERPRISE`: 병렬개발/고위험/규제 시 추가 Guard

Config: `sdlc/config/artifact-profiles.yaml`

## 사용자 명령

```bash
python sdlc/scripts/ai_sdlc.py init --project-root .
python sdlc/scripts/ai_sdlc.py work <ID> --project-root .
python sdlc/scripts/ai_sdlc.py change <ID> "내용" --project-root .
python sdlc/scripts/ai_sdlc.py check <ID> --project-root .
python sdlc/scripts/ai_sdlc.py sync-worklist --project-root .
python sdlc/scripts/ai_sdlc.py promote-knowledge <candidate.yaml> --project-root .
```

## Harness 검증

```bash
python sdlc/scripts/test_p0_production_readiness.py
python sdlc/scripts/test_p1_foundation.py
python sdlc/scripts/test_p1_operational_usability.py
python sdlc/scripts/validate_contract_authority.py sdlc/config/contract-authority.yaml --repo-root .
```

Self-test PASS는 Harness primitive의 검증이며 실제 고객 Source 검증을 대체하지 않는다.

## Harness 관리자 문서

- `sdlc/guides/01_SDLC_전체가이드.md`
- `sdlc/guides/02_SKILL_사용가이드.md`
- `sdlc/guides/03_TEMPLATE_산출물가이드.md`
- `sdlc/guides/04_PROVIDER_RUNTIME_사용가이드.md`
- `sdlc/guides/05_HARNESS_커스터마이징가이드.md`
- `sdlc/design/README.md`

`guides/`와 `design/`은 설명/이력 영역이며 Runtime Machine Authority가 아니다.
