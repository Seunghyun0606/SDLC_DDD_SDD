# /setup

프로젝트 최초 도입용 설정 Skill. 일반 사용자의 시작점은 `docs/00_시작/START_HERE.md`이며 실행은 `sdlc/scripts/harness.py` 하나로 통일한다.

## 사용자에게 보이는 설정은 하나

새 프로젝트에서 사람이 직접 유지하는 기본 설정 파일은 다음 1개다.

```text
.sdlc/project.yaml
```

`project-profile.yaml`, `source-profile.yaml`, Provider JSON, Contract, Starter Manifest를 먼저 학습시키지 않는다. Runtime이 호환/실행 파일을 계산한다.

```text
.sdlc/project.yaml                              # 사람이 보는 Source of Truth
        ↓ Runtime Resolver
.sdlc/runtime/effective/project-profile.json   # Machine runtime input
.sdlc/runtime/effective/source-profile.json    # Machine runtime input
.sdlc/runtime/effective/agent-execution.json   # INTERACTIVE / HEADLESS
.sdlc/runtime/effective/agent-provider.json    # Compatibility/provider runtime input
.sdlc/runtime/effective/project-context.json   # Agent project context
.sdlc/runtime/effective/config-usage.json      # Config 소비 판정
```

## 기본 원칙

1. 사용자는 프로젝트명·유형·진행 수준과 실제 프로젝트 자료만 제공한다.
2. Source root, Build/Test, Language/Framework/DB는 Repository에서 먼저 자동 탐색한다.
3. 자동으로 확인하지 못한 값은 `unresolved` 또는 OPEN으로 남긴다.
4. 빈 Template이나 수십 개 Config placeholder를 사람이 채우게 하지 않는다.
5. 업무정책·범위·승인·기술 선택처럼 사람의 판단권한이 필요한 것만 확인한다.
6. Source Evidence를 Business Truth로 자동 승격하지 않는다.
7. Dead Config와 잘못된 schema/mode/delivery/agent execution은 조용히 무시하지 않고 fail-closed 한다.
8. 내부 Machine taxonomy나 Agent 제품명을 사용자 업무 설정으로 요구하지 않는다.

## Agent 실행모드

기본값은 `INTERACTIVE`다. `.sdlc/project.yaml`에 `agent` 항목이 없어도 현재 Cursor/Codex/Claude Code/기타 IDE·CLI Agent에서 바로 Harness를 사용할 수 있다.

```yaml
agent:
  execution: INTERACTIVE
```

INTERACTIVE에서는 현재 대화 세션의 Agent가 Stage Agent다. 별도의 Provider command/API key 설정을 요구하지 않는다.

CI/Batch 등 Harness가 Agent를 직접 시작해야 할 때만 `HEADLESS`를 선택한다.

```yaml
agent:
  execution: HEADLESS
  provider:
    command:
      - python
      - path/to/provider_adapter.py
      - --context
      - "{context_path}"
      - --result
      - "{result_path}"
```

`HEADLESS`에서는 `agent.provider.command`가 필수다. 기존 `--provider-command`와 `sdlc/config/agent-provider.json`은 Legacy automation 호환용이며 신규 프로젝트 기본 설정으로 안내하지 않는다.

## Fast Path — 최초 질문

기본 setup에서는 프로젝트명, 프로젝트 유형, 진행 수준(Delivery Profile)을 확인한다. 나머지는 실제 자료/Repository를 우선 조사한다.

1. 프로젝트 유형 — `GREENFIELD / BROWNFIELD / HYBRID / AUTO`, 모르면 AUTO
2. 요구사항 또는 변경요청 위치 — XLSX/문서/Issue 등 실제 원본 위치
3. Source/Repository 위치 — Greenfield는 없음 가능
4. Build/Test 경로 — 모르면 Runtime이 탐색하고 OPEN 유지
5. 고객용 문서 필요 여부 — 프로젝트 커뮤니케이션 범위 확인

Agent Provider 선택은 기본 setup 질문이 아니다.

## 실제 첫 실행

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode AUTO \
  --delivery STANDARD

python sdlc/scripts/harness.py check --setup
```

INTERACTIVE이면 Provider 없이 `READY`가 정상이다.

## Zero-to-One Requirement 인입

표준 2행 Header XLSX는 별도 Column Profile 없이 공식 intake로 인입한다.

```bash
python sdlc/scripts/harness.py intake 요구사항목록.xlsx
```

Runtime은 다음을 수행한다.

```text
요구사항 원본
→ Source row / hash / 외부 ID 보존
→ RQ/FR Candidate 생성
→ 유사 그룹은 Review로 분리하고 자동 병합하지 않음
→ Canonical에 CANDIDATE/OPEN 등록
→ 실제 RQ-001 같은 Target 반환
→ 다음 work 명령 안내
```

현재 문제·기대 결과·Business Rule이 자료에서 확인되지 않으면 Agent가 발명하지 않고 OPEN으로 둔다. 기존 `CONFIRMED_BUSINESS`는 재인입 자료로 덮어쓰거나 낮추지 않는다.

인입 후 현재 Agent에서 다음처럼 진행한다.

```text
/work --target RQ-001
```

Host가 Slash Command를 지원하지 않으면 `RQ-001 다음 단계 작업해줘` 같은 자연어 요청을 Core Work Skill로 연결한다.

INTERACTIVE Runtime은 먼저 `INTERACTIVE_HANDOFF_READY`를 반환한다. 현재 Agent가 Artifact + `stage-result.json`을 만든 뒤 finalize하여 Validator가 성공한 경우에만 Stage 완료다.

## Mode별 시작 자료

- GREENFIELD → `sdlc/starter-kits/greenfield/`
- BROWNFIELD → `sdlc/starter-kits/brownfield/`
- HYBRID → Brownfield Source 기준과 Greenfield 신규 영역을 함께 사용
- AUTO → Repository Evidence로 Mode를 판정한 뒤 위 안내로 연결

## `.sdlc/project.yaml` 작성 원칙

Bootstrap은 확인된 값 중심으로 생성한다. Architecture/Coding/Data/Interface/Security/Deployment 같은 프로젝트 맥락은 확인된 값이 있을 때만 추가한다. 완성 예시는 `sdlc/config/project.example.yaml`을 참고하되 예시 값을 실제 프로젝트 사실처럼 복사하지 않는다.

Project Context는 실제 `work/change` plan에 포함된다. INTERACTIVE에서는 현재 Host Agent가 Context를 읽고, HEADLESS에서는 Provider `{context_path}`로 전달된다.

## 사람이 확인해야 할 것

- 유사 RQ 병합 여부
- 중복 외부 ID의 기준 원문
- 업무 정책·범위·승인·권한
- 실제 프로젝트의 기술 선택
- Source/문서에서 끝내 확인할 수 없는 OPEN

사람이 Requirement Template을 처음부터 채우는 것은 기본 절차가 아니다.

## Validation

```bash
python -m unittest tests.test_project_entry_config tests.test_agent_neutral_execution tests.test_requirement_intake_runtime -v
python sdlc/scripts/harness.py check --setup
python sdlc/scripts/validate_harness_structure.py .
python sdlc/scripts/validate_document_experience.py .
```

## 준비도 경계

Config/Runtime/Behavioral Test 성공은 각 Host Agent가 실제로 Core Skill을 발견하고 준수하는지를 자동 증명하지 않는다. Cursor/Codex/Claude Code 등 Cross-Agent Pilot은 별도 실증 대상이다.
