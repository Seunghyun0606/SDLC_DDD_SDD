# Template 및 산출물 가이드

이 문서는 **Template이 무엇이고, Agent가 어떤 사람용 산출물을 만드는지** 설명한다. Profile 선택과 문서 개수 Custom은 `03_TAILORING_설정가이드.md`, 역할별 책임은 `05_이해관계자별_작업가이드.md`를 본다.

## 1. Template과 Profile은 다르다

| 위치 | 역할 |
|---|---|
| `sdlc/templates/semantic/` | 작업 단계에서 Agent가 어떤 의미와 근거를 다룰지 정의 |
| `sdlc/templates/engineering/` | 개발자/설계자용 생성 문서 Template |
| `sdlc/templates/customer/` | 고객용 생성 문서 Template |
| `sdlc/templates/management/` | PM/관리 View Template |
| `sdlc/tailoring/standard/*.yaml` | 어떤 Template을 어떤 문서로 조립할지 정하는 Profile |

`semantic` Template은 고객 제출 문서나 개발자 최종 문서가 아니다. Agent 작업 구조다.

## 2. 사람용 문서는 크게 세 종류

### Engineering

설계·개발·테스트를 수행하기 위한 Living Spec이다.

기본:

```text
docs/10_engineering/<TARGET>/
├─ 00_work-map.md
├─ specs/<TARGET>.md
└─ programs/<TARGET>.md   # 필요할 때만
```

### Customer

고객 협의·제출·검수·인수용 문서다.

기본:

```text
docs/20_고객/<TARGET>/
├─ A01_요구_업무_기능_합의서.md
├─ A02_영향_개발범위_공유서.md
└─ A03_테스트_인수_운영_결과서.md
```

### PM / 관리 View

RQ 배정·일정·진척·확인 필요사항을 보는 관리용 View다.

```text
docs/00_관리/
```

실제 파일 경로는 항상 선택 Profile의 `output_path`를 따른다.

## 3. Template은 빈 입력 Form이 아니다

일반 사용자가 Template 파일을 열어 처음부터 모든 표를 채우는 것이 기본 절차가 아니다.

기본 흐름:

```text
/work 또는 /change 요청
→ Agent가 요구사항·기존 문서·Source·DB·Config·근거를 먼저 조사
→ 확인 가능한 내용으로 초안 작성
→ 사람 판단이 필요한 항목만 질문
→ 사람 답변 또는 보류
→ 기준 정보와 근거 갱신
→ Engineering / Customer 생성 문서 최신화
```

Source에서 확인 가능한 Java Class/Method, JSP/XML 경로, Query/Table/Column, 호출관계 같은 기술 사실을 사람에게 다시 입력시키지 않는다.

사람에게 물어야 하는 것은 정책·범위·예외·승인·인수 기준처럼 실제 권한 있는 판단이 필요한 내용이다.

사람의 답변을 명시적으로 기록해야 할 때는 `review`를 사용할 수 있다. 답변 기록 자체가 업무 기준을 자동 변경하지 않으며, 실제 정책 변경은 `/change`로 반영한다.

## 4. Work Map

목적은 상세설계를 반복하는 것이 아니라 한 화면에서 다음을 연결하는 것이다.

- 어떤 요구인가
- 어떤 기능/작업 단위인가
- 어떤 Program/Source를 수정하는가
- 어떤 Test로 확인하는가
- 현재 남은 작업은 무엇인가

내부 식별자와 추적 정보는 Agent가 유지할 수 있지만 사람이 보는 본문은 업무/기능/개발작업/Source/Test 중심으로 읽히게 작성한다.

## 5. Work Unit SDD

기능 또는 업무 단위의 Living Spec이다. 여러 Stage 문서를 단순 이어 붙이는 문서가 아니다.

주로 다음 내용을 현재 확인 수준에 맞게 유지한다.

- 업무 목적과 요구 의도
- 현재 처리 방식
- 목표 처리 방식
- 업무 규칙과 예외
- 영향 범위
- Source/Program 연결
- 구현 계약
- 인수·테스트 조건
- 아직 확인이 필요한 사항
- 실제 구현 결과와 검증 결과

작은 변경이면 확인된 범위만 간결하게 쓰고, 근거가 없는 큰 업무 Process를 억지로 만들어내지 않는다.

## 6. Program Spec

Program Spec은 기능 의미를 다시 쓰는 문서가 아니라 **실제 Source에 어떤 변경을 구현할지** 상세화하는 문서다.

```text
Work Unit SDD → 무엇을 왜 어떻게 동작시킬 것인가
Program Spec  → 어떤 Source에 어떤 차이를 구현할 것인가
```

표준 Compact Profile에서는 Program Spec이 항상 필요한 것은 아니다. 기본 Profile의 현재 정의에서는 `min_change_level: L3`가 적용되어 L3 이상에서 생성 대상이 되며, Project Custom Profile은 별도 규칙을 정의할 수 있다.

### 개발 시작 전 기본 확인 6가지

현재 표준 Readiness는 과거처럼 17개 항목을 모든 변경에 무조건 채우는 방식이 아니다. 먼저 다음 **6개 핵심 정보**를 확인하고, 위험이 실제로 있을 때만 추가 항목을 본다.

1. 기능 의도·설계 기준
2. 실제 구현 대상
3. 실제 Source 근거
4. 개발 작업과 변경 Source
5. 인수조건·테스트 연결
6. 아직 남은 미확정 사항과 실행 차단 여부

그리고 데이터 Mapping, DB/Schema, 공통코드, Transaction, 동시성, Interface, 오류처리, 보안, 로그/감사, 성능·Migration, Architecture 표준 같은 항목은 **해당 위험이 있는 변경에서만 추가 확인**한다.

과거 Formal 계약의 17개 전체 항목 체계는 호환성 검증에 남아 있지만 신규 프로젝트의 기본 작성 방식은 아니다.

Program Spec에는 실제 개발에 필요한 경우 다음 기술정보를 유지한다.

- File/Class/Method
- JSP/XML/Query
- Table/Column
- Interface/Batch/Procedure
- Transaction/권한
- Source 변경 범위
- Test/Verification 연결

## 7. 작은 변경도 최소 분석은 유지한다

L1/L2는 문서 내용을 간결하게 할 수 있지만 Source를 수정하기 전 다음 의미 검증은 생략하지 않는다.

```text
요구 의도 확인
→ 현재 Source 확인
→ 영향 범위 확인
```

내부 Runtime은 이 세 가지가 확인되었는지를 기계적으로 검증하지만, 사람이 내부 상태 코드 이름을 문서에 직접 쓰거나 외울 필요는 없다.

문서 존재 여부는 Change Level 하나로 정하지 않고 선택 Profile이 결정한다.

- 조건부 문서: 조건이 맞을 때 생성
- Profile 필수 문서: 낮은 Level에서도 유지하되 간결하게 갱신

## 8. 생성 문서를 수정하고 싶을 때

오탈자·레이아웃 수준을 제외하면 파일만 직접 고치기보다 Agent에게 **어느 문서의 어떤 의미를 어떻게 바꿀지** 말한다.

예:

```text
RQ-0042 Work Unit SDD의 업무 규칙에서
월 마감 이후 재계산 정책을 "급여 마감 전까지만 허용"으로 바꿔줘.
```

Agent는 내용에 따라 다음 흐름을 선택한다.

| 수정 내용 | 처리 |
|---|---|
| 요구사항·업무규칙·범위·목표 동작 변경 | `/change` |
| 현재 Source·DB·Mapping·구현결과 재조사 | `/work` |
| 오탈자·표현·레이아웃 | 생성 문서만 수정 가능 |

생성 문서를 직접 수정했다고 프로젝트 기준 정보가 자동 변경되지는 않는다.

## 9. Customer 문서는 별도 표현을 사용한다

Engineering의 Java Method/Table/Query 같은 기술 세부를 Customer 문서에 그대로 복사하지 않는다.

기술 근거에서 고객에게 필요한 업무 의미를 확인할 수 있으면 다음처럼 바꾼다.

```text
기술 표현:
WorkPlanService.savePlan()에서 EMP_WORK_PLAN 저장

고객 표현:
근무계획을 등록하면 입력한 내용이 시스템에 저장됩니다.
```

업무 의미를 확정할 수 없으면 추측하지 않고 추가 확인이 필요하다고 표시한다.

상세: `15_고객문서_미리보기_가이드.md`

## 10. 사람에게 내부 Runtime 분류를 외우게 하지 않는다

사람용 문서에는 업무 의미와 필요한 행동을 먼저 보여준다. 내부 JSON key, 상태 enum, Source hash, queue 식별자, guard code 등을 사람이 직접 관리하는 입력 항목으로 만들지 않는다.

Framework 자체를 설명해야 할 때만 쉬운 한국어와 함께 내부 용어를 제한적으로 병기한다.

## 11. Project Custom Template

프로젝트 고유 Template은 Core 표준을 수정하지 않고 다음에 둔다.

```text
sdlc/custom/project/templates/
```

예:

```text
sdlc/custom/project/templates/hris-hunel/
├─ 01_업무정의서.md
└─ 02_작업지시서.md
```

어떤 Template을 실제 문서로 사용할지는 `sdlc/custom/project/tailoring/*.yaml`에서 정한다.

## 12. 검증

Profile 검증:

```bash
python sdlc/scripts/tailoring_runtime.py validate-profile --profile <PROFILE_ID>
```

사람용 Template은 다음을 확인한다.

- 빈칸 채우기 위주 Form이 아니라 Agent 초안 + Review 구조인가
- 실제 개발에 필요한 기술정보는 Engineering에 남아 있는가
- 고객 문서에는 내부 구현 세부가 불필요하게 노출되지 않는가
- 근거 없는 업무 사실을 Template이 강제로 요구하지 않는가
- Custom Profile의 output path와 Template 경로가 실제 존재하는가

## 13. 관련 문서

- Profile 선택/Custom: `03_TAILORING_설정가이드.md`
- 역할별 사용법: `05_이해관계자별_작업가이드.md`
- 고객문서: `15_고객문서_미리보기_가이드.md`
- 프로젝트 개발가이드: `16_프로젝트_개발가이드_Agent_적용가이드.md`
- 전체 CLI 기능: `18_HARNESS_CLI_기능_참조가이드.md`
