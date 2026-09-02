# Brownfield 시작 안내

처음 사용하는 경우 `docs/00_시작/START_HERE.md`에서 시작합니다.

Brownfield에서는 기존 Source가 존재한다는 이유만으로 업무정책이나 영향범위를 확정하지 않습니다. 실제 Evidence Coverage를 먼저 확인합니다.

## 최소 시작 자료

- 분석할 요구사항 또는 변경요청 원문
- 실제 Repository/Source 기준점

다음은 있으면 도움이 되는 **선택 Evidence**이며 프로젝트 시작의 필수 입력으로 만들지 않습니다.

- DB Schema/DDL
- API/Interface/Event 명세
- Batch/Scheduler 설정
- 기존 Test/Build/배포 자료
- SOP/운영 매뉴얼/고객 정책 문서

없는 자료는 시작을 막지 않되 Coverage Gap으로 남깁니다.

## 시작 명령

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode BROWNFIELD \
  --delivery STANDARD

python sdlc/scripts/harness.py check --setup
python sdlc/scripts/harness.py intake <requirement-file.xlsx>
```

`intake`가 실제 RQ Target을 반환하면 계획을 확인합니다.

```bash
python sdlc/scripts/harness.py work --target RQ-001 --plan-only
```

## Agent/도구가 먼저 확인할 것

- Source root / Module
- Controller/API/Entry Point
- Service/Use Case
- Repository/Mapper/Data read-write
- Transaction
- External Interface/Event
- Batch/Scheduler/Config/Feature Flag
- Test/Build dependency

분석하지 못한 영역은 `Coverage Gap` 또는 `CHECK_REQUIRED`로 남깁니다. 찾지 못한 것을 `영향 없음`으로 해석하지 않습니다.

## 사람에게 확인할 것

- 업무정책과 To-Be 범위
- 기존 동작을 유지/변경할지에 대한 결정
- 승인/권한/운영 기준
- 실제 기술 선택
- Source만으로 결정할 수 없는 OPEN

## OPEN 해소 기본 경로

```text
Agent가 근거 추가 탐색
→ Source/문서에서 해결 가능한 것은 보강
→ 그래도 결정권한이 필요한 항목만 사람에게 확인
→ 확인 결과로 초안 갱신
```

## 하지 말아야 할 것

- Source Evidence를 자동으로 CONFIRMED_BUSINESS로 승격
- Project Adapter Coverage가 부족한데 COMPLETE라고 표현
- 사용자에게 내부 Profile/Contract를 먼저 작성하도록 요구
- 기존 자료를 다시 수기 입력시켜 Provenance를 잃는 것
