# 프로젝트 Input 자료 준비 가이드

이 문서는 프로젝트 시작 시 또는 진행 중 Harness에 제공할 **요구사항·고객문서·업무자료·개발표준**을 어디에 두고 어떤 진입점을 사용할지 설명한다.

기본 원칙은 **원본을 Harness 전용 Template으로 다시 작성하지 않는 것**이다.

## 1. 어떤 입력을 어떤 기능으로 넣는가

| 상황 | 기본 기능 |
|---|---|
| 최초 요구사항 Excel/CSV | `intake` |
| 대량 요구사항을 파일로 추가 | `intake` |
| 프로젝트 중 새 요구사항 한두 건 | `rq-add` |
| 기존 RQ의 업무 의미/정책/범위 변경 | `/change` |
| 담당자/일정/WBS/메모 | `rq-list` |
| RQ에 참고할 규정/회의록/업무문서 연결 | `rq-ref` |

소수 신규 RQ 상세는 `17_RQ_간편추가_가이드.md`를 본다.

## 2. 정형 요구사항 Excel/CSV

원본 요구사항 파일을 그대로 Intake한다.

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx
```

Harness는 다음을 보존한다.

- 원본 행
- 외부 요구사항 ID
- 원문
- 원본 위치와 Hash

비슷한 문구를 임의로 확정 병합하거나 원문에 없는 업무규칙을 새로 만들지 않는다. 서로 충돌하거나 의미가 다른 입력을 Harness가 자동으로 하나의 업무 사실로 정리했다고 가정하지 않는다.

### 기준 정보에 반영하기 전에 후보만 확인

먼저 후보만 검토하고 기준 정보는 바꾸지 않으려면 `--candidate-only`를 사용한다.

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx --candidate-only
```

이 모드에서는 후보/검토 결과를 만들 수 있지만 Canonical Store는 변경하지 않는다.

### 비표준 컬럼 Mapping

표준 컬럼을 인식하기 어려운 비표준 Excel만 선택적으로 Column Mapping을 사용한다.

예시 Profile:

```text
sdlc/config/requirement-intake-columns.example.yaml
```

적용 예:

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx \
  --profile sdlc/config/requirement-intake-columns.example.yaml
```

이 Profile은 모든 프로젝트가 복사해야 하는 필수 설정이 아니라 비표준 입력용 예시다.

`--json-out`, `--report-out`, `--manifest-json`, `--manifest-report`는 Runtime/보고서 출력 위치를 별도로 지정해야 할 때 쓰는 고급 옵션이다. 전체 CLI 옵션의 위치는 `18_HARNESS_CLI_기능_참조가이드.md`를 본다.

## 3. 요구사항과 참고자료를 같이 받은 경우

실제 고객 전달 패키지는 다음처럼 들어올 수 있다.

```text
고객 전달 패키지
├─ 요구사항목록.xlsx
├─ 기능개선안.pptx
├─ 현행업무정리.xlsx
├─ 운영회의결정.docx
└─ 업무규정.pdf
```

이 경우 요구사항과 참고자료를 같이 전달할 수 있다.

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx \
  --reference 기능개선안.pptx \
  --reference 현행업무정리.xlsx \
  --reference 운영회의결정.docx \
  --reference 업무규정.pdf
```

참고자료가 한 폴더에 모여 있다면:

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx \
  --reference-dir br-input/originals
```

Requirement 파일 자체는 참고문서 후보에서 제외한다.

지원 참고 형식:

```text
PPTX / XLSX / DOCX / PDF / CSV / MD / TXT
```

PDF에 텍스트 레이어가 없으면 자동 추출이 충분하지 않을 수 있으며 별도 수동 추출/OCR이 필요할 수 있다.

## 4. Intake 시 참고자료에서 하는 일

참고자료가 함께 들어오면 Harness는 다음 순서로 처리한다.

```text
요구사항 Intake
→ RQ 생성
→ 참고자료 원본 보존/등록
→ 문서 내용 추출
→ RQ↔문서 관련 후보 생성
→ Agent가 실제 내용을 읽고 검토
→ 사람 검토가 필요하면 제시
→ 실제 /work에서 근거로 사용
```

자동 후보 연결은 검색 범위를 줄이는 초안이지 업무 사실 확정이 아니다.

RQ↔참고문서 검토·Export/Import 상세는 `13_RQ_참고문서_레지스트리_가이드.md`에만 설명한다.

## 5. 원본 고객문서 보관

고객에게 받은 원본 PDF/DOCX/XLSX/PPTX/MD/TXT/CSV는 원형을 보존한다.

권장 구조:

```text
br-input/
├─ originals/
│  ├─ 규정.pdf
│  ├─ 운영매뉴얼.docx
│  ├─ 기능개선안.pptx
│  └─ 현행업무정리.xlsx
├─ manifest.yaml
├─ context.md       # 선택
├─ glossary.csv     # 선택
└─ decisions/       # 선택
```

원본 파일을 프로젝트 산출물 Template에 맞춰 다시 작성하거나 덮어쓰지 않는다.

## 6. Manifest

참고자료는 `br-input/manifest.yaml`에서 안정적인 `document_id`와 원본 위치를 관리한다.

최소 예:

```yaml
documents:
  - document_id: DOC-001
    path: originals/규정.pdf
```

자동 Intake를 사용하면 기본 `document_id`, `path`, `title`, `source_hash` 등을 Harness가 만들 수 있다.

알고 있는 경우 다음 Metadata를 보강할 수 있다.

- 문서 제목
- 문서 종류
- 권위/담당부서
- 현재 유효 여부
- 적용범위
- 관련 시스템

모르는 값은 임의로 만들지 않는다.

## 7. 개발표준 / Agent Rule / 업무원본 / 용어집을 구분한다

```text
sdlc/custom/project/standards/
→ Java/DB/Test/Security/배포 등 개발자가 따라야 할 기준

sdlc/custom/project/rules/
→ Agent가 반드시 지켜야 할 프로젝트 규칙/금지사항

br-input/originals/
→ 업무규정, 회사내규, 회의자료, 운영매뉴얼 등 원본 근거자료

br-input/context.md
→ 프로젝트/업무 배경 설명

br-input/glossary.csv
→ 프로젝트/고객 용어집
```

고객에게 받은 개발표준 PDF 원본은 `br-input/originals/`에 보존하고, 실제 개발 때 반복 사용할 정리본이 필요하면 `sdlc/custom/project/standards/`에 현재 적용 기준을 정리한다.

상세: `16_프로젝트_개발가이드_Agent_적용가이드.md`

## 8. 프로젝트 중 새 요구사항이 추가된 경우

### 한두 건 / 자연어 요청

```bash
python sdlc/scripts/harness.py rq-add \
  --title "승인 후 수정 제한" \
  --request "승인 완료된 근무계획은 일반 사용자가 수정할 수 없게 해줘."
```

상세: `17_RQ_간편추가_가이드.md`

### 대량 / 고객 파일 전달

```bash
python sdlc/scripts/harness.py intake 추가요구사항.xlsx
```

참고자료도 같이 받았다면 `--reference` 또는 `--reference-dir`를 함께 사용한다.

기존 확정 업무 기준을 새 Intake 자료만으로 자동 덮어쓰지 않는다.

## 9. 요구사항 없이 참고자료만 추가된 경우

새 규정·회의록·업무자료만 추가됐다면 원본을 `br-input/originals/`에 보존하고 Manifest/Registry에 등록한 뒤 기존 RQ와의 관련성을 검토한다.

이 연결만으로 업무규칙이 자동 변경되지는 않는다. 실제 `/work`에서 문서를 읽고 특정 사실에 사용했을 때 근거 이력을 남긴다.

상세: `13_RQ_참고문서_레지스트리_가이드.md`

## 10. 사람이 보는 주요 결과

대표적인 프로젝트 관리 View는 다음 위치에 생성된다.

```text
docs/00_관리/요구사항_인입결과.md
docs/00_관리/RQ_생성근거.md
docs/00_관리/RQ_참고문서_초안검토.md
docs/00_관리/RQ_참고문서_연결목록.md
docs/00_관리/RQ_작업목록.md
```

Machine Runtime 결과는 `sdlc/runtime/` 아래에서 관리되며 일반 사용자가 직접 수정하지 않는다.

## 11. Intake 다음 작업

Intake가 반환한 실제 RQ ID를 사용한다.

```bash
python sdlc/scripts/harness.py rq-list export \
  --format xlsx \
  --output docs/00_관리/RQ_작업관리.xlsx

python sdlc/scripts/harness.py work --target RQ-001
```

참고자료가 함께 들어왔다면 첫 `/work` 전에 RQ↔문서 연결 초안과 실제 문서 내용을 검토한다.

## 12. Source Repository가 아직 없는 Brownfield

요구사항과 고객문서만 먼저 받은 경우 확인 가능한 업무 Context까지만 진행할 수 있다.

현재 Source 근거가 필요한 영향분석·구현설계는 Source Repository가 제공된 뒤 확인한다. Source가 없는데 Class/Method/Table을 임의로 만들어내지 않는다.

## 13. 관련 문서

- RQ 작업목록: `12_RQ_작업목록_운영가이드.md`
- RQ 참고문서: `13_RQ_참고문서_레지스트리_가이드.md`
- 소수 신규 RQ: `17_RQ_간편추가_가이드.md`
- 개발표준/Rule: `16_프로젝트_개발가이드_Agent_적용가이드.md`
- 한글/인코딩: `14_한글_인코딩_및_외부명령_가이드.md`
- 전체 CLI 기능: `18_HARNESS_CLI_기능_참조가이드.md`
