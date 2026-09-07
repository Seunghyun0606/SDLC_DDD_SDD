# Custom 3×3 Template Pilot — 03. Test 및 ChatGPT 분석 전달 가이드

## 1. 목적

Custom 개발용 3종/고객용 3종을 실제 RQ에 적용한 뒤, 결과를 ChatGPT에 전달하여 다음을 분석하는 방법을 설명한다.

- Config ↔ Tailoring Profile ↔ Template ↔ Projection 일치 여부
- Canonical 의미가 Custom 문서에서 손실되거나 왜곡됐는지
- 개발용 문서와 고객용 문서의 역할 분리가 적절한지
- 설계 ↔ Source 변경 연결이 충분한지
- 불필요한 문서/중복/Agent Context가 늘었는지
- Customer View가 Business Truth를 침범하지 않는지
- Review Cost와 Framework Overhead를 줄일 여지가 있는지

CI PASS만으로 실제 문서 품질 PASS를 주장하지 않는다.

## 2. Test 대상 선정

최소 3개 RQ를 권장한다.

### Case 1 — L1/L2 Local Change

예:
- 화면 Label 변경
- Validation 조건 1개 수정
- 단일 SQL WHERE 조건
- 단일 Method Local Fix

확인 포인트:
- 분석은 유지하지만 문서가 과도하게 생성되지 않는가
- Coding Start가 Framework 때문에 늦어지지 않는가
- Source write 전 Intent/AS-IS/Impact가 확인되는가

### Case 2 — L3 UI + Multi Program Change

확인 포인트:
- 업무정의서 → 화면설계서 → 프로그램설계서 의미 연결
- Program/Source Mapping
- AC/Test 연결
- 고객 3종 Projection의 의미 보존

### Case 3 — L3/L4 Unexpected Legacy Discovery

확인 포인트:
- 예상하지 못한 Program/Batch 영향 기록
- Change Level 상향
- Regression 확장
- STALE View
- Reconciliation / AS-BUILT

## 3. 자동 회귀 Test

Repository 자체 회귀는 다음으로 확인한다.

```bash
python -m unittest tests.test_custom_template_3x3_pilot_v19 -v
```

전체 회귀는 프로젝트 CI/Worklist workflow 기준으로 실행한다.

Custom 3×3 Test에서 최소 확인하는 자동 항목은 다음이다.

1. Customer Projection Config key가 DEAD_CONFIG가 아님
2. Internal Profile = 3종
3. Customer Profile = 3종
4. Customer View가 실제 Custom Template을 사용
5. 업무정의서의 Internal Profile Stage Mapping이 Customer Projection 입력으로 연결됨
6. 화면설계서는 DESIGN Evidence를 사용
7. 프로그램설계서는 Program/Development/Test/Verify 계열 Evidence를 사용
8. Customer metadata에 실제 Custom Profile ID 기록
9. Customer View `business_truth_authority=false`
10. unresolved `{{placeholder}}`가 남지 않음

## 4. 수동 Pilot 결과 저장 위치

ChatGPT 분석 전에 RQ별 Evidence 폴더를 하나 만든다.

```text
pilot-evidence/
└─ RQ-001/
   ├─ 00_check_before.json
   ├─ 01_check_after.json
   ├─ 02_source.diff
   ├─ 03_build.log
   ├─ 04_test.log
   └─ 05_review-notes.md
```

예:

```bash
mkdir -p pilot-evidence/RQ-001
python sdlc/scripts/harness.py check RQ-001 > pilot-evidence/RQ-001/00_check_before.json
```

개발 후:

```bash
python sdlc/scripts/harness.py check RQ-001 > pilot-evidence/RQ-001/01_check_after.json
git diff <PILOT_BASE_SHA>..HEAD > pilot-evidence/RQ-001/02_source.diff
```

Build/Test는 프로젝트 실제 명령으로 실행하고 로그를 남긴다.

```bash
./mvnw -q -DskipTests package > pilot-evidence/RQ-001/03_build.log 2>&1
./mvnw test > pilot-evidence/RQ-001/04_test.log 2>&1
```

명령은 예시이며 `.sdlc/project.yaml`의 실제 Build/Test 명령을 우선한다.

## 5. ChatGPT에 반드시 전달할 파일

### A. Config / Mapping — 필수

```text
.sdlc/project.yaml
sdlc/custom/project/tailoring/CUSTOM_PILOT_INTERNAL_3.yaml
sdlc/custom/project/tailoring/CUSTOM_PILOT_CUSTOMER_3.yaml
sdlc/custom/project/config/customer-3x3-document-contract.json
sdlc/custom/project/config/customer-3x3-projection-profile.json
```

목적:
- 어떤 Profile이 실제 선택됐는지 확인
- Stage/Canonical/Evidence → Artifact Mapping 확인
- 고객 Projection Section 규칙 확인

### B. Custom Template 6개 — 필수

```text
sdlc/custom/project/templates/pilot-3x3/internal/01_업무정의서.md
sdlc/custom/project/templates/pilot-3x3/internal/02_화면설계서.md
sdlc/custom/project/templates/pilot-3x3/internal/03_프로그램설계서.md
sdlc/custom/project/templates/pilot-3x3/customer/A01_업무정의서.md
sdlc/custom/project/templates/pilot-3x3/customer/A02_화면설계서.md
sdlc/custom/project/templates/pilot-3x3/customer/A03_프로그램설계서.md
```

목적:
- Human/Machine Ownership 확인
- 중복/누락 Section 확인
- Internal/Customer Layer 역할 분리 확인

### C. 실제 생성 문서 — 필수

RQ별로 실제 생성된 파일을 전달한다.

```text
docs/10_산출물/RQ-001/01_업무정의서.md
docs/10_산출물/RQ-001/02_화면설계서.md     # UI가 있을 때
docs/10_산출물/RQ-001/03_프로그램설계서.md

docs/20_고객/RQ-001/A01_업무정의서.md
docs/20_고객/RQ-001/A02_화면설계서.md     # UI가 있을 때
docs/20_고객/RQ-001/A03_프로그램설계서.md
```

이 파일이 가장 중요하다. Template 파일만 전달하면 실제 Agent 작성 품질을 분석할 수 없다.

### D. Canonical / Runtime Evidence — 필수

```text
sdlc/canonical/store.json
sdlc/runtime/change-level/RQ-001.json
sdlc/runtime/work-handoff/RQ-001.json
sdlc/runtime/projections/RQ-001-A01.json
sdlc/runtime/projections/RQ-001-A02.json     # 존재할 때
sdlc/runtime/projections/RQ-001-A03.json
```

그리고 해당 RQ의 실행 폴더에서 다음을 전달한다.

```text
sdlc/runtime/work-runs/RQ-001-*/work-context.json
sdlc/runtime/work-runs/RQ-001-*/stage-result.json
```

모든 RQ 전체 Canonical을 외부에 제공하기 어렵다면 최소한 분석 대상 RQ와 직접 Relation된 Entity를 포함한 비식별화 사본을 제공한다. 단, 비식별화 과정에서 상태/Relation/Authority 의미를 삭제하지 않는다.

### E. Source 변경 / Test Evidence — 필수

```text
pilot-evidence/RQ-001/02_source.diff
pilot-evidence/RQ-001/03_build.log
pilot-evidence/RQ-001/04_test.log
pilot-evidence/RQ-001/00_check_before.json
pilot-evidence/RQ-001/01_check_after.json
```

가능하면 변경된 실제 Source 파일도 함께 제공한다.

Source가 없으면 다음 질문에 답할 수 없다.

- 프로그램설계가 실제 Source와 맞는가
- Machine-derived Source Mapping이 정확한가
- 설계가 구현에 반영됐는가
- 예상 밖 변경이 있었는가

### F. Human Review 결과 — 실제 사용성 분석 시 필수

`pilot-evidence/RQ-001/05_review-notes.md`에 다음 정도만 기록한다.

```markdown
# Pilot Human Review

- RQ: RQ-001
- Reviewer 역할: BA / Designer / Developer / Tester / Customer
- 업무정의 Review 시간(분):
- 화면설계 Review 시간(분):
- 프로그램설계 Review 시간(분):
- 고객 문서 Review 시간(분):
- 직접 수정 시간(분):
- 이해하기 어려웠던 Section:
- 중복이라고 느낀 Section:
- 빠진 중요 내용:
- Agent가 근거 없이 작성한 내용:
- 실제 작업에 도움이 된 내용:
```

Review 시간을 기록하지 않으면 “문서 수를 줄였으니 비용도 줄었다”는 주장만 남는다.

## 6. 보안/개인정보 정리 후 전달

ChatGPT에 전달하기 전에 다음을 제거하거나 마스킹한다.

- Password/API Key/Token
- 실제 고객 개인정보
- 운영 DB 접속정보
- 사내 비공개 URL/계정
- Secret header/cookie

하지만 다음은 가능하면 유지한다.

- RQ/FR/BR/AC/TC ID 관계
- Change Level과 판정 이유
- Source file 상대경로와 symbol 이름
- Relation 구조
- 상태값 `OPEN`, `CONFIRMED`, `CHECK_REQUIRED`, `STALE_VIEW`
- Source diff의 변경 의미

분석에 필요한 구조까지 삭제하면 Semantic/Trace 검증이 불가능하다.

## 7. ChatGPT 전달 권장 순서

한 번에 Repository 전체를 올리지 않는다.

### 1차 — Framework/Config 검토

A + B 파일을 전달한다.

목적:
- Config/Profile/Template 구조 자체의 정합성 확인

### 2차 — RQ 실행 결과 검토

C + D 파일을 전달한다.

목적:
- Canonical → Internal → Customer Projection 의미 보존 확인

### 3차 — Source/Test 검토

E 파일과 변경 Source를 전달한다.

목적:
- Design → Code / Code → Design Reconciliation 확인

### 4차 — 실사용성 검토

F Human Review 기록을 전달한다.

목적:
- Review Cost / Overhead / Adoption 판단

이 순서를 쓰면 불필요한 Repository 전체 Context가 Agent에 들어가는 것을 줄일 수 있다.

## 8. ChatGPT 분석 요청 Prompt

아래 Prompt에서 `<RQ-ID>`, `<프로젝트 설명>` 부분만 바꿔서 사용한다.

```text
당신은 Enterprise SDLC Architecture Red Team Reviewer이자 Brownfield Enhancement Reviewer다.

분석 대상:
- Framework Branch: SDLC_DESIGN_SESSION_FIRST/tailoring-control-plane/v1.9.0
- Target RQ: <RQ-ID>
- Project: <프로젝트 설명>

이번 검토에서는 제공한 파일만 근거로 사실을 판정하고, 파일에 없는 내용을 추정하여 PASS 처리하지 마라.

핵심 검토 목적:
1. .sdlc/project.yaml의 Config가 실제 Custom Internal/Customer Profile과 일치하는가?
2. Tailoring Profile의 Stage/Canonical Mapping과 Template Section이 일치하는가?
3. 같은 Canonical 의미가 개발용 3종과 고객용 3종에 보존되는가?
4. 고객 문서가 새로운 Business Truth를 만들거나 Source Observation을 업무정책으로 승격하지 않는가?
5. 업무정의서 → 화면설계서 → 프로그램설계서 → Source Diff가 추적 가능한가?
6. Program/Method/Query/Table 등 Source에서 재생성 가능한 항목을 사람이 불필요하게 유지하고 있지 않은가?
7. Change Level에 비해 문서/Review 작업이 과도하지 않은가?
8. Agent가 근거 없이 생성한 Business/Technical Fact가 있는가?
9. Source와 설계가 다른 항목이 ALIGNED/CONFLICT/CHECK_REQUIRED로 적절히 구분되는가?
10. Canonical revision 변경 후 Customer Projection의 STALE/PENDING_REVIEW/CURRENT lifecycle이 맞는가?

반드시 다음을 별도로 평가하라.

A. Config/Profile/Template Consistency
B. Canonical Semantic Coverage
C. Internal Document Quality
D. Customer Projection Quality
E. Design-to-Code Traceability
F. Source-to-Design Reconciliation
G. Unsupported AI Fact
H. Duplicate/Redundant Documentation
I. Human Review Cost
J. Framework Overhead

각 Finding은 다음으로 판정하라.
- PASS
- PARTIAL
- FAIL
- INSUFFICIENT_EVIDENCE

각 Finding마다 반드시 실제 파일명과 근거 Section/값을 제시하라.

마지막에는 다음 표를 작성하라.

1. 유지할 Section
2. 삭제/통합할 Section
3. Machine-derived로 바꿀 Section
4. Human Authoritative로 유지할 Section
5. 고객용에서 숨길 기술정보
6. 추가로 필요한 Evidence
7. Runtime/Config 수정이 필요한 항목

그리고 다음 수치를 계산 가능한 범위에서 제시하라.
- generated artifact count
- framework interaction count
- human review minutes
- human edit minutes
- coding start latency
- unsupported AI fact count
- stale view count
- framework overhead ratio

실제 시간이 제공되지 않았으면 임의 추정하지 말고 NOT_MEASURED로 표시하라.

최종적으로 이 Custom 3×3 구조가 Standard Profile보다 실제 Review Cost를 줄이는지 판정하되, Human Review 실측이 없으면 INSUFFICIENT_EVIDENCE로 두어라.
```

## 9. ChatGPT 분석 결과를 다시 Framework 개선에 사용할 때

분석 결과를 그대로 Canonical Truth로 넣지 않는다.

다음 순서를 따른다.

```text
ChatGPT Finding
→ Framework/Project Candidate
→ 사람 Review
→ Config/Profile/Template 또는 Runtime 수정
→ 동일 RQ 재실행
→ 결과 비교
```

특히 ChatGPT가 제안한 업무정책은 Customer/BA 확인 없이 `CONFIRMED_BUSINESS`로 승격하지 않는다.

## 10. Test 종료 시 보관할 최소 Evidence Package

최종적으로 아래 묶음이 있으면 다음 Red Team 분석을 재현하기 쉽다.

```text
Custom Config 1
Custom Tailoring Profile 2
Custom Projection Config/Contract 2
Custom Template 6
실제 Internal 문서 최대 3/RQ
실제 Customer 문서 최대 3/RQ
Canonical/Change Level/Projection metadata
Source diff
Build/Test 결과
PM check before/after
Human Review notes
```

이 패키지는 Framework 전체 Repository를 전달하는 것보다 작고, 실제 Pilot 분석에는 더 유용하다.
