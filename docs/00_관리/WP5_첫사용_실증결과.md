# WP-5 첫사용 실증 결과

## 목적

이 문서는 Session 5 / WP-5에서 확인한 첫사용 Evidence를 기록한다. 기존 문서의 `PASS`, `READY`, `VALIDATED` 문구를 구현 또는 실제 사용자 실증 근거로 사용하지 않는다.

검토 기준 사용자 경험은 다음이다.

> 프로젝트 자료 제공 → Agent 초안 → 사람이 확인해야 할 항목만 결정 → Agent 문서 완성 → 다음 단계 자동 안내

## 확인한 기존 문제

### 1. Provider 미연결이 setup 실패처럼 보였다

기존 내부 bootstrap은 Provider command가 없으면 `CONFIGURED_PROVIDER_REQUIRED`와 non-zero exit를 반환한다. 내부 Runtime 관점에서는 유효한 경계지만, 공식 첫사용 명령에서도 그대로 노출되면 프로젝트 설정과 요구사항 intake까지 실패한 것으로 오해하기 쉽다.

WP-5 공식 `harness.py setup/check --setup`에서는 프로젝트 설정이 정상이고 Provider만 없는 경우 `SETUP_READY_PROVIDER_PENDING`으로 구분한다. setup과 intake는 계속 진행할 수 있고 Provider는 첫 `work` 전에만 필요하다.

### 2. Provider를 나중에 연결하려면 내부 JSON 편집 또는 `--force`가 필요했다

최초 setup이 만든 `sdlc/config/agent-provider.json`이 이미 존재하면, 나중에 `setup --provider-command ...`를 실행해도 기존 파일 보존 규칙 때문에 Provider가 갱신되지 않았다. 사용자는 내부 JSON을 직접 편집하거나 `.sdlc/project.yaml`까지 다시 쓰는 `--force`를 사용할 가능성이 있었다.

WP-5 공식 setup은 명시적으로 `--provider-command`가 들어온 경우 Provider 설정만 갱신하고 `.sdlc/project.yaml`은 보존한다.

### 3. `provider_class=EXTERNAL_AGENT` 라벨이 실제 Agent 증거처럼 사용될 수 있었다

기존 반복성 테스트에는 결정론적 Python fixture에 `provider_class="EXTERNAL_AGENT"` 라벨만 붙여도 `actual_agent_provider_executed=true`를 기대하는 경우가 있었다.

WP-5에서는 이를 제거했다. 반복성 Runner가 증명하는 범위는 Provider command 실행 여부, Stage Result validation, 의미 fingerprint 일치율까지다. Provider identity는 Runner가 검증하지 않으며 실제 저수준 Agent 수행 여부는 별도 관찰 Pilot이 필요하다.

## Behavioral first-use Pilot

대상은 내부 함수를 직접 호출하지 않고 공식 CLI만 사용하는 다음 흐름이다.

1. `harness.py setup`
2. `harness.py check --setup`
3. 표준 2행 Header XLSX `harness.py intake`
4. 동일 프로젝트 설정을 보존한 상태에서 Provider command 연결
5. `harness.py work --target RQ-001`
6. `BUSINESS_POLICY` 판단 항목 1건만 Human review로 분리
7. Source 조사 가능 항목 1건은 Agent-owned `CHECK_REQUIRED`로 유지
8. `harness.py review --answer ...`
9. Human 결정 provenance 기록
10. Business field 자동 변경 없음
11. 다음 `work` 명령 안내

이 Pilot의 Provider는 **Behavioral fixture**다. 실제 External Agent가 아니다. `분석가 김민수`, `승인 주체는 팀장으로 한다` 같은 값도 테스트 시나리오의 예시이며 실제 사용자 관찰 기록이 아니다.

## 관측된 Behavioral CI

WP-5 수정 후 PR Workflow에서 다음을 직접 관측했다.

- `python -m unittest discover -s tests -v`: **253 tests, OK**
- WP-5 black-box first-use Pilot: **1 test, OK**
- Mermaid label 검사: **118 Markdown files checked**
- Worklist sync quality: SUCCESS
- P0 P1 Production Readiness: SUCCESS
- Docs quality: SUCCESS
- Greenfield Work Executor E2E: SUCCESS
- Public Brownfield Pilot: SUCCESS

이 결과는 Runtime wiring과 Behavioral contract의 관측 증거다. 실제 Agent 의미 품질 또는 실제 Human first-use usability 증거로 사용하지 않는다.

## Evidence 판정

| Evidence 층 | 현재 상태 | 근거/한계 |
|---|---|---|
| Document | UPDATED | START_HERE와 이 결과 문서에 first-use 경계 명시 |
| Contract | REUSED | 기존 Harness/Agent 실행 계약을 유지하며 Runtime 해석을 더 엄격하게 적용; 새 Contract 추가 없음 |
| Config | UPDATED | repeatability profile에서 Provider class는 선언임을 명시 |
| Runtime | UPDATED | 공식 setup/check handoff와 repeatability evidence interpretation 변경 |
| Behavioral Test | CI_PASS | 253 tests OK, black-box first-use Pilot OK, 5개 PR Workflow SUCCESS |
| External low-level Agent empirical | NOT_RUN | 실제 Agent Provider 관찰 실행 없음 |
| Human first-use | NOT_RUN | 실제 분석가·설계자·개발자·QA 참여 관찰 없음 |

## 실제 Agent/Human 실증에서 반드시 기록할 항목

실제 Pilot에서는 최소 다음을 관찰한다.

- 사용자가 설계자 설명 없이 시작 문서를 찾아 실행할 수 있었는가
- setup/intake/work/review 중 막힌 지점은 어디인가
- Agent가 Evidence로 초안 가능한 내용을 사람에게 되묻지 않았는가
- Human review 질문 중 실제 판단권한이 아닌 질문 비율은 얼마인가
- OPEN을 근거 없이 채운 사례가 있는가
- 사용자 문서와 Machine JSON을 혼동한 사례가 있는가
- 답변 후 Agent가 문서를 정확히 갱신했는가
- 다음 단계 안내만으로 계속 진행할 수 있었는가

실제 관찰이 이루어지기 전에는 이 표의 두 empirical 항목을 `PASS`로 변경하지 않는다.
