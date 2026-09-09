# SDLC Core Skill — customer-view

이 파일은 특정 IDE나 Agent 제품에 종속되지 않는 고객문서 작성·현행화 Skill의 **Core Source of Truth**다.

목표는 사용자가 Customer Profile이나 Projection Lifecycle 내부 구조를 외우지 않아도 **현재 확보된 업무 기준 정보와 검증된 설계·Source·Test 근거를 이용해 고객문서를 만들고, 필요할 때 계속 현행화해서 볼 수 있게 하는 것**이다.

고객에게 보여주는 최종 본문은 Runtime이 수집한 기술 문구를 그대로 복사하지 않는다. **Agent가 같은 사실만 사용해 고객이 이해할 수 있는 간결한 한국어 문장으로 다시 작성한 뒤 Projection으로 등록한다.**

## 1. 사용자 의도

다음 요청은 모두 이 Skill로 처리한다.

- `RQ-001 고객문서 만들어줘`
- `RQ-001 고객문서 최신화해줘`
- `지금 상태 기준으로 고객문서 다시 보여줘`
- `A01 다시 만들어줘`
- `A02 영향범위 문서 최신화해줘`
- `A03 테스트/인수 문서 만들어줘`
- `고객문서가 최신인지 확인해줘`
- `/customer-view RQ-001`
- `/customer-view refresh RQ-001`
- `/customer-view status RQ-001`

## 2. 가장 중요한 원칙

1. **고객문서는 업무 기준 정보가 아니라 생성 문서다.**
   - Customer 문서 작성/재생성만으로 `sdlc/canonical/store.json`을 변경하지 않는다.
   - 고객문서에서 새로운 Requirement/Business Rule/Scope/TO-BE를 확정하지 않는다.
2. **없는 사실을 채워 넣지 않는다.**
   - 현재 기준 정보와 검증된 Engineering/Source/Test/Operations 근거가 없는 내용은 미확정 또는 확인 필요로 남긴다.
3. **Customer Profile이 문서 구성을 결정한다.**
   - 기본 `CUSTOMER_STANDARD_3`만 하드코딩하지 않는다.
   - 프로젝트가 1/3/5/8/13/N종 Custom Profile을 사용하면 Customer Profile의 `artifacts`를 읽어 그 구성을 따른다.
4. **Engineering 문서 구조와 Customer 문서 구조를 직접 묶지 않는다.**
   - Customer Profile은 독립적으로 선택한다.
   - Engineering 문서는 고객문서를 보강하는 근거일 수 있지만 문서 수/순번을 강제하지 않는다.
5. **고객 본문은 고객 관점의 자연어 문장으로 작성한다.**
   - Source 파일명, Java Class/Method, SQL Query ID, Table/Column, HTTP 상태값, 내부 Runtime 상태를 기본 본문에 그대로 노출하지 않는다.
   - 기술 근거의 의미를 확인할 수 있으면 `누가 / 어떤 조건에서 / 무엇을 하고 / 결과가 무엇인지`가 드러나는 일반적인 한국어 문장으로 표현한다.
   - 기술 근거만 있고 업무 의미를 확정할 수 없으면 억지로 번역하지 않고 `확인 필요`로 남긴다.
6. **프로젝트/고객 도메인 용어를 우선한다.**
   - `br-input/glossary.csv`가 있으면 먼저 읽고 고객이 사용하는 `term`을 우선 사용한다.
   - alias/약어가 있으면 문서에서는 가능한 한 고객 표준 용어로 통일한다.
   - 용어집에 없는 의미를 임의 정의하지 않는다.
7. **FINAL_REVIEW와 사람 수정 문구를 자동 덮어쓰지 않는다.**
   - 최종검토된 문서가 현재 상태면 그대로 보여준다.
   - 최종검토 후 기준 정보가 변경되어 `STALE_VIEW`가 되어도 기존 파일을 자동 재생성하지 않는다.
   - 사람 수정 내용이 있는 문서는 재검토 필요를 알리고 `/change` 또는 `/work` 경계부터 판단한다.
8. **고객문서를 최신이라고 말하기 전에 Lifecycle을 확인한다.**
   - 파일 존재 여부만 보고 최신이라고 판단하지 않는다.

## 3. 공식 Runtime 진입점

고객문서 초안 생성:

```bash
python sdlc/scripts/harness.py customer-view \
  --target <RQ> \
  --type <customer-artifact-id>
```

고객/Engineering/PM 생성 문서 상태 확인:

```bash
python sdlc/scripts/harness.py projection status --target <RQ>
```

RQ 전체 작업 상태 확인이 필요하면:

```bash
python sdlc/scripts/harness.py check <RQ>
```

직접 `customer_projection_runtime.py` 또는 Lifecycle JSON을 수정하지 않고 공식 Harness 진입점을 사용한다.

중요: `harness.py customer-view`는 근거를 안전하게 선별·조립하는 Runtime 경계다. **사람에게 보여줄 최종 고객문서는 이 Skill의 `고객 문장 작성 단계`까지 완료한 결과**를 사용한다.

## 4. 고객문서 작성/현행화 기본 Flow

```text
사용자 요청
→ Target 확인
→ Project의 documents.customer.profile 확인
→ Customer Profile의 artifacts 확인
→ projection status 확인
→ 현재 기준 정보 + 관련 검증 근거 확인
→ br-input/glossary.csv 확인
→ 문서별 안전 상태 분류
   ├─ 미생성 / 일반 STALE / 일반 재생성 요청 → customer-view 초안 생성
   ├─ CURRENT → 현재 문서를 보여주거나 명시적 요청 시 재생성
   ├─ PENDING_REVIEW → 최신 내용 확인 후 검토 대기 상태로 보여줌
   ├─ MANUAL_EDIT_DETECTED → 자동 덮어쓰기 금지, 수정 의미 분류
   └─ FINAL_REVIEW + 이후 변경 → 기존 문구 보존, 재검토 필요
→ 생성 초안의 고객 본문을 같은 사실 기준으로 쉬운 한국어 문장으로 재작성
→ 기술 식별자/내부 상태/코드 조각 노출 여부 자체검토
→ 재작성된 파일을 Projection generated로 다시 등록
→ projection status 재확인
→ 사람에게 문서 경로 + 현재 상태 + 확인 필요 항목 요약
```

## 5. 먼저 해야 하는 확인

### 5.1 Target 존재 확인

사용자가 지정한 RQ가 기준 정보에 없으면 고객문서를 임의 생성하지 않는다.

새 요구사항이면 먼저 Requirement Intake가 필요하다.

### 5.2 현재 Customer Profile 확인

`.sdlc/project.yaml`의 다음 값을 기준으로 한다.

```yaml
documents:
  customer:
    profile: CUSTOMER_STANDARD_3
```

Skill은 Profile의 `artifacts` 목록을 읽어서 고객문서 종류를 결정한다.

따라서 `전체 고객문서 최신화해줘` 요청에서 `CUSTOMER_STANDARD_3`이면 3종을 처리하고, Custom Profile이면 실제 정의된 N종을 처리한다.

### 5.3 프로젝트 도메인 용어 확인

프로젝트/고객이 사용하는 업무 용어는 다음 파일을 우선 확인한다.

```text
br-input/glossary.csv
```

표준 예시는 다음에 있다.

```text
sdlc/templates/br-intake/glossary.example.csv
```

기본 컬럼:

```text
term,meaning,alias_or_abbreviation,scope,note
```

예:

```csv
term,meaning,alias_or_abbreviation,scope,note
근무계획,직원이 근무할 예정 시간과 형태를 등록한 계획,근무스케줄,근태,고객 표준 명칭
마감,해당 기간의 근태 또는 급여 처리를 더 이상 일반 사용자가 변경하지 못하도록 확정하는 절차,Close,근태/급여,업무 문서 정의 기준
```

규칙:

- 문서 본문에서는 `term`을 우선 사용한다.
- `meaning`은 설명이 필요할 때만 자연스럽게 풀어 쓴다.
- `alias_or_abbreviation`은 원본 탐색에는 사용하지만 고객문서 표준 표현으로 무조건 유지하지 않는다.
- `scope`가 다른 같은 용어는 문맥에 맞는 정의만 사용한다.
- 정확한 의미가 고객 문서 근거로 확인되지 않았다면 용어집만 보고 새로운 업무 Rule을 만들지 않는다.

### 5.4 현재 Projection 상태 확인

항상 먼저 다음을 실행한다.

```bash
python sdlc/scripts/harness.py projection status --target RQ-001
```

고객문서에 대해 최소 다음을 본다.

- `artifact_id`
- `artifact_path`
- `audience = CUSTOMER`
- `state`
- `lifecycle`
- `generated_from_revision`

## 6. 고객 문장 작성 단계 — 필수

Runtime이 고객문서 파일을 생성한 뒤 **그 파일을 그대로 완료 결과로 제시하지 않는다.** FINAL_REVIEW/MANUAL_EDIT_DETECTED가 아닌 생성 대상에 한해 Agent가 본문을 다시 읽고 다음 규칙으로 고객용 표현을 만든다.

### 6.1 문장 구조

가능하면 한 문장에 하나의 사실을 담는다.

권장 순서:

```text
주체 또는 대상
→ 조건/상황
→ 처리 또는 변화
→ 고객/업무 결과
```

예:

```text
기술식 표현:
근무계획 저장 시 EMP_WORK_PLAN INSERT, WorkPlanService.savePlan() 호출

고객용 표현:
근무계획을 등록하면 입력한 내용이 시스템에 저장됩니다.
```

```text
기술식 표현:
approval_yn='Y'인 경우에만 UPDATE 가능

고객용 표현:
승인이 완료된 경우에만 내용을 변경할 수 있습니다.
```

```text
기술식 표현:
오류 발생 시 transaction rollback

고객용 표현:
처리 중 오류가 발생하면 변경 내용을 저장하지 않고 이전 상태를 유지합니다.
```

위 예시는 표현 방법의 예일 뿐이다. 실제 문서에서는 **현재 RQ와 근거에서 확인된 사실만** 사용한다.

### 6.2 기본 본문에서 피해야 하는 표현

고객이 특별히 요구하지 않았다면 기본 본문에 다음을 그대로 쓰지 않는다.

```text
JSP / Java / XML / SQL
Class / Method / Controller / Service / DAO / Mapper
Query ID
Table / Column 이름
파일 경로
Hash
HTTP 4xx/5xx 코드
JSON field 이름
Runtime 내부 상태 코드
Canonical / Provenance / Projection / Stage
DEFERRED / SOURCE_BLOCK / ITERATE / OPEN
```

필요한 의미는 다음처럼 바꾼다.

```text
DB 영속 여부
→ 처리한 내용이 시스템에 저장되어 계속 유지되는지

Source 수정
→ 현재 시스템의 처리 방식을 변경

API 오류
→ 시스템 간 연계 처리 중 오류

Table/Column 변경
→ 저장 정보의 구조 변경

Batch
→ 정해진 시간이나 조건에 따라 자동으로 실행되는 처리
```

단, 프로젝트 고객이 `API`, `배치`, `인터페이스` 등을 공식 도메인 용어로 사용하며 `br-input/glossary.csv`에 등록했다면 그 용어는 사용할 수 있다.

### 6.3 기술 내용을 지우기만 하지 않는다

기술 근거가 고객에게 필요한 업무 의미를 뒷받침한다면 **업무 효과를 문장으로 설명**한다.

잘못된 방식:

```text
EMP_WORK_PLAN, savePlan(), updatePlan() 삭제
→ "저장합니다."
```

권장 방식:

```text
근무계획 등록 시 저장된다는 근거가 확인됨
→ "근무계획을 등록하면 입력한 내용이 시스템에 저장됩니다."
```

기술 근거만으로 무엇이 저장되는지 또는 어떤 업무 Rule인지 알 수 없으면 추측하지 않는다.

```text
→ "현재 자료만으로 고객에게 설명할 업무 의미를 확정하기 어려워 추가 확인이 필요합니다."
```

### 6.4 문체

- 기본 종결은 `~합니다`, `~됩니다`, `~할 수 있습니다`, `~필요합니다`처럼 짧고 명확하게 쓴다.
- `~함`, `~처리`, `~여부`, `~대상`, `~적용`처럼 명사만 나열한 문장을 최소화한다.
- 내부 설계보고서처럼 `A → B → C`만 나열하지 말고 고객이 이해할 수 있는 문장으로 설명한다.
- 같은 의미를 여러 단락에서 반복하지 않는다.
- 표는 비교/범위/결정사항처럼 표가 더 이해하기 쉬운 경우에만 사용한다.
- 고객에게 필요한 경우에만 괄호로 원용어를 병기한다.

### 6.5 재작성 후 자체검토

문서를 완료하기 전에 visible body를 다시 읽고 다음을 확인한다.

1. 처음 보는 고객이 별도 Framework 설명 없이 이해할 수 있는가?
2. Java Method/Table/Column/File Path 같은 구현 식별자가 기본 본문에 남아 있지 않은가?
3. `DB 영속`, `DEFERRED`처럼 일반 사용자가 바로 이해하기 어려운 표현이 남아 있지 않은가?
4. 각 핵심 문장이 `무엇이 어떻게 바뀌는지` 설명하는가?
5. 도메인 용어가 `br-input/glossary.csv`와 일치하는가?
6. 기술 내용을 자연어로 바꾸면서 없는 업무 사실을 추가하지 않았는가?

하나라도 만족하지 못하면 사람에게 보여주기 전에 다시 다듬는다.

### 6.6 Agent 재작성 후 Projection hash 재등록

Agent가 생성된 고객문서의 **표현만** 고객 친화적으로 다듬으면 그 파일은 Agent가 관리하는 동일 Projection이다. 따라서 단순 manual edit로 오인되지 않도록 `customer-view` 생성 결과에서 받은 `artifact_id`, `artifact_path`, `customer_tailoring_profile`을 사용해 다시 등록한다.

예:

```bash
python sdlc/scripts/harness.py projection generated \
  --target RQ-001 \
  --artifact-id solution_agreement \
  --artifact-path docs/20_고객/RQ-001/A01_요구_업무_기능_합의서.md \
  --audience CUSTOMER \
  --profile-id CUSTOMER_STANDARD_3 \
  --manual-edit-policy FINAL_REVIEW_ONLY
```

그 다음:

```bash
python sdlc/scripts/harness.py projection status --target RQ-001
```

로 다시 확인한다.

이 재등록은 고객문서 hash/lifecycle을 갱신할 뿐 **업무 기준 정보를 변경하지 않는다.**

## 7. 상태별 처리 규칙

### 7.1 아직 문서가 없는 경우

Profile의 해당 artifact를 생성하고, 6장의 고객 문장 작성 단계를 수행한다.

예:

```bash
python sdlc/scripts/harness.py customer-view \
  --target RQ-001 \
  --type solution_agreement
```

### 7.2 STALE_VIEW

먼저 기존 metadata의 `lifecycle`을 확인한다.

- 일반 초안/검토중 문서: 현재 기준 정보/검증 근거를 이용해 다시 생성할 수 있다.
- `FINAL_REVIEW`: 자동 재생성하지 않는다. 기존 사람 문구를 보존하고 `재검토 필요`로 안내한다.

### 7.3 CURRENT

단순 `최신 문서 보여줘` 요청이면 기존 문서를 다시 생성할 필요가 없다. 파일을 읽어 핵심 내용을 보여준다.

사용자가 명시적으로 `다시 생성해줘`라고 요청했고 FINAL_REVIEW가 아니라면 최신 입력으로 다시 생성하고 고객 문장 작성 단계를 수행할 수 있다.

### 7.4 PENDING_REVIEW

현재 기준 정보 revision 기준으로 생성된 문서이면 다시 만들기보다 현재 문서를 보여주고 `고객/사람 검토 대기`임을 알려준다.

다만 이후 `/work` 또는 `/change`로 의미/근거가 추가되었다면 Lifecycle이 stale인지 다시 확인한다.

### 7.5 MANUAL_EDIT_DETECTED

자동 덮어쓰지 않는다.

사람 수정 내용을 다음 중 하나로 분류한다.

- `표현/오탈자/레이아웃`: 생성 문서 표현 수정 후보
- `Requirement/Business Rule/Scope/TO-BE 의미 변경`: `/change`
- `Source/DB/Program/AS-IS/Test 근거 수정`: `/work`

의미가 불명확하면 사람에게 짧게 확인한 뒤 처리한다.

### 7.6 FINAL_REVIEW

최종검토된 사람 문구는 보존한다.

```text
FINAL_REVIEW + 현재 기준 정보 동일
→ 기존 파일 유지
→ 현재 문서로 보여줌

FINAL_REVIEW + 이후 기준 정보 변경
→ STALE_VIEW
→ 기존 파일 자동 덮어쓰기 금지
→ 무엇이 달라졌는지 확인
→ /change 또는 /work 반영 여부 결정
→ 고객문서 재검토
```

## 8. 현재 Source/Test까지 반영해 달라는 요청

`customer-view` 자체가 Source를 다시 분석하거나 Test를 실행하는 것은 아니다.

사용자가 다음처럼 요청하면:

```text
현재 소스까지 반영해서 고객문서 최신화해줘.
방금 개발한 내용과 테스트 결과까지 넣어서 A03 갱신해줘.
```

Agent는 먼저 관련 `/work` 결과와 실제 검증 근거가 최신인지 확인한다.

- Source/DB/Program 현행을 다시 조사해야 함 → `/work`
- Requirement/Business Rule/Scope/TO-BE 변경 → `/change`
- 이미 검증된 Engineering/Test 근거가 존재함 → 그 파일만 `--input`으로 고객문서에 추가

고객문서를 만들기 위해 Source 사실을 추측하지 않는다.

## 9. 관련 Engineering/Test 근거를 추가할 때

Target과 실제 관련된 검증 파일만 선택한다. 전체 `docs/10_engineering`을 무조건 입력하지 않는다.

예:

```bash
python sdlc/scripts/harness.py customer-view \
  --target RQ-001 \
  --type delivery_scope \
  --input docs/10_engineering/RQ-001/01_업무정의서.md \
  --input docs/10_engineering/RQ-001/02_작업지시서.md
```

추가 입력이 Customer 문서에 통째로 복사되는 것은 아니다. Customer Projection Contract와 Profile에서 허용된 내용만 조립한다.

## 10. 기본 CUSTOMER_STANDARD_3 사용 예

### A01 요구·업무·기능 합의서

```bash
python sdlc/scripts/harness.py customer-view \
  --target RQ-001 \
  --type solution_agreement
```

### A02 영향·개발범위 공유서

```bash
python sdlc/scripts/harness.py customer-view \
  --target RQ-001 \
  --type delivery_scope
```

### A03 테스트·인수·운영 결과서

```bash
python sdlc/scripts/harness.py customer-view \
  --target RQ-001 \
  --type acceptance_handover
```

기본 출력:

```text
docs/20_고객/RQ-001/
```

## 11. `전체 고객문서 최신화` 요청

고정 3종 명령을 무조건 실행하지 않는다.

1. 프로젝트 Customer Profile을 읽는다.
2. Profile `artifacts`를 순서대로 확인한다.
3. 각 artifact의 현재 Projection 상태를 확인한다.
4. FINAL_REVIEW/MANUAL_EDIT_DETECTED는 자동 덮어쓰기 대상에서 제외한다.
5. 나머지 필요한 artifact만 `customer-view --type <artifact-id>`로 초안 생성/현행화한다.
6. 생성된 파일마다 6장의 고객 문장 작성 단계를 수행한다.
7. 재작성된 파일을 `projection generated`로 다시 등록한다.
8. 마지막에 `projection status --target <RQ>`를 다시 실행한다.

결과는 다음처럼 간결하게 보여준다.

```text
RQ-001 고객문서 현행화
- A01: 고객용 문장 현행화 완료 / 검토 대기
- A02: 고객용 문장 현행화 완료 / 검토 대기
- A03: 근거 부족으로 현재 내용 유지
- 최종검토 문서: 자동 덮어쓰기 없음
```

## 12. 고객문서에서 수정 요청을 받은 경우

고객이나 사용자가 문서의 특정 부분을 바꿔달라고 요청하면 파일부터 고치지 않는다.

예:

```text
A01의 업무규칙을 "승인 후에만 수정 가능"으로 바꿔줘.
```

이 요청이 실제 정책 변경이면 `/change`로 기준 정보를 먼저 갱신한다.

```text
A01 표현을 "신청" 대신 "요청"으로 통일해줘.
```

업무 의미가 변하지 않는 문구 변경이라면 생성 문서 표현 수정으로 다룰 수 있다. FINAL_REVIEW 문구라면 사람 수정 이력을 보존한다.

## 13. 사람에게 보여줄 결과

작업 완료 보고는 다음만 우선한다.

- 사용한 Customer Profile
- 확인/생성/현행화한 고객문서 목록
- 각 문서 경로
- 최신 / 검토 대기 / 재검토 필요 상태
- 근거 부족 또는 사람 확인 필요 항목
- 고객 용어집 적용 여부
- 고객용 자연어 문장 자체검토 완료 여부
- FINAL_REVIEW 자동 덮어쓰기 여부

Machine Runtime JSON 전체를 그대로 사용자에게 출력하지 않는다.

상세 명령 예시는 `docs/00_시작/15_고객문서_미리보기_가이드.md`를 따른다.
