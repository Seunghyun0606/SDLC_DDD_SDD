# Cursor Adapter — /rq-list

이 파일은 Cursor용 PM RQ 작업목록 진입 Adapter다. 업무 규칙과 안전 경계는 중복 정의하지 않는다.

## Core Skill

반드시 다음 Core Skill을 Source of Truth로 사용한다.

`@sdlc/agent/skills/rq-list/SKILL.md`

상세 운영 가이드:

`@docs/00_시작/12_RQ_작업목록_운영가이드.md`

## 사용자 입력 예

```text
/rq-list refresh
/rq-list export
/rq-list import docs/00_관리/RQ_작업관리.xlsx
```

자연어 요청도 동일하게 처리한다.

```text
PM용 RQ 관리 엑셀 만들어줘.
RQ 작업목록 최신 상태로 보여줘.
수정한 RQ_작업관리.xlsx를 반영해줘.
RQ-001 담당 개발자를 홍길동으로 지정해줘.
```

## 실행 원칙

- 실제 명령은 `python sdlc/scripts/harness.py rq-list ...` 공식 진입점을 사용한다.
- Excel/CSV PM 정보는 업무 기준 정보(Canonical)를 자동 변경하지 않는다.
- 새 RQ는 PM 파일에서 만들지 않고 Requirement Intake로 생성한다.
- Runtime이 계산한 현재 상태를 PM이 수동 완료 처리하지 않는다.
- 다수 RQ 관리는 Excel/CSV, 단일 RQ 간단 배정은 `assign`을 사용할 수 있다.
- 결과는 사람에게 처리 건수, 갱신 파일, 확인 필요 항목 중심으로 간결하게 설명한다.
