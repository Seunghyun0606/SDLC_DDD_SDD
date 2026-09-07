# 프로젝트 Input 자료 준비 가이드

이 문서는 요구사항 Excel과 기존 고객 문서처럼 **프로젝트 시작 시 Harness에 제공하는 자료**를 준비하는 방법만 설명한다. 원본을 Harness 전용 Template으로 다시 작성하지 않는 것이 기본 원칙이다.

## 1. 정형 요구사항 Excel

표준 요구사항 XLSX/CSV는 원본을 그대로 제공하고 공식 진입점으로 Intake한다.

```bash
python sdlc/scripts/harness.py intake <요구사항목록.xlsx>
```

Harness는 원본 행과 외부 요구사항 ID를 보존하고 RQ/FR Candidate를 만든다. 각 행을 곧바로 확정 Business Truth로 승격하지 않는다.

### 기본 원칙

- 외부 요구사항 ID와 원문을 보존한다.
- 동일한 명칭/업무구분을 이용한 Grouping은 Candidate다.
- 유사 문구는 자동 병합하지 않고 `GROUPING_REVIEW`로 남긴다.
- 일정/담당자 등 비필수 필드는 비어 있어도 Intake를 막지 않는다.
- 중복 외부 ID는 조용히 overwrite하지 않는다.
- 현재 문제, Business Rule, 기대 결과처럼 원문에 없는 사실을 Agent가 임의 확정하지 않는다.

표준 컬럼을 인식할 수 없는 고객 Excel만 별도 Column Mapping을 사용한다.

```text
sdlc/config/requirement-intake-columns.example.yaml
```

이 파일은 복사해야 하는 필수 프로젝트 설정이 아니라 **비표준 입력을 위한 선택 Mapping 예시**다.

## 2. 비정형 고객 문서 / BR 자료

PDF, DOCX, XLSX, PPTX, Markdown, TXT, CSV 등은 특정 BR Template로 다시 작성하도록 요구하지 않는다. 원본은 원형 그대로 보존하고 최소 Manifest만 함께 둔다.

권장 구조:

```text
br-input/
├─ originals/
│  ├─ 규정.pdf
│  ├─ 운영매뉴얼.docx
│  ├─ 요구목록.xlsx
│  └─ 회의록.docx
├─ manifest.yaml
├─ context.md       # 선택
├─ glossary.csv     # 선택
└─ decisions/       # 선택
```

Manifest의 최소 항목은 다음 두 개다.

```yaml
documents:
  - document_id: DOC-001
    path: originals/규정.pdf
```

정확도를 높이려면 문서 제목, 종류, 권위, 유효 여부, 담당부서, 적용범위, 관련 시스템, 페이지/Sheet/Slide 등의 Locator 정보를 추가한다. 모르는 값은 비우거나 `UNKNOWN`으로 둔다.

## 3. 원문과 정규화 결과의 관계

원문을 덮어쓰지 않는다.

```text
Original Source
  ↓ Evidence / Locator / Hash 보존
Normalized Candidate
  ↓ Review / Evidence 보강
Canonical Spec
```

BR 후보에서는 가능한 범위에서 조건, 주체, 행동/판단, 기대결과, 예외, 적용기간, 원본 위치를 분리한다. 서로 다른 문서가 충돌하면 자동으로 최신 문서를 정답으로 선택하지 않고 `BR_CONFLICT`와 확인 질문을 만든다.

## 4. 사람이 보는 결과와 Machine 결과

대표 결과는 다음처럼 분리된다.

```text
docs/00_관리/요구사항_인입결과.md        # 사람이 보는 Project-generated View
sdlc/runtime/intake/...                  # Machine Runtime 결과
sdlc/canonical/store.json                # Canonical Candidate/Truth Store
```

`docs/00_관리`는 Framework 검증보고서를 보관하는 폴더가 아니라 **실제 프로젝트에서 생성되는 PM/사용자용 관리 View 위치**로 사용한다.

## 5. Intake 다음 작업

Intake가 반환한 실제 Target을 그대로 사용한다.

```bash
python sdlc/scripts/harness.py work --target RQ-001
```

Source Repository가 아직 제공되지 않은 Brownfield 프로젝트라면 Source Evidence가 필요한 Impact/Implementation 확정은 보류하고, 확인 가능한 Requirement/Business Context까지만 Candidate로 진행한다.

## 6. 완성 예시

- `examples/요구사항_인입_완성예시.md`
- `examples/요구사항_정의_완성예시.md`

예시는 작성 양식이 아니라 Agent가 Evidence 범위 안에서 어디까지 초안을 작성하고 어디를 OPEN으로 남기는지 보여주는 참고자료다.
