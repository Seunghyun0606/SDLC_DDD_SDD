# Template 역할 구분

이 디렉터리의 Template은 모두 같은 목적이 아니다. v1.10부터 아래 역할을 정식 기준으로 사용한다.

| 경로 | 역할 | 신규 프로젝트에서의 의미 |
|---|---|---|
| `semantic/` | SDLC Stage 의미 구조 | Requirement/Analysis/Impact/Design/Program/Test/Verify 등 Agent의 Stage 실행용 Semantic Template |
| `engineering/` | Engineering Projection | 개발자/설계자가 검토하는 Work Map, Work-unit SDD, Program Spec |
| `customer/` | Customer Projection | 고객 합의/범위/인수 등 고객 커뮤니케이션용 Generated View |
| `management/` | PM/관리 View | 요구사항 검토 등 관리 관점 Template |
| `br-intake/` | 외부 BR 입력 보조 | 비정형 고객문서/BR 인입 검토용 Template |
| `tailoring/standard/` | Legacy/Formal Projection Template | `STANDARD_3`, `STANDARD_5` 같은 기존 정형 산출물 Profile이 사용할 최종 문서 Template |

## semantic과 tailoring의 차이

`semantic/*.md`는 **한 Stage에서 어떤 의미를 분석·작성해야 하는지**를 정의한다.

`../tailoring/standard/*.yaml`은 Markdown Template이 아니라 **Projection Profile**이다. 어떤 Stage/Canonical 정보를 어떤 최종 문서 Template에 연결하고 어디에 출력할지를 정의한다.

즉:

```text
Canonical + Stage Evidence
        ↓
semantic/                 # 단계별 의미 구조
        ↓
Tailoring Profile         # 조립/선택 규칙
        ↓
engineering/ | customer/ | tailoring/standard/
                            # 최종 Projection Template
```

## `tailoring/standard/*.md`의 목적

이 폴더의 Markdown은 Agent Stage 실행용 Semantic Template이 아니다. 기존 SI/SM 프로젝트에서 익숙한 **정형 문서 단위로 Projection을 만들기 위한 Legacy/Formal 출력 Template**이다.

### STANDARD_3용 3종

| Template | 목적 | 주요 입력 Stage |
|---|---|---|
| `01_업무정의서.md` | 요구, 확인사항, 업무 Process, 영향/현행 근거를 한 문서로 통합 | DECOMPOSE, CLARIFY, PROCESS, DISCOVERY, IMPACT, KNOWLEDGE_PROMOTION |
| `02_상세설계서.md` | 기능설계부터 프로그램/구현/테스트/검증 내용을 하나의 상세설계 문서로 통합 | DESIGN, PROGRAM, DEVELOPMENT, TEST, VERIFY |
| `03_화면설계서.md` | UI가 있는 경우 화면 흐름·입출력·행위·테스트 관점을 별도 문서로 제공 | DESIGN, PROGRAM, DEVELOPMENT, TEST |

### STANDARD_5용 5종

| Template | 목적 | 주요 입력 Stage |
|---|---|---|
| `11_요구사항정의서.md` | 요구사항과 미확정/확인 내용을 정형 요구사항 문서로 정리 | DECOMPOSE, CLARIFY |
| `12_업무프로세스설계서.md` | 업무 Process, AS-IS 근거, 영향 분석을 업무 흐름 중심으로 정리 | PROCESS, DISCOVERY, IMPACT |
| `13_기능화면설계서.md` | 기능 동작과 화면/사용자 흐름을 설계 관점으로 정리 | DESIGN |
| `14_프로그램설계서.md` | 구현 Program/Source Mapping과 개발 내용을 정형 프로그램 설계서로 정리 | PROGRAM, DEVELOPMENT |
| `15_테스트인수결과서.md` | Test, Verify, 운영/인수 결과를 최종 확인 문서로 정리 | TEST, VERIFY, KNOWLEDGE_PROMOTION |

신규 프로젝트 기본은 `ENGINEERING_SDD_COMPACT`이며, 위 3종/5종 Template은 고객사나 프로젝트가 기존 정형 문서 체계를 요구할 때만 명시적으로 선택한다.

## v1.10 경로 원칙

Stage Semantic Template의 정식 경로는 오직 `sdlc/templates/semantic/`이다. 별도의 호환 Template 경로를 두지 않으며 Runtime, Contract, Profile, Test, Guide도 같은 용어와 경로를 사용한다.
