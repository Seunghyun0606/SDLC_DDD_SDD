# SDLC Harness Agent Instructions

이 Repository는 Agent/IDE 제품에 종속되지 않는 SDLC Harness를 사용한다.

## 가장 먼저 읽을 파일

프로젝트 설정의 Human Source of Truth:
- `.sdlc/project.yaml`

`work` 요청의 Core Skill:
- `sdlc/agent/skills/work/SKILL.md`

Stage별 Reference:
- `sdlc/agent/skills/work/references/`

사람에게 보여주는 표현 기준:
- `sdlc/design/contracts/human-facing-language-contract.json`
- `sdlc/agent/skills/work/references/human-language.md`

## Work 요청 해석

다음은 모두 같은 SDLC work 의도로 처리한다.

- `work --target RQ-001`
- `/work --target RQ-001`
- `RQ-001 다음 단계 작업해줘`

현재 Agent가 Repository 파일 읽기/쓰기와 Shell 실행이 가능한 대화형 Agent라면 기본 실행모드는 `INTERACTIVE`다.
Cursor/Codex/Claude Code 등 제품명을 Project Config에 기록하거나 그 제품을 Business Evidence로 사용하지 않는다.

INTERACTIVE에서는:
1. `python sdlc/scripts/harness.py work --target <TARGET>` 실행
2. `INTERACTIVE_HANDOFF_READY`의 context/result/artifact 경로 확인
3. Core Skill과 Stage Reference에 따라 Artifact + `stage-result.json` 작성
4. finalize 명령 실행
5. Harness Validator가 성공 상태를 반환한 경우에만 Stage 완료로 보고

`.sdlc/project.yaml`에서 `agent.execution: HEADLESS`인 경우에는 현재 Agent가 별도 Provider를 대신 수행하지 말고 Harness의 Headless 경로를 사용한다.

## 사람에게 보여주는 표현

- HITL 질문, 사용자 설명, 사람용 문서 본문에서는 내부 Runtime 상태명과 Taxonomy를 그대로 노출하지 않는다.
- `DEFERRED`는 `보류`, `SOURCE_BLOCK`은 `개발 전 확인 필요`, `Recheck At`은 `다시 확인할 시점`, `Human Decision Queue`는 `추가 확인이 필요한 사항`으로 보여준다.
- `Canonical`, `Projection`, `Provenance`, `Evidence`는 일반 사용자 문맥에서 각각 `기준 정보`, `생성 문서`, `근거 이력`, `근거`를 우선 사용한다.
- `영속적`, `영속성`처럼 일반 사용자가 바로 이해하기 어려운 표현은 `DB에 저장되어 계속 유지되는`, `DB 저장 여부`처럼 풀어 쓴다.
- 필요한 전문용어를 없애야 하는 것은 아니다. 사람의 판단에 필요한 경우 쉬운 설명을 먼저 쓰고 전문용어를 괄호 안에 한 번 병기한다.
- 질문은 내부 코드 설명보다 `왜 필요한가`, `현재 확인한 내용`, `무엇을 결정해야 하는가`, `답하지 못하면 어떻게 되는가`, `언제 다시 확인하는가`를 먼저 보여준다.

## 공통 안전 규칙

- 모르는 업무 사실을 발명하지 않는다.
- Source 관찰은 Business Truth로 자동 확정하지 않는다.
- Target Graph 밖 기존 Canonical Entity를 임의 변경하지 않는다.
- 명시적 권한 없이 `CONFIRMED_BUSINESS`를 변경하지 않는다.
- protected branch write를 우회하지 않는다.
- `INTERACTIVE_HANDOFF_READY` 또는 `PLAN_READY`를 완료 상태로 표현하지 않는다.
- Artifact만 만든 뒤 Canonical 적용이 끝난 것처럼 말하지 않는다.

Host 자체의 편의 기능보다 `sdlc/agent/skills/work/SKILL.md`, Harness Contract, Runtime Validator가 우선한다.
