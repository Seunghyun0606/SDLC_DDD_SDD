# Standard 3 / Standard 5 / Full Tailoring 비교 Sample

> 동일 Canonical snapshot, 동일 RQ, 동일 Change Level, 동일 Runtime Stage sequence에서 Human Artifact grouping만 비교한다.
> 이 결과는 실제 Agent 작성 본문의 의미동등성을 주장하지 않는다.

## 재현 명령

```bash
python sdlc/scripts/generate_tailoring_profile_comparison.py \
  --root . \
  --store framework/samples/tailoring/comparison-canonical.example.json \
  --target RQ-COMP-001 \
  --change-level L3 \
  --out-json sdlc/runtime/tailoring-comparison.json \
  --out-md sdlc/runtime/tailoring-comparison.md
```

## 비교 기준

- Target: `RQ-COMP-001`
- Canonical revision: `7`
- Canonical fingerprint: `sha256:7a119831c7e436eba7fdcf7992488bc485f32577493ee9770e0158d6e7ede7bf`
- Change Level: `L3 FEATURE`
- 비교 Stage: `DECOMPOSE → CLARIFY → PROCESS → DISCOVERY → IMPACT → DESIGN → PROGRAM → DEVELOPMENT → TEST → VERIFY → KNOWLEDGE_PROMOTION`
- Structural invariant 기대값: `PASS`

## 문서군 수

| Profile | 고유 Human Artifact 수 | Stage 보존 | Projection의 Business Truth 생성 |
|---|---:|---|---|
| Standard 3 (`STANDARD_3`) | 3 | YES | NO |
| Standard 5 (`STANDARD_5`) | 5 | YES | NO |
| Full (`STAGE_ORIENTED_FULL`) | 10 | YES | NO |

## Stage → Primary Human Artifact

| Runtime Stage | Standard 3 | Standard 5 | Full |
|---|---|---|---|
| `DECOMPOSE` | `business_definition` | `requirement_definition` | `requirement` |
| `CLARIFY` | `business_definition` | `requirement_definition` | `interview` |
| `PROCESS` | `business_definition` | `process_design` | `process` |
| `DISCOVERY` | `business_definition` | `process_design` | `impact` |
| `IMPACT` | `business_definition` | `process_design` | `impact` |
| `DESIGN` | `detail_design` + `screen_design` | `functional_screen_design` | `functional_design` |
| `PROGRAM` | `detail_design` + `screen_design` | `program_design` | `program_spec` |
| `DEVELOPMENT` | `detail_design` + `screen_design` | `program_design` | `implementation_result` |
| `TEST` | `detail_design` + `screen_design` | `test_acceptance` | `test` |
| `VERIFY` | `detail_design` | `test_acceptance` | `verification` |
| `KNOWLEDGE_PROMOTION` | `business_definition` | `test_acceptance` | `knowledge` |

Standard 3에서 `screen_design`은 Web UI Evidence 때문에 함께 선택되지만 Primary는 order가 앞선 `detail_design`이다. Runtime Stage 자체는 세 Profile에서 동일하다.

## Profile별 고유 산출물

### Standard 3 — 3종

- `business_definition` → `docs/10_산출물/RQ-COMP-001/01_업무정의서.md`
- `detail_design` → `docs/10_산출물/RQ-COMP-001/02_상세설계서.md`
- `screen_design` → `docs/10_산출물/RQ-COMP-001/03_화면설계서.md`

### Standard 5 — 5종

- `requirement_definition` → `docs/10_산출물/RQ-COMP-001/01_요구사항정의서.md`
- `process_design` → `docs/10_산출물/RQ-COMP-001/02_업무프로세스설계서.md`
- `functional_screen_design` → `docs/10_산출물/RQ-COMP-001/03_기능화면설계서.md`
- `program_design` → `docs/10_산출물/RQ-COMP-001/04_프로그램설계서.md`
- `test_acceptance` → `docs/10_산출물/RQ-COMP-001/05_테스트인수결과서.md`

### Full — 10종

- `requirement` → `docs/10_산출물/RQ-COMP-001/01_요구사항.md`
- `interview` → `docs/10_산출물/RQ-COMP-001/02_업무확인.md`
- `process` → `docs/10_산출물/RQ-COMP-001/03_업무프로세스.md`
- `impact` → `docs/10_산출물/RQ-COMP-001/04_영향분석.md`
- `functional_design` → `docs/10_산출물/RQ-COMP-001/05_기능설계.md`
- `program_spec` → `docs/10_산출물/RQ-COMP-001/06_프로그램설계.md`
- `implementation_result` → `docs/10_산출물/RQ-COMP-001/07_구현결과.md`
- `test` → `docs/10_산출물/RQ-COMP-001/08_테스트.md`
- `verification` → `docs/10_산출물/RQ-COMP-001/09_검증결과.md`
- `knowledge` → `docs/10_산출물/RQ-COMP-001/10_운영지식.md`

## 판정 경계

- 이 Sample의 PASS는 `Stage 유지 + Canonical 동일 + Projection 무변조`에 대한 구조 검증이다.
- 세 Profile에 대해 Agent가 실제 작성한 문서 본문의 의미가 완전히 동일하다는 Empirical Evidence는 아니다.
- 실제 사용자의 가독성·중복·누락·검토부담은 Human first-use Pilot에서 별도로 검증한다.
- External Agent의 Profile별 초안 품질/의미 보존도 별도 empirical pilot 대상이다.
