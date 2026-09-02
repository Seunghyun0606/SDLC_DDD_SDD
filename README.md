# SDLC_DDD_SDD

AI-SDLC Harness 설계·Runtime·검증 저장소입니다.

## 처음 사용하는 프로젝트 참여자

**Framework 설계 문서나 내부 Contract부터 읽지 마세요.**

다음 한 문서에서 시작합니다.

- `docs/00_시작/START_HERE.md`

최초 실행은 다음 두 명령입니다.

```bash
python sdlc/scripts/harness.py setup --name <project-name> --mode AUTO --delivery STANDARD
python sdlc/scripts/harness.py check --setup
```

일반 사용자가 기억할 실행 명령은 현재 네 가지입니다.

```text
setup   프로젝트 시작 상태를 준비한다
work    현재 요구사항/작업의 다음 단계를 진행한다
change  기존 요구사항의 변경 내용을 등록한다
check   현재 상태와 다음 행동을 확인한다
```

> 중요: 현재 Branch에는 빈 프로젝트의 요구사항 원문을 RQ ID로 등록해 곧바로 `work`까지 연결하는 통합 `intake` 명령이 아직 없습니다. 이 Zero-to-One 연결은 WP-03 범위이며, START_HERE에 현재 가능한 경로와 중단 지점을 명시했습니다.

## 프로젝트 참여자가 주로 볼 위치

- 시작 방법: `docs/00_시작/START_HERE.md`
- setup 상세: `docs/00_시작/프로젝트_설정_가이드.md`
- 프로젝트 산출물: `docs/**`

Harness 내부 Config/Contract/Reference/Validation 구조는 일반 프로젝트 참여자의 선행 학습 대상이 아닙니다.

## Harness 개발·관리자

Harness 자체 구현, Contract, Validation, Pilot 자료는 `sdlc/**`, `.cursor/**`, `tests/**`에 있습니다. 이 영역은 Framework 개발·검증을 위한 것이며 일반 사용자 Onboarding과 분리해서 다룹니다.

이 Repository의 테스트가 통과하더라도 실제 외부 Agent 품질과 일반 사용자 사용성이 자동으로 증명되는 것은 아닙니다.
