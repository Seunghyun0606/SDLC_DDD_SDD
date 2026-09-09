# SDLC Harness 시작하기 — v1.10.1

이 문서는 프로젝트 참여자가 **Framework 내부 구조를 외우지 않고 실제 작업을 시작하는 순서**만 설명한다.

## 1. 먼저 3가지만 이해한다

- **기준 정보**: 요구사항, 업무규칙, 범위, 결정의 프로젝트 기준이다.
- **개발자용 생성 문서**: 설계·개발·테스트를 위해 Agent가 계속 최신화하는 문서다.
- **고객용 생성 문서**: 고객 협의·제출·인수에 맞게 별도로 만드는 문서다.

개발자용 문서와 고객용 문서는 같은 기준을 참고하지만 **문서 수, 이름, 순번, Template은 서로 독립**이다.

## 2. 프로젝트 시작 순서

### 2.1 설정

```bash
python sdlc/scripts/harness.py setup --name <project> --mode <AUTO|GREENFIELD|BROWNFIELD|HYBRID>
python sdlc/scripts/harness.py check --setup
```

사람이 직접 관리하는 프로젝트 설정은 `.sdlc/project.yaml`이다.

- 설정 순서: `02_PROJECT_설정가이드.md`
- 모든 Config 옵션의 정확한 의미: `02A_PROJECT_CONFIG_옵션_상세가이드.md`
- 문서 종류를 프로젝트에 맞게 바꾸기: `03_TAILORING_설정가이드.md`

### 2.2 요구사항과 참고자료 넣기

대량 요구사항이나 고객 Excel을 처음 받을 때:

```bash
python sdlc/scripts/harness.py intake <requirements.xlsx>
```

요구사항과 PPTX/XLSX/DOCX/PDF 참고자료를 같이 받았다면 함께 Intake할 수 있다.

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx \
  --reference 기능개선안.pptx \
  --reference 현행업무정리.xlsx
```

상세: `11_INPUT_자료_준비가이드.md`

### 2.3 프로젝트 중 새 요구사항 한두 건 추가

전체 Excel을 다시 만들 필요가 없는 소수 신규 요구는 `rq-add`를 사용한다.

```bash
python sdlc/scripts/harness.py rq-add \
  --title "근무계획 승인 후 수정 제한" \
  --request "승인 완료된 근무계획은 일반 사용자가 수정할 수 없게 해줘."
```

Cursor에서는 `/rq-add`, 다른 Agent에서는 `sdlc/agent/skills/rq-add/SKILL.md`의 같은 규칙을 사용한다.

상세: `17_RQ_간편추가_가이드.md`

### 2.4 PM 작업목록 만들기

```bash
python sdlc/scripts/harness.py rq-list export \
  --format xlsx \
  --output docs/00_관리/RQ_작업관리.xlsx
```

PM은 담당자·일정·WBS·우선순위·메모 같은 컬럼을 자유롭게 추가해 다시 Import할 수 있다. 이 값은 업무 요구사항을 자동 변경하지 않는다.

Cursor에서는 `/rq-list`를 사용할 수 있다.

상세: `12_RQ_작업목록_운영가이드.md`

### 2.5 RQ와 참고문서 연결 검토

요구사항과 참고문서를 같이 Intake했다면 Harness가 RQ↔문서 연결 초안을 만들 수 있다. 연결 자체는 업무 사실 확정이 아니며 실제 작업에서 문서를 읽고 확인한 내용만 근거로 사용한다.

상세: `13_RQ_참고문서_레지스트리_가이드.md`

### 2.6 설계·개발·테스트 진행

```bash
python sdlc/scripts/harness.py work --target RQ-001
python sdlc/scripts/harness.py check RQ-001
```

다음처럼 구분한다.

```text
현재 Source 조사 / 상세설계 / 프로그램 매핑 / 개발 / 테스트 / 구현결과 보완
→ /work

요구사항 / 업무규칙 / 범위 / 목표 동작 자체 변경
→ /change
```

작은 변경이라도 Source를 수정하기 전에는 **요구 의도 → 현재 Source → 영향 범위**를 확인한다.

## 3. 기본 개발자용 문서

신규 프로젝트의 기본 Engineering Profile은 `ENGINEERING_SDD_COMPACT`다.

```text
docs/10_engineering/<TARGET>/
├─ 00_work-map.md
├─ specs/<TARGET>.md
└─ programs/<TARGET>.md   # 필요할 때만
```

- `00_work-map.md`: 요구 → 작업 → 프로그램/Source → 테스트 연결
- `specs/...`: 기능/업무 단위 Living SDD
- `programs/...`: 실제 Source 구현 차이를 별도 상세화할 필요가 있을 때 생성

산출물과 Template 관계는 `04_TEMPLATE_및_산출물_가이드.md`를 본다.

## 4. 기본 고객용 문서

기본 `CUSTOMER_STANDARD_3`는 다음 3종이다.

```text
docs/20_고객/<RQ>/
├─ A01_요구_업무_기능_합의서.md
├─ A02_영향_개발범위_공유서.md
└─ A03_테스트_인수_운영_결과서.md
```

```bash
python sdlc/scripts/harness.py customer-view --target RQ-001 --type solution_agreement
python sdlc/scripts/harness.py customer-view --target RQ-001 --type delivery_scope
python sdlc/scripts/harness.py customer-view --target RQ-001 --type acceptance_handover
```

Cursor에서는 `/customer-view`를 사용할 수 있다. 고객 문서는 없는 사실을 임의로 채우지 않고 현재 확인된 내용만 고객이 읽기 쉬운 표현으로 작성한다.

상세: `15_고객문서_미리보기_가이드.md`

## 5. 프로젝트 개발가이드와 Rule

프로젝트별 개발 기준은 Framework Core를 직접 고치지 않고 다음에 둔다.

```text
sdlc/custom/project/standards/   # Java/DB/Test/Security 등 개발 기준
sdlc/custom/project/rules/       # 반드시 지켜야 할 프로젝트 규칙/금지사항
```

상세: `16_프로젝트_개발가이드_Agent_적용가이드.md`

## 6. 한글 자료와 Windows 명령

MD/TXT/CSV 및 Build/Test/외부 Tool 출력은 OS 기본 인코딩만 믿지 않고 손실 없는 방식으로 처리한다. CMD/BAT와 PowerShell도 명시적인 실행 경계를 사용한다.

상세: `14_한글_인코딩_및_외부명령_가이드.md`

## 7. Brownfield 프로젝트

현재 Source/DB/Config에서 관찰한 기술 사실과 고객이 확정한 업무 기준을 구분한다. Source가 다르다는 이유만으로 업무 정책을 자동 변경하지 않는다.

상세: `07_BROWNFIELD_SSOT_현행화가이드.md`

## 8. 실제 읽는 순서

처음 프로젝트에 들어온 사람은 다음 순서면 충분하다.

1. `START_HERE.md`
2. `02_PROJECT_설정가이드.md`
3. `11_INPUT_자료_준비가이드.md`
4. `17_RQ_간편추가_가이드.md` — 프로젝트 중 소수 신규 요구가 있을 때
5. `12_RQ_작업목록_운영가이드.md`
6. `13_RQ_참고문서_레지스트리_가이드.md` — 참고자료가 있을 때
7. `04_TEMPLATE_및_산출물_가이드.md`
8. `05_이해관계자별_작업가이드.md`
9. 필요할 때 `03`, `07`, `14`, `15`, `16`
10. Config Key를 정확히 확인해야 할 때만 `02A`

`01_STANDARD_SCAFFOLD_사용가이드.md`와 `06_CUSTOM_SCAFFOLD_적용가이드.md`는 과거 링크 호환을 위해 Framework Repository에만 남아 있는 Compatibility Notice이며 **신규 Project Scaffold에는 배포되지 않고 읽기 순서에도 포함하지 않는다.**

## 9. Legacy Formal Profile 주의

`STANDARD_3`, `STANDARD_5`, `STAGE_ORIENTED_FULL`은 신규 Project Scaffold의 기본 포함 항목이 아니다. Framework 관리자가 기존 프로젝트 호환이 필요한 경우 Project Scaffold 생성 시 Legacy Compatibility package를 명시적으로 포함했을 때만 사용할 수 있다.

신규 프로젝트 기본값은 다음이다.

```text
Engineering → ENGINEERING_SDD_COMPACT
Customer    → CUSTOMER_STANDARD_3
PM          → PM_STANDARD
```

## 10. Framework와 실제 Project 경계

Framework 관리자가 다른 Repository용 Project Scaffold를 만들 때만 Framework Repository에서 다음 도구를 사용한다.

```bash
python sdlc/scripts/build_project_scaffold.py \
  --root . \
  --output <outside-target-directory>
```

Legacy Formal Profile까지 배포해야 할 때만 Framework 관리자가 다음 옵션을 추가한다.

```bash
--include-legacy-compatibility
```

`build_project_scaffold.py`와 `project-scaffold-contract.json`은 Framework distribution tool이며 생성된 Project Scaffold 안에는 포함되지 않는다. 배포받은 프로젝트 참여자가 자기 프로젝트 안에서 다시 Scaffold를 생성하는 흐름이 아니다.
