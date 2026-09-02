# Greenfield 시작 안내

처음 사용하는 경우 `docs/00_시작/START_HERE.md`에서 시작합니다.

## 최소 시작 자료

1. 프로젝트가 해결하려는 문제 또는 목표
2. 최소 한 건의 요구사항/요청 원문

Source, SOP, Architecture가 아직 없어도 시작할 수 있습니다. 없는 정보를 만들지 않고 OPEN으로 남깁니다.

## 시작 명령

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode GREENFIELD \
  --delivery STANDARD

python sdlc/scripts/harness.py check --setup
python sdlc/scripts/harness.py intake <requirement-file.xlsx>
```

`intake`가 실제 RQ Target을 반환하면 다음 단계로 진행합니다.

```bash
python sdlc/scripts/harness.py work --target RQ-001 --plan-only
```

## Agent가 먼저 해야 하는 일

- 요구 원문과 외부 ID/Source 위치 보존
- RQ/FR/AC 후보 작성
- 확인 가능한 기술 조건 탐색
- 모르는 사실은 OPEN 유지
- 다음 작업 안내

## 사람이 확인하는 일

- 업무정책·범위·승인·권한
- 유사 요구사항 병합 여부
- 기술 선택
- 남은 OPEN

사람이 Starter Manifest나 빈 Template을 먼저 채우는 방식은 기본 절차가 아닙니다.

## 하지 말아야 할 것

- Source가 없다는 이유로 화면/API/Table/업무정책을 확정값으로 발명
- 요구사항 원본을 요약본으로 대체해 Provenance를 잃는 것
- 내부 Contract/Canonical taxonomy를 사용자 입력값으로 요구
- 불확실한 상태를 READY로 표현
