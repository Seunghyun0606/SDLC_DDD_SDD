# HRIS / hunel Custom Engineering Template 검토

기준 Branch: `SDLC_DESIGN_SESSION_FIRST/hris-hunel-engineering/v1.10.1`
기준 Framework: `SDLC_DESIGN_SESSION_FIRST/projection-separation/v1.10.0`

## 1. 결론

첨부 HRIS 문서는 현재 Framework에 **Custom Engineering Projection**으로 적용하는 것이 적합하다.

다만 문서 전체를 Standard로 승격하지 않는다.

- 업무정의서의 Evidence/Scenario/Rule/AC/Traceability 개념은 현재 Work Unit SDD와 같은 의미 계층이다.
- 작업지시서의 조건부 구현 Block, Source Write Guard, Source Change List는 범용성이 있어 Standard Engineering Template에 일반화할 수 있다.
- `hunelCommonDS`, ibsheet, doAction, SQLResource, `chkAuthMenu`, 3-file set, Procedure 운영 경계는 기술스택 고유이므로 Custom Template에 남긴다.

## 2. Standard 대비 비교

| 관점 | ENGINEERING_SDD_COMPACT | HRIS 예시의 장점 | HRIS 예시의 단점/위험 | 처리 |
|---|---|---|---|---|
| 문서 수 | Work Map + Work Unit SDD + 조건부 Program Spec | 업무정의 + 작업지시 2문서로 개발자 이해가 빠름 | 특정 프로젝트 구조를 Framework 기본으로 오해할 수 있음 | Custom 2문서 Profile |
| Work Unit 경계 | 기존에는 간략 | Unit≠Program, 1:N 관계가 명확 | HRIS Program ID 중심으로 과적합 가능 | Standard에 경계 원칙만 반영 |
| AS-IS 근거 | Evidence 중심 | Coverage Gap을 별도 추적 | 상세 표가 과도하면 문서 유지비 증가 | Standard에 Compact Coverage Gap 반영 |
| TO-BE | Functional Intent 중심 | 정상/대안/예외 Flow가 명확 | Semantic Template과 중복될 수 있음 | Engineering View에는 요약/Reference만 유지 |
| 구현 상세 | 기술중립 | JSP/Java/XML 연결을 개발자가 바로 사용 | hunel 외 프로젝트에는 부적합 | Custom 작업지시서 |
| 조건부 구조 | Risk-triggered Conditional | 화면 유형별 필요한 Block만 작성 | 화면유형 하드코딩은 일반화 어려움 | Standard에는 Generic Block, Custom에는 hunel Block |
| Open 관리 | Readiness/Open Guard | BLOCK/ITERATE로 실무 진행성이 좋음 | Framework Hard Block과 의미 충돌 가능 | `SOURCE_BLOCK/ITERATE/ALERT`로 재정의 |
| Source 범위 | Implementation Target 중심 | Agent 직접수정과 DBA 적용 경계가 명확 | Procedure 전용으로 보일 수 있음 | `DIRECT_MODIFY/SCRIPT_OUTPUT/HUMAN_OPERATION/VERIFY_ONLY`로 일반화 |
| 권한 | Security conditional | HRIS 프로파일 권한이 상세 | Business 권한과 구현 권한이 한 문서에 섞임 | 업무정의=의미, 작업지시=hunel 구현으로 분리 |

## 3. Standard Template 개선

다음은 HRIS를 제거해도 범용 가치가 있어 `sdlc/templates/engineering/standard/`에 반영했다.

1. Work Unit과 Program의 1:N 관계 및 경계/분할 근거
2. AS-IS Evidence와 Coverage Gap의 분리
3. Generic Conditional Implementation Block
4. Source Change Boundary와 실행 책임 분리
5. `SOURCE_BLOCK / ITERATE / ALERT` 실행 영향 분류
6. AS-BUILT에서 계획 밖 영향과 Drift를 명시

Standard에는 다음 hunel 용어를 넣지 않는다.

- `hunelCommonDS`
- ibsheet
- doAction
- CUDSQLManager
- SQLResource
- chkAuthMenu/chkAuthTrans

## 4. Custom Template 구조

```text
sdlc/custom/project/templates/hris-hunel/
├─ 01_업무정의서.md
├─ 02_작업지시서.md
└─ README.md

sdlc/custom/project/tailoring/
└─ CUSTOM_HRIS_HUNEL_ENGINEERING.yaml

sdlc/custom/project/config/
└─ project.hris-hunel.example.yaml
```

### 업무정의서
- Work Unit 단위
- 기술 독립 WHAT/WHY
- AS-IS Evidence와 Coverage Gap
- Scenario/Rule/상태/논리 Data/업무 권한
- AC/영향/Open/Traceability
- hunel 구현 상세를 포함하지 않음

### 작업지시서
- Program/개발 Target 단위
- hunel Pattern 판정
- B-SHEET/B-TAB/B-VUE/B-APPL/B-PROC/B-POPUP/B-DYNAMIC/B-AUTH/B-MIGRATION 조건부 Block
- JSP/Java/XML Mapping
- Source Change Boundary
- Readiness / Source Write Guard
- Traceability / AS-BUILT

## 5. Config 적용

Core Config를 수정하지 않는다. 프로젝트 root `.sdlc/project.yaml`의 Engineering Profile만 선택한다.

```yaml
documents:
  engineering:
    profile: "CUSTOM_HRIS_HUNEL_ENGINEERING"
    manual_edit_policy: "HUMAN_REVIEW"
    freshness: "CANONICAL_REVISION"
```

현재 v1.10의 정식 selector는 `documents.engineering.profile`이다. `documents.internal.profile`은 migration 호환 alias이며 신규 Config에서는 사용하지 않는다.

`template_set` 키는 현재 Project Config Contract의 정식 selector가 아니므로 추가하지 않는다. Template 선택은 Tailoring Profile이 담당한다.

Customer/PM Profile은 독립이다.

```yaml
  customer:
    profile: "CUSTOMER_STANDARD_3"
  pm:
    profile: "PM_STANDARD"
```

## 6. 검증

추가 회귀 테스트:

`tests/test_hris_hunel_custom_engineering_profile.py`

검증 내용:

- Custom Profile/Template 파일 존재
- Config 예제가 Engineering Profile selector를 사용
- `template_set`을 사용하지 않음
- Standard Engineering Template에 hunel 전용 용어가 없음
- Standard에 Work Unit/Coverage Gap/Conditional Block/Source Change Boundary가 존재
- hunel 전용 용어는 Custom 작업지시서에 존재

GitHub Actions는 본 작업 시점에 해당 Commit에 연결된 Workflow Run이 생성되지 않아 CI PASS를 주장하지 않는다. 최종 병합 전 Repository 표준 Test Suite 실행이 필요하다.
