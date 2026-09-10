# Harness CLI 기능 참조 가이드

이 문서는 `python sdlc/scripts/harness.py ...`에 공개된 **현재 공식 명령 전체**를 한 곳에서 확인하기 위한 참조 문서다.

처음 사용하는 사람은 `START_HERE.md`의 기본 흐름만 따라가면 된다. 이 문서는 특정 기능의 존재 여부, 직접 실행 명령, 일반 사용자 기능과 고급 운영 기능의 경계를 확인할 때 사용한다.

## 1. 명령 분류

### 일반 프로젝트 사용

| 명령 | 용도 | 상세 가이드 |
|---|---|---|
| `setup` | 프로젝트 초기 설정 | `02_PROJECT_설정가이드.md` |
| `intake` | 구조화된 XLSX 요구사항 일괄 인입 | `11_INPUT_자료_준비가이드.md` |
| `rq-add` | 소수 신규 RQ 자연어 추가 | `17_RQ_간편추가_가이드.md` |
| `rq-list` | PM 작업목록 조회/Excel 관리 | `12_RQ_작업목록_운영가이드.md` |
| `rq-ref` | RQ와 참고문서 연결 관리 | `13_RQ_참고문서_레지스트리_가이드.md` |
| `work` | 분석·설계·개발·테스트 작업 | `04_TEMPLATE_및_산출물_가이드.md` |
| `review` | `/work`에서 요청한 사람 판단 기록 | 이 문서 4절 |
| `change` | 요구·업무규칙·범위·목표 동작 변경 | `04_TEMPLATE_및_산출물_가이드.md` |
| `check` | 현재 RQ/프로젝트 상태 확인 | 이 문서 5절 |
| `customer-view` | 고객문서 작성·미리보기·현행화 | `15_고객문서_미리보기_가이드.md` |

### 운영·진단

| 명령 | 용도 |
|---|---|
| `execution-plan` | 현재 Change Level과 필요한 작업 깊이 확인 |
| `delivery` | 개발·테스트·인수·배포의 근거 기반 상태 기록/조회 |
| `projection` | 생성 문서 최신성·검토 상태 관리 |

### Brownfield/SM/Framework 고급 기능

| 명령 | 용도 |
|---|---|
| `discover-impact` | 개발 중 예상 밖 Legacy 영향 발견 기록 |
| `impact-history` | 과거 예상 영향과 실제 영향을 별도로 축적·조회 |
| `component` | 기술 Component의 AS-BUILT baseline/delta 관리 |
| `arch-check` | 정적 Architecture Rule 점검 PoC |
| `metrics` | Harness 효과/비용의 실제 측정값 기록 |

고급 명령은 일반 사용자가 Framework 내부 동작을 위해 매번 직접 실행해야 하는 명령이 아니다. 프로젝트 운영 정책이나 Brownfield Extension을 사용하는 경우에만 선택한다.

## 2. setup

기본:

```bash
python sdlc/scripts/harness.py setup --name my-project --mode AUTO
python sdlc/scripts/harness.py check --setup
```

사람이 관리하는 설정의 기준은 `.sdlc/project.yaml`이다.

주요 옵션:

```text
--name <프로젝트명>
--mode AUTO|GREENFIELD|BROWNFIELD|HYBRID
--delivery FAST|STANDARD|FULL
--force
--no-validate
```

`--force`는 기존 사용자 설정을 덮어쓸 수 있고, `--no-validate`는 Setup 뒤 Harness 구조 검증을 생략하므로 일반 기본값으로 사용하지 않는다.

`--customer`, `--reverse`, `--provider-command`는 과거 자동화와의 호환을 위해 남아 있는 편의 경로다. 신규 프로젝트에서 Agent Provider는 `.sdlc/project.yaml`의 `agent.execution`과 `agent.provider.command`로 관리한다.

## 3. intake

현재 Requirement Intake의 주 입력은 **구조화된 XLSX**다.

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx
```

CSV는 현재 Requirement 주 입력이 아니라 참고자료/근거 추출 형식으로 지원된다.

참고자료 포함:

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx \
  --reference 기능개선안.pptx \
  --reference 운영회의결정.docx
```

폴더 단위 참고자료:

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx \
  --reference-dir br-input/originals
```

기준 정보를 쓰기 전에 후보만 먼저 확인하고 싶다면:

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx --candidate-only
```

비표준 컬럼 Mapping이 필요한 경우에만 Intake Profile을 지정한다.

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx \
  --profile sdlc/config/requirement-intake-columns.example.yaml
```

고급 출력 위치 옵션:

```text
--json-out
--report-out
--manifest-json
--manifest-report
--store
```

## 4. work / review / change

일반 작업:

```bash
python sdlc/scripts/harness.py work --target RQ-001
```

`/work` 결과에서 사람 판단이 필요하다고 제시된 경우 `review`로 결정 근거를 기록할 수 있다.

```bash
python sdlc/scripts/harness.py review \
  --target RQ-001 \
  --by "업무담당자" \
  --answer "승인 완료 후에는 일반 사용자가 수정할 수 없습니다."
```

지원 선택지는 다음과 같다.

```text
--approve
--answer <답변>
--request-change <변경 요청>
--reject <거절 사유>
```

한 번에 하나만 선택한다. `review`는 사람의 답변/검토 근거를 기록하지만 **업무 기준 필드를 조용히 자동 변경하지 않는다.** 승인·답변은 다음 `/work`가 사용하고, 실제 요구/정책 변경 요청은 `/change` 경계에서 처리한다.

업무 의미 자체를 변경할 때:

```bash
python sdlc/scripts/harness.py change \
  --target RQ-001 \
  --change "승인 완료 후에는 관리자만 수정할 수 있도록 변경"
```

`work`와 `change`의 `--stage`, `--artifact`, `--plan-only`, `--dry-run`, `--finalize` 같은 옵션은 Agent/Runtime 실행 경계를 제어하는 고급 옵션이다. 일반 사용자는 Skill이 만든 handoff/finalize 명령을 그대로 사용하는 것을 권장한다.

## 5. check / execution-plan

현재 작업 상태:

```bash
python sdlc/scripts/harness.py check RQ-001
python sdlc/scripts/harness.py check project
```

프로젝트 최초 설정 확인:

```bash
python sdlc/scripts/harness.py check --setup
```

내부 작업 단계를 진단할 때만 `--debug-stage`를 사용할 수 있다. 기본 사람용 상태에서는 내부 Stage를 숨긴다.

현재 Change Level과 필요한 작업 계획을 진단할 때:

```bash
python sdlc/scripts/harness.py execution-plan --target RQ-001
```

일반 사용자가 내부 작업 단계를 직접 조작하기보다, 이 결과를 현재 변경에 필요한 분석·근거·검토 깊이를 이해하는 진단 정보로 사용한다.

## 6. rq-add / rq-list / rq-ref

### rq-add

```bash
python sdlc/scripts/harness.py rq-add \
  --title "승인 후 수정 제한" \
  --request "승인 완료된 근무계획은 일반 사용자가 수정할 수 없게 해줘."
```

주요 선택 옵션:

```text
--background
--desired-result
--scope
--external-id
--allow-duplicate
```

### rq-list

지원 subcommand:

```text
refresh
assign
import
export
```

PM Excel:

```bash
python sdlc/scripts/harness.py rq-list export \
  --format xlsx \
  --output docs/00_관리/RQ_작업관리.xlsx
```

일부 컬럼만 합칠 때:

```bash
python sdlc/scripts/harness.py rq-list import 일부수정.csv --merge-columns
```

### rq-ref

지원 subcommand:

```text
refresh
link
unlink
import
export
```

참고문서 직접 연결 예:

```bash
python sdlc/scripts/harness.py rq-ref link \
  --target RQ-001 \
  --document-id DOC-001 \
  --purpose "현재 업무규정 확인"
```

연결만으로 업무 사실이 확정되지는 않는다.

## 7. customer-view / projection

### 고객문서 생성

```bash
python sdlc/scripts/harness.py customer-view \
  --target RQ-001 \
  --type solution_agreement
```

공식 Harness 경로는 기존 정식 고객문서가 최종 검토됐거나 사람이 수정된 경우 자동 덮어쓰지 않는다.

별도 비교 미리보기:

```bash
python sdlc/scripts/harness.py customer-view \
  --target RQ-001 \
  --type solution_agreement \
  --out docs/20_고객/RQ-001/미리보기_A01.md
```

정식 Profile 경로와 다른 `--out`은 별도 미리보기 Lifecycle로 기록되므로 정식 문서의 검토상태를 대체하지 않는다.

추가 입력 및 일회성 설정:

```text
--input <검증된 추가 근거>       # 반복 가능
--short-name <표시명>
--tailoring-profile <Profile ID>
--contract <Customer Contract 경로>
--profile <Customer Projection Config 경로>
```

Agent Skill을 사용하는 경우 계속 최신화하려면:

```text
/customer-view refresh RQ-001
```

### 생성 문서 상태

```bash
python sdlc/scripts/harness.py projection status --target RQ-001
```

`projection`의 공식 subcommand는 다음과 같다.

```text
generated
status
review
```

`generated`는 Runtime/Agent가 생성 문서를 Lifecycle에 등록하는 저수준 경계다. 일반 사용자는 보통 `work` 또는 `customer-view`가 대신 등록한다.

### 고객 검토 기록

일반 승인:

```bash
python sdlc/scripts/harness.py projection review \
  --target RQ-001 \
  --artifact-id solution_agreement \
  --reviewer "고객담당자" \
  --accept
```

최종 합의 문구 보호:

```bash
python sdlc/scripts/harness.py projection review \
  --target RQ-001 \
  --artifact-id solution_agreement \
  --reviewer "고객담당자" \
  --accept \
  --final-review
```

검토 중 실제 업무정책 변경이 제안되면:

```bash
python sdlc/scripts/harness.py projection review \
  --target RQ-001 \
  --artifact-id solution_agreement \
  --reviewer "고객담당자" \
  --business-policy-edit "승인 완료 후에는 관리자만 수정 가능"
```

이 경우 변경 후보만 기록하고 업무 기준을 자동 변경하지 않는다. `/change`가 필요하다.

## 8. delivery

지원 subcommand:

```text
status
mark
```

현재 배포/인수 상태 조회:

```bash
python sdlc/scripts/harness.py delivery status --target RQ-001
```

현재 지원 이벤트:

```text
DEVELOPMENT_STARTED
SOURCE_CHANGED
BUILD_PASSED
TEST_PASSED
REGRESSION_PASSED
TECHNICAL_VERIFICATION_PASSED
CUSTOMER_ACCEPTED
DEPLOYMENT_COMPLETED
AS_BUILT_RECONCILED
```

`DEVELOPMENT_STARTED`를 제외한 이벤트는 근거가 필요하다.

```bash
python sdlc/scripts/harness.py delivery mark \
  --target RQ-001 \
  --event TEST_PASSED \
  --evidence "테스트 결과 문서 또는 실행 근거" \
  --actor "테스터"
```

기술 검증 완료를 고객 인수 완료로 자동 간주하지 않는다.

## 9. discover-impact / impact-history

### discover-impact

Brownfield 개발 중 예상하지 못한 Component를 발견했을 때:

```bash
python sdlc/scripts/harness.py discover-impact \
  --target RQ-001 \
  --component LEGACY-COMPONENT-A
```

선택적으로 변경 식별자와 업무 Key를 함께 기록할 수 있다.

```text
--change <change-id>
--key <business-key>    # 반복 가능
```

이 기능은 테스트 범위와 재검토 필요성을 확장하지만, 발견한 Source를 업무 기준으로 자동 확정하지 않는다.

### impact-history

지원 subcommand:

```text
record
recommend
discover
metrics
```

과거 영향 기록:

```bash
python sdlc/scripts/harness.py impact-history record \
  --change CHG-001 \
  --target RQ-001 \
  --key 급여마감 \
  --predicted PAY-SVC \
  --actual PAY-SVC
```

과거 이력에서 현재 조사 후보 추천:

```bash
python sdlc/scripts/harness.py impact-history recommend --key 급여마감
```

예상하지 못한 실제 Component 추가 기록:

```bash
python sdlc/scripts/harness.py impact-history discover \
  --change CHG-001 --target RQ-001 --component LEGACY-BATCH
```

기존 기록의 영향분석 지표 조회:

```bash
python sdlc/scripts/harness.py impact-history metrics \
  --change CHG-001 --target RQ-001
```

과거 이력의 추천은 현재 영향의 확정값이 아니라 **현재 근거를 찾기 위한 후보**다.

## 10. component

기술 Component의 baseline + 승인된 delta로 현재 기술 상태를 재구성하는 고급 기능이다.

지원 subcommand와 주요 입력:

| subcommand | 주요 입력 |
|---|---|
| `baseline` | `--component --revision --state-json` (`--replace` 선택) |
| `release` | `--release --release-seq` |
| `delta` | `--component --change --base-revision --release --operations-json` |
| `current` | `--component` (`--release` 선택) |
| `compact` | `--component --release` |

현재 상태 조회:

```bash
python sdlc/scripts/harness.py component current --component <component-id>
```

`delta`에는 선택적으로 `--status`, `--supersedes`, `--revert-of`를 사용할 수 있다. 이 저장소는 완전한 Event Sourcing이 아니며, Component 기술 상태도 업무 기준의 권위가 아니다.

## 11. arch-check

프로젝트의 실행 가능한 Architecture Rule을 정적으로 점검하는 PoC다.

```bash
python sdlc/scripts/harness.py arch-check \
  --config sdlc/config/architecture-rules.json \
  --source-root src/main/java
```

`--source-root`는 반복할 수 있고, 결과를 파일로 보존하려면 `--out`을 지정한다.

위반 결과는 기술 Finding이며 업무정책을 자동 변경하지 않는다. 실제 프로젝트 Rule을 적용하려면 프로젝트 개발가이드/Rule 정책과 함께 사용한다.

## 12. metrics

실제 프로젝트에서 Harness 투입비용과 효과를 측정할 때만 사용한다.

지원 subcommand:

```text
init
record
summary
```

측정 시작:

```bash
python sdlc/scripts/harness.py metrics init \
  --run PILOT-001 \
  --case CASE_A_L1_LOCAL \
  --target RQ-001
```

실제 측정값 기록:

```bash
python sdlc/scripts/harness.py metrics record \
  --run PILOT-001 \
  --metric human_review_minutes \
  --value 12
```

요약:

```bash
python sdlc/scripts/harness.py metrics summary --run PILOT-001
```

측정값이 없으면 임의의 ROI나 PASS를 만들지 않으며 `INSUFFICIENT_EVIDENCE`로 남는다.

## 13. 기능이 추가될 때 문서 동기화 원칙

`harness.py`에 공식 명령을 추가하거나 제거할 때는 최소 다음을 함께 확인한다.

1. 이 문서의 전체 명령 목록
2. 해당 명령의 실제 subcommand와 필수 입력
3. 해당 기능의 상세 사용자 가이드 또는 고급 기능 설명
4. Project Scaffold 배포 대상 여부
5. Runtime/Contract/Test
6. 사람에게 직접 노출되는 표현이 쉬운 한국어인지

공식 명령은 코드에만 존재하고 가이드에서 완전히 사라지지 않게 하고, 반대로 가이드에서 실행 가능한 것처럼 설명한 명령이 실제 Harness에 없는 상태도 허용하지 않는다.
