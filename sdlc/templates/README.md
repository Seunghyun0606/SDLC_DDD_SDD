# Template 역할 구분

이 디렉터리의 Template은 모두 같은 목적이 아니다. v1.10부터 아래 역할을 기준으로 구분한다.

| 경로 | 역할 | 신규 프로젝트에서의 의미 |
|---|---|---|
| `semantic/` | SDLC Stage의 의미 구조 | Requirement/Analysis/Impact/Design/Program/Test/Verify 등 Agent의 Stage 실행용 Semantic Template |
| `engineering/` | Engineering Projection | 개발자/설계자가 검토하는 Work Map, Work-unit SDD, Program Spec |
| `customer/` | Customer Projection | 고객 합의/범위/인수 등 고객 커뮤니케이션용 Generated View |
| `management/` | PM/관리 View | 요구사항 검토 등 관리 관점 Template |
| `br-intake/` | 외부 BR 입력 보조 | 비정형 고객문서/BR 인입 검토용 Template |
| `tailoring/standard/` | Legacy Compatibility | `STANDARD_3`, `STANDARD_5`, `STAGE_ORIENTED_FULL` 호환 산출물 Template. 신규 기본 구조가 아님 |

## semantic과 tailoring의 차이

`semantic/*.md`는 **한 Stage에서 어떤 의미를 작성해야 하는지**를 정의한다.

`../tailoring/standard/*.yaml`은 Template이 아니라 **Projection Profile**이다. 어떤 Stage/Canonical 정보를 어떤 최종 문서 Template에 연결하고, 어디에 출력할지를 정의한다.

즉:

```text
Canonical + Stage Evidence
        ↓
semantic/                 # 단계별 의미 구조
        ↓
Tailoring Profile         # 조립/선택 규칙
        ↓
engineering/ | customer/  # 최종 Projection Template
```

## `core` 경로

`sdlc/templates/core`는 더 이상 별도 Template 원본 폴더가 아니다. 기존 v1.9 Runtime/외부 참조 호환을 위해 `semantic`을 가리키는 **symlink compatibility alias**만 유지한다.

- 신규 코드/가이드/검증은 `sdlc/templates/semantic/`을 사용한다.
- 기존 `sdlc/templates/core/...` 참조는 동일 파일로 해석되어 동작한다.
- 두 위치에 Template 본문을 중복 보관하지 않는다.

Legacy compatibility가 제거 가능한 시점에는 `core` alias도 제거할 수 있다.
