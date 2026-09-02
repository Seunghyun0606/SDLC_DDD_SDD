# SDLC_DDD_SDD

AI-SDLC Harness 설계·Runtime·검증 저장소입니다.

## 처음 사용하는 프로젝트 참여자

Framework 설계 문서나 내부 Contract부터 읽지 않습니다. 다음 문서에서 시작합니다.

- `docs/00_시작/START_HERE.md`

최초 흐름은 다음입니다.

```bash
python sdlc/scripts/harness.py setup --name <project-name> --mode AUTO --delivery STANDARD
python sdlc/scripts/harness.py check --setup
python sdlc/scripts/harness.py intake <requirement-file.xlsx>
```

`intake`는 실제 `RQ-001` 같은 Target과 다음 `work` 명령을 반환합니다.

일반 사용자가 기억할 실행 명령은 다섯 가지입니다.

```text
setup   프로젝트 설정과 Runtime 기준을 준비한다
intake  요구사항 원본을 근거 보존형 RQ/FR Candidate로 등록한다
work    실제 Target의 다음 단계를 진행한다
change  기존 Target의 변경 내용을 등록한다
check   현재 상태와 다음 행동을 확인한다
```

사람이 여러 Profile/Contract/Template을 먼저 작성하는 방식은 기본 사용 흐름이 아닙니다.

## 프로젝트 참여자가 주로 볼 위치

- 시작 방법: `docs/00_시작/START_HERE.md`
- 프로젝트 설정: `docs/00_시작/프로젝트_설정_가이드.md`
- 요구사항 인입 예시: `sdlc/guides/요구사항_인입_완성예시.md`
- 프로젝트 산출물: `docs/**`

Harness 내부 구현·Contract·Validation은 `sdlc/**`, `.cursor/**`, `tests/**`에 있습니다. 테스트 성공은 실제 외부 Agent 품질이나 일반 사용자 사용성의 실증을 대신하지 않습니다.
