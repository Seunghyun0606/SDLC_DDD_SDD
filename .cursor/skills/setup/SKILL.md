# /setup

프로젝트 최초 도입용 설정 Skill. 실제 실행 Runtime은 `sdlc/scripts/bootstrap_project.py`이며 비숙련 사용자는 `sdlc/scripts/harness.py`만 사용해도 된다.

## 기본 원칙

신규 프로젝트 담당자가 Harness 내부 Profile/Rule/Contract 구조를 학습하지 않아도 시작할 수 있어야 한다. 최초 설정은 **Fast Path — 최초 5개 입력** 범위로 충분해야 하며, 실제 필요가 확인된 항목만 Advanced Setup으로 연다. 사용자가 여러 Config 파일을 직접 채우는 것을 기본 절차로 만들지 않는다.

## 실제 첫 실행

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD
```

Provider가 있으면 같은 명령에 `--provider-command`를 연결한다. Provider가 없다는 사실은 OPEN으로 유지하며 실제 문서 생성 성공으로 과장하지 않는다.

## Fast Path — 최초 5개 입력

1. **프로젝트 유형** — `GREENFIELD / BROWNFIELD / HYBRID / AUTO`, 모르면 AUTO
2. **요구사항 또는 변경요청 위치** — 원본 파일/폴더/이슈 기준점
3. **Source/Repository 위치** — Greenfield는 없음 가능
4. **Build/Test 경로** — 모르면 자동 탐색 후 OPEN
5. **고객용 문서 필요 여부** — internal / customer / both

이 입력으로 설정 초안을 만든 뒤 프로젝트 참여자는 Requirement Template을 직접 작성하지 않는다.

## 설정 다음 실제 사용자 흐름

```bash
python sdlc/scripts/harness.py check --setup
python sdlc/scripts/harness.py intake 요구사항목록.xlsx
```

표준 2행 Header XLSX는 별도 Column Profile 없이 인입한다. Runtime은 Candidate/OPEN 상태의 Canonical RQ/FR을 만들고 실제 `RQ-001` 같은 Target과 다음 `/work` 명령을 반환한다.

```bash
python sdlc/scripts/harness.py work --target RQ-001
```

사람이 해야 할 일은 유사 그룹 병합 여부, 업무 정책·범위·승인처럼 판단권한이 필요한 항목 확인이다. 현재 문제/기대 결과가 Source로 확인되지 않으면 Agent가 발명하지 않고 OPEN으로 둔다.

## 자동 탐색 범위

`bootstrap_project.py`는 build file, 흔한 Source/Test/Resource root, Language/Framework 신호, Schema/DDL, Build/Test command 후보를 Evidence로 조사한다. Git Repository라는 사실만으로 Brownfield라고 판정하지 않는다.

## 호환 Mapping과 Delivery

Starter Kit/Preset ID는 기존 자동화 호환을 위해 남아 있다.

- GREENFIELD → `greenfield-default`
- BROWNFIELD → `brownfield-auto`

이 값은 사용자가 선택해야 할 새 설정 항목이 아니다. 새 프로젝트의 문서량/Stage 제어는 `FAST / STANDARD / FULL` Delivery Profile로 처리한다.

## OPEN 처리

사람이 기본적으로 보는 상태는 `미확정 / 확인중 / 제안 / 확정 / 보류` 정도로 단순화한다. Machine taxonomy는 내부 metadata에 둔다. Business Truth는 권한자의 확인 없이 확정하지 않는다.

## Advanced Setup

다음은 실제 프로젝트 필요가 확인될 때만 연다.

- 고객 용어/고객 문서 Projection
- 비정형 문서 Evidence 추출
- 프로젝트별 결정 권한 Matrix
- Brownfield Framework별 Impact Adapter
- Project Overlay

기본 Customization 개념은 `Core → Project Overlay → Local Override` 세 단계만 노출한다.

## Validation

```bash
python sdlc/scripts/harness.py check --setup
python sdlc/scripts/validate_harness_structure.py .
python sdlc/scripts/validate_document_experience.py .
```

Intake와 `/work --plan-only` Behavioral Test가 통과해도 실제 외부 Agent 품질과 일반 사용자 First-use usability는 별도 실증 대상이다.
