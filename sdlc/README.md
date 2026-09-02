# AI-SDLC Harness

## 사용자 최초 진입점

**처음 Repository를 받은 PM / BA / 개발자 / Tester / 저수준 Agent는 먼저 [`sdlc/START_HERE.md`](START_HERE.md)만 읽는다.**

`design/`, Runtime YAML Template, Validation History는 일반 사용자의 시작 경로가 아니다.

## 사용자 Contract

- 초기화: `python sdlc/scripts/ai_sdlc.py init --project-root .`
- 요구사항 등록: `python sdlc/scripts/ai_sdlc.py intake-requirements <xlsx> --project-root .`
- 진행: `python sdlc/scripts/ai_sdlc.py work <ID> --project-root .`
- 변경: `python sdlc/scripts/ai_sdlc.py change <ID> "내용" --project-root .`
- 조회: `python sdlc/scripts/ai_sdlc.py check <ID> --project-root .`
- 작업목록 동기화: `python sdlc/scripts/ai_sdlc.py sync-worklist --project-root .`

내부 Lifecycle:

```text
INTAKE → DECOMPOSE → CLARIFY → PROCESS → DISCOVERY → IMPACT
→ DESIGN → PROGRAM → DEVELOPMENT → TEST → VERIFY → KNOWLEDGE_PROMOTION → COMPLETE
```

Stage Authority: `sdlc/config/stage-routing.yaml`

Human Artifact Authority: `sdlc/config/human-artifacts.yaml`

Operational Authority Index: `sdlc/config/contract-authority.yaml`

## Safety Invariants

- Human Truth != Source Evidence
- Candidate != Canonical
- Source Behavior != Business Truth
- Test Design != Runtime PASS
- Missing Provider != Success
- OPEN은 추정으로 닫지 않음
- Source Requirement Intake != Canonical RQ
- Source write는 actual Revision/Ownership/Permission/Idempotency Guard 필요
- Shared Source는 Atomic Claim 필요
- Reverse Sync는 Confirmed Trace 중심 Candidate 생성 후 Human Review
- Controlled Pilot Ready != Production Ready

## P0 Production Candidate Primitive

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

## P1 Operational Usability

P1부터 운영 Contract Authority는 `sdlc/config/contract-authority.yaml`에서 단일화한다.

- Project Decision: `sdlc/config/project-decisions.yaml` → `.ai-sdlc/project-decisions.yaml`
- Schema-safe Overlay: 없는 key/type 변경/stale base overwrite DENY
- Canonical Worklist: `.ai-sdlc/worklist-canonical.yaml`
- Human View: `docs/00_관리/전체작업목록.md/.xlsx`
- Knowledge Promotion: human-confirmed review 없이는 Business 의미 자동 확정 금지

## P2 Integrated Scale-out

P2는 대표 Brownfield Slice에서 확인한 잔여 gap을 P0/P1 Runtime과 연결한다.

### Requirement Intake → Worklist

```bash
python sdlc/scripts/ai_sdlc.py intake-requirements \
  inputs/customer/requirements/요구사항목록.xlsx \
  --only-id REQ_TM_TE100 \
  --project-root .
```

Workbook 값은 `GIVEN`으로 Intake되고 `SOURCE_REQUIREMENT / CANDIDATE` Work Item으로 등록된다. Canonical RQ는 자동 생성하지 않는다. 동일 Source Requirement의 내용이 바뀌면 Review Required로 중단한다.

### Batch / Scheduler

`batch-scheduler` Analyzer는 다음을 bounded Source Evidence로 읽는다.

- crontab
- Spring `@Scheduled`
- Spring Batch signal
- Kubernetes CronJob
- GitHub Actions schedule

```bash
python sdlc/scripts/analyze_batch_scheduler.py . deploy/cronjob.yaml src/main/java/example/Job.java \
  -o .ai-sdlc/batch-scheduler-analysis.yaml
```

Live scheduler catalog, 실행이력, 동적 Runtime 관계는 관찰되지 않았다면 `OPEN`이다.

### Scale-out Gate

Authority: `sdlc/config/p2-scaleout-readiness.yaml`

Runtime: `sdlc/scripts/assess_scaleout_readiness.py`

P0/P1 상태, 필수 Analyzer, 필수 Runtime path, 실제 고객 E2E Evidence를 읽는다. CLI flag만으로 Production Ready를 만들 수 없다.

현재 Harness Self-test/CI가 허용하는 판정은 **Controlled Pilot Scale-out Candidate**다. 실제 고객 Source/Build/Test/DB-or-Interface/Reverse-Sync 검증이 없으면 `production_scaleout_ready=false`를 유지한다.

## 프로젝트 규모

- `LITE`: 사람 문서 최소화, Safety 내부 계약 유지
- `STANDARD`: 기본
- `ENTERPRISE`: 병렬개발/고위험/규제 시 추가 Guard

Config: `sdlc/config/artifact-profiles.yaml`

## Harness 검증

```bash
python sdlc/scripts/test_structural_redesign.py
python sdlc/scripts/test_p0_production_readiness.py
python sdlc/scripts/test_p1_usability_authority.py
python sdlc/scripts/test_p1_operational_usability.py
python sdlc/scripts/test_p2_representative_slice.py
python sdlc/scripts/test_p2_integrated_scaleout.py
```

Self-test PASS는 Harness primitive의 검증이며 실제 고객 Source 검증을 대체하지 않는다.

## Harness 관리자 문서

- `sdlc/guides/01_SDLC_전체가이드.md`
- `sdlc/guides/02_SKILL_사용가이드.md`
- `sdlc/guides/03_TEMPLATE_산출물가이드.md`
- `sdlc/guides/04_PROVIDER_RUNTIME_사용가이드.md`
- `sdlc/guides/05_HARNESS_커스터마이징가이드.md`
- `sdlc/guides/README.md`
- `sdlc/design/README.md`
