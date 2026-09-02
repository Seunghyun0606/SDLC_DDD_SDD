# AI-SDLC START HERE

이 문서는 **프로젝트 참여자의 단일 최초 진입점**이다. `sdlc/design/`, Runtime YAML Template, Validation History는 처음 읽지 않는다.

## 1. 가장 먼저 준비할 것

### 공통 필수
- 고객 요구사항 문서: XLSX/MD 등
- 프로젝트명과 목적
- 고객 정책/업무 배경 문서가 있으면 함께 준비

### Greenfield 추가
- 회사/고객의 기술·보안·운영 표준
- 기술 결정을 승인할 담당자

### Brownfield 추가
- 기존 Source Repository
- 기준 Commit/Revision
- Build 명령
- Test 명령
- 가능하면 DB Schema/Table/Column, Procedure, Batch/Scheduler, API/Interface 문서

Source에 구현되어 있다는 이유만으로 Business Rule로 확정하지 않는다.

## 2. 고객 파일 배치

권장 위치:

```text
inputs/customer/requirements/   # 요구사항
inputs/customer/policy/         # 정책/SOP
inputs/customer/process/        # 업무 Process
inputs/customer/existing-docs/  # 기존 설계/운영 문서
```

Brownfield Source는 이 폴더로 복사할 필요가 없다. Harness가 들어 있는 실제 Git Repository 자체를 Source Root로 사용하거나 Provider에 별도 Source Root를 지정한다.

`.ai-sdlc/`는 Runtime 생성 영역이며 사람이 직접 편집하지 않는 것을 원칙으로 한다.

## 3. 첫 명령

```bash
python sdlc/scripts/ai_sdlc.py init --project-root .
```

`ai-sdlc.yaml`이 없으면 Template를 생성한다. 프로젝트명/Mode/Profile을 확인한 뒤 다시 실행한다.

기본 Registry는 안전하게 Source/Test Provider가 `UNCONFIGURED`다. 따라서 처음부터 실제 Source/Test 성공을 주장하지 않는다.

### Brownfield에서 실제 Local Git/Test를 연결할 때

```bash
cp sdlc/config/adapter-config.local.example.yaml ai-sdlc-adapters.yaml
```

`ai-sdlc-adapters.yaml`의 `root`, `cwd`, `allowed_commands`를 실제 프로젝트에 맞게 수정한 뒤:

```bash
python sdlc/scripts/ai_sdlc.py init \
  --project-root . \
  --registry sdlc/config/provider-registry.local-production.yaml \
  --adapter-config ai-sdlc-adapters.yaml
```

Production Candidate Adapter를 사용하더라도 **실제 고객 Source E2E 검증 전에는 Production Ready라고 부르지 않는다.**

## 4. 요구사항 Excel Intake

예:

```bash
python sdlc/scripts/intake_requirements_xlsx.py \
  inputs/customer/requirements/요구사항목록.xlsx \
  --only-id REQ_TM_TE100 \
  -o .ai-sdlc/requirement-intake-REQ_TM_TE100.yaml
```

Workbook 값은 `GIVEN`으로 보존하며 Canonical ID를 자동 확정하지 않는다.

## 5. 첫 Prompt

Bootstrap 결과의 Mode에 따라 그대로 사용한다.

- Greenfield: `sdlc/starter/prompts/greenfield-first-prompt.md`
- Brownfield: `sdlc/starter/prompts/brownfield-first-prompt.md`

## 6. 사용자 명령

```bash
python sdlc/scripts/ai_sdlc.py work <요구사항ID> --project-root .
python sdlc/scripts/ai_sdlc.py check <요구사항ID> --project-root .
python sdlc/scripts/ai_sdlc.py change <요구사항ID> "변경 내용" --project-root .
```

사용자는 내부 Stage Skill을 직접 골라 실행하지 않는다. `work`가 Stage Router를 통해 Skill/Capability/출력 계획을 결정한다.

Side Effect는 자동 실행하지 않는다. Source write/Test execute/Canonical publish는 Stage Pack에 명시적 요청과 Guard Proof가 있을 때만 실행 계약을 만든다.

## 7. 사람이 보는 산출물과 Runtime Artifact

### 고객/팀이 검토하는 문서

| 단계 | Human Artifact |
|---|---|
| INTAKE | 요구사항 |
| DECOMPOSE/CLARIFY | 요구분석 |
| PROCESS | 프로세스분석 |
| IMPACT | 영향분석 |
| DESIGN | 기능설계 |
| PROGRAM | 프로그램설계 |
| DEVELOPMENT | 구현결과 |
| VERIFY | 테스트·검증결과 |

Authority: `sdlc/config/human-artifacts.yaml`

문서 생성:

```bash
python sdlc/scripts/render_human_artifact.py \
  요구사항 \
  sdlc/templates/human-artifact-context.yaml \
  -o docs/REQ-0001_업무_요구사항.md
```

누락 값은 `OPEN`으로 남고 `.meta.yaml`에 누락 Field/Revision/Evidence가 기록된다.

### Agent/Runtime 내부 파일

- `.ai-sdlc/project-bootstrap.yaml`
- `.ai-sdlc/artifact-plan.yaml`
- Stage Input Pack / Stage Execution Plan
- Provider Request/Response / Invocation Journal
- Source Analysis Result
- Reverse Sync Candidate

이 파일들은 고객 산출물이 아니다.

## 8. Brownfield Source 분석

1. Git Revision을 고정한다.
2. Bounded Inventory를 수행한다.
3. Requirement와 관련된 파일만 Analyzer로 전달한다.
4. Java/SQL heuristic 결과는 `OBSERVED/INFERRED` Evidence다.
5. OpenAPI/AsyncAPI/WSDL은 `interface-contract` Analyzer로 분석한다.
6. 지원되지 않는 Batch/Scheduler/동적 Runtime 관계는 `OPEN`으로 남긴다.

```bash
python sdlc/scripts/analyze_interface_contract.py . \
  --file contracts/openapi.yaml \
  -o .ai-sdlc/interface-analysis.yaml
```

## 9. Source 수정 전 필수 절차

1. 실제 Git HEAD 확인
2. Agent Branch/Parent Change Branch 확인
3. Atomic Claim 획득
4. Revision/Ownership Guard 실행
5. Provider write에서 HEAD를 다시 확인
6. 가능하면 `expected_object_sha256`까지 확인
7. Write 후 Hash 재검증

Atomic claim 예:

```bash
REV=$(git rev-parse HEAD)
python sdlc/scripts/manage_source_claims.py acquire \
  --project-root . \
  --claim-id CLAIM-REQ-0001-TASK-01 \
  --agent-id agent-a \
  --expected-revision "$REV" \
  --expected-branch "$(git branch --show-current)" \
  --path 'src/main/java/example/Service.java'
```

두 번째 Agent가 같은 경로/Program을 Claim하면 DENY된다.

## 10. Test / Verify

`test.execute`는 allowlist에 등록된 argv만 `shell=False`로 실행한다. Exit code와 실제 stdout/stderr Evidence를 기록한다.

- Test 설계만 존재 → PASS 아님
- Test 미실행 → PASS 아님
- Provider OK + Test exit code non-zero → Test `FAILED`
- Actual Runtime Evidence + 모든 Required Test PASS + 다른 Verification 조건 만족 시에만 `VERIFIED_PASS`

## 11. Source → 문서 Reverse Sync

Source 변경은 먼저 `Source Change Evidence`와 `Reverse Sync Candidate`를 만든다.

- Confirmed Graph 직접 관계만 자동 STALE 후보
- RQ/FR/BR/PROC/FTR/AC는 Source 변경만으로 자동 overwrite 금지
- Human Review 이후 Canonical/문서를 갱신

## 12. 프로젝트 규모 선택

`ai-sdlc.yaml`:

```yaml
artifacts:
  profile: LITE   # 또는 STANDARD / ENTERPRISE
```

LITE는 Human 문서를 줄일 수 있지만 Revision/Truth/Test/OPEN/Provider Guard를 제거하지 않는다.

## 13. 막혔을 때 볼 곳

1. `.ai-sdlc/*status*.yaml`
2. `.ai-sdlc/*guard*.yaml`
3. `.ai-sdlc/*open*.yaml`
4. `sdlc/README.md`
5. Harness 관리자만 `sdlc/guides/`, `sdlc/config/`, `sdlc/design/` 확인

## 14. Harness 자체 P0 Self-Test

```bash
python sdlc/scripts/test_p0_production_readiness.py
```

이 테스트는 임시 **실제 Git Worktree + 실제 subprocess**를 사용하지만 고객 Source 검증은 아니다. 출력의 `real_customer_source_validated: false`를 임의로 바꾸지 않는다.

## 15. Project Decision Registry

기술/운영 결정의 Primary Authority는 `sdlc/config/project-decisions.yaml`이다. `init` 실행 시 `.ai-sdlc/project-decisions.yaml`이 생성된다.

- `OPEN`: 아직 미확정. 관련 없는 분석은 계속 가능
- `CANDIDATE`: 후보값이 있으나 확정 아님
- `CONFIRMED`: 값 + 결정자/Owner + 근거 필요
- Source 관찰만으로 `CONFIRMED` 자동 승격 금지

특히 Greenfield의 개발언어, Framework, Architecture, Directory/Module, DB, Transaction, API, Error, Logging, Security, Test, CI/CD, 문서 규칙, Naming/Coding, Branch 전략을 한 Registry에서 확인한다.

```bash
python sdlc/scripts/validate_project_decisions.py .ai-sdlc/project-decisions.yaml
```

## 16. 전체작업목록 MD ↔ XLSX

다음 두 파일은 동일한 Canonical Work Item의 Human View다.

- `docs/00_관리/전체작업목록.md`
- `docs/00_관리/전체작업목록.xlsx`

Canonical Runtime Authority는 `.ai-sdlc/worklist-canonical.yaml`이다.

```bash
python sdlc/scripts/ai_sdlc.py sync-worklist --project-root .
```

기존 항목을 수정하면 `변경버전`을 올린다. 같은 버전에서 MD/XLSX/Canonical 값이 다르면 `SYNC_CONFLICT`로 중지하며 어느 쪽도 조용히 덮어쓰지 않는다.

## 17. Knowledge Promotion

Source/Agent에서 얻은 지식은 바로 Canonical Business Truth가 아니다.

`CANDIDATE → Review → PROMOTED` 절차를 사용한다.

```bash
python sdlc/scripts/ai_sdlc.py promote-knowledge .ai-sdlc/knowledge-candidate.yaml --project-root .
```

Business Rule/Process/Data/Interface 의미가 `OBSERVED/INFERRED`이면 Source/Agent 결과만으로 Promotion하지 않는다. Review에 `decision: CONFIRM`, `human_confirmation: true`, 검토자/시각/근거가 명시된 경우에만 사람 확인 사실을 근거로 `CONFIRMED`로 전환한 뒤 Promotion한다. `OPEN`은 Promotion할 수 없고, Promotion은 Canonical Publish를 자동 요청하지 않는다.

## 18. Authority가 헷갈릴 때

Primary Authority 목록은 `sdlc/config/contract-authority.yaml` 하나에서 확인한다.

- `sdlc/guides/`: 설명용 Derived View
- `sdlc/design/`: Baseline/Contract/Review/Validation/Experiment를 포함한 설계 Reference & History

이 두 영역은 Active Runtime Contract를 덮어쓰는 Authority가 아니다. 상세 경계는 `sdlc/design/README.md`와 `sdlc/guides/README.md`를 따른다.
