# Greenfield First Prompt

이 Repository는 신규 Greenfield 프로젝트다. 별도 구두 설명 없이 아래 순서로 시작한다.

1. `sdlc/START_HERE.md`를 기준으로 고객 입력 파일과 `ai-sdlc.yaml` 존재 여부를 확인한다.
2. `.ai-sdlc/project-bootstrap.yaml`이 없으면 임의로 가정하지 말고 `ai_sdlc.py init`에 필요한 입력 누락을 먼저 보고한다.
3. 제공된 Project Context / 고객 표준 / 회사 SOP / 요구사항만 Evidence로 사용한다.
4. 개발언어, Framework, DB, 배포환경, Architecture, Directory/Module, API Rule, Transaction Policy, Coding/Naming/Logging/Error/Security/Test/CI-CD/Document/Branch Strategy를 `CONFIRMED / CANDIDATE / OPEN`으로 분리한다.
5. 미확정 기술 선택이나 Business Truth를 임의 확정하지 않는다.
6. Human Decision마다 owner, 필요한 evidence, 영향받는 Action을 기록한다. OPEN이라는 이유만으로 독립적인 분석/설계를 중지하지 않는다.
7. 선택된 Artifact Profile(LITE/STANDARD/ENTERPRISE)을 확인한다. LITE여도 Truth/Revision/Test Safety는 제거하지 않는다.
8. Requirement가 있으면 INTAKE Stage Input Pack을 만들고 `sdlc/config/human-artifacts.yaml`에서 해당 Human Artifact Template을 확인한다.
9. Source가 아직 없으면 Source Provider 부재를 실패로 처리하지 않는다. Source 생성/Write가 필요한 시점에만 Revision/Ownership 계약을 준비한다.
10. Side Effect Action은 자동 요청하지 않는다.
11. 마지막에 `현재 확인된 사실 / OPEN / 다음 Human Decision / 다음 실행 가능한 작업 / 생성될 Human Artifact`를 정리한다.
