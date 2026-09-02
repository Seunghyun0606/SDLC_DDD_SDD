# Brownfield 시작 안내

처음 사용하는 경우 먼저 `docs/00_시작/START_HERE.md`를 읽으세요.

이 문서는 **기존 운영 시스템을 변경·고도화하는 프로젝트**에서 무엇을 준비하면 되는지 설명합니다. 일반 사용자가 Impact Contract, Adapter 내부 규칙, Runtime taxonomy를 먼저 학습할 필요는 없습니다.

## 최소 시작 자료

Brownfield에서 가장 중요한 것은 문서의 양이 아니라 **무엇을 바꾸려는지와 실제 Source 기준점이 있는지**입니다.

최소한 다음 두 가지가 필요합니다.

1. 변경 요청 또는 분석 목적
2. 접근 가능한 Repository/Source bundle

예:

```text
변경 요청:
기존 주문 취소 기능에 부분취소를 추가한다.

Source:
현재 운영 Branch/Commit 기준 Repository
```

Repository 기준점이 없으면 실제 Source 영향분석을 완료했다고 표현하면 안 됩니다. **SOP는 프로젝트 시작의 필수 입력이 아니다.** 없으면 Source/기존 자료로 확인 가능한 범위를 먼저 분석하고 업무정책은 `확인 필요`로 남깁니다.

## 있으면 좋은 자료

- 기존 기능/업무 설계서
- SOP/운영 매뉴얼/정책 문서
- DB Schema/ERD/DDL
- Mapper/Query/Procedure 자료
- REST/API/Swagger/외부 인터페이스 자료
- Kafka/Event/Batch/Scheduler 자료
- Build/Test/배포 기준
- Log/APM/장애 이력
- 운영자나 업무담당자가 알고 있는 예외 정책

자료가 없으면 Agent는 그 영역을 `영향 없음`으로 단정하지 않고 Coverage Gap 또는 `확인 필요`로 남깁니다.

## 사용자가 하는 일

```text
변경 요청과 기존 자료 제공
→ setup 결과 확인
→ Agent가 Source/문서 기반 AS-IS와 영향 후보 작성
→ 사람이 업무정책/범위/위험 판단만 확인
→ Agent가 기능설계/프로그램명세 초안 보완
```

사람에게 Source 후보, Mapper/Table 후보, 호출관계를 처음부터 직접 채우게 하지 않습니다. 확인 가능한 기술 사실은 Agent/도구가 먼저 찾아야 합니다.

## Agent가 먼저 해야 하는 일

- 변경 요청을 현재 시스템의 관련 기능 후보와 연결
- 실제 Repository 기준점과 Source Evidence 확인
- Entry Point, Service, Data, Interface, Batch/Event 영향 후보 탐색
- 직접 영향과 간접 영향 구분
- 분석하지 못한 영역을 Coverage Gap으로 기록
- 기존 Source에서 관찰한 AS-IS와 고객 업무정책을 구분
- 기능설계/Program Spec/Test 후보 초안 작성
- 사람이 결정해야 하는 항목만 `확인 필요`로 모음

Source에 코드가 있다는 이유만으로 Business Truth를 자동 확정하지 않습니다.

## 시작 명령

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode BROWNFIELD \
  --delivery STANDARD

python sdlc/scripts/harness.py check --setup
```

기존/신규 영역이 섞였거나 유형이 애매하면 `--mode AUTO` 또는 `HYBRID`를 사용합니다.

## Brownfield 자동 분석의 현재 경계

Core는 일반적인 Repository 기술 신호와 일부 Java/Spring 계열 정적 후보를 확인할 수 있습니다. 그러나 다음처럼 Runtime 또는 프로젝트별 의미가 필요한 관계는 항상 완전 자동이라고 가정하지 않습니다.

- Reflection/Dynamic dispatch
- 실제 운영 Transaction 경계
- Kafka broker topology/schema
- Scheduler/Feature Flag의 운영 동작
- DB Procedure/Trigger의 복잡한 영향
- APM/Log 기반 Runtime 관계
- 프로젝트 고유 Framework/ORM/Integration

지원하지 못한 영역은 Tool/Adapter 필요 또는 Coverage Gap으로 남깁니다.

상세 지원 범위를 사용자에게 한눈에 보여주는 Capability 문서는 WP-14에서 별도로 정리합니다.

## Reverse 관련 표현

현재 자동 기능을 Full Reverse Engineering이라고 부르지 않습니다.

현재 기준으로 실제 구현된 핵심은 Source 변화와 기존 Evidence의 불일치를 찾는 Drift Check 계열입니다. Source에서 업무정책을 자동 확정하거나 기존 기능설계서를 자동 덮어쓰는 기능으로 설명하지 않습니다.

Reverse 용어 정리는 WP-16에서 더 단순화합니다.

## 하지 말아야 할 것

- Source가 발견됐다는 이유만으로 업무정책 확정
- Adapter가 없는 영역을 분석 완료로 표시
- 찾지 못한 관계를 `영향 없음`으로 표현
- 신규 사용자가 내부 Contract/Profile/Adapter 구조를 이해해야 시작할 수 있다고 안내
- 기존 문서를 전부 먼저 역설계한 뒤에만 변경을 시작

## 다음 단계

기존 RQ Target이 있다면:

```bash
python sdlc/scripts/harness.py check --target <RQ-ID>
python sdlc/scripts/harness.py work --target <RQ-ID> --plan-only
```

기존 RQ의 변경요청은:

```bash
python sdlc/scripts/harness.py change \
  --target <RQ-ID> \
  --change "부분취소를 지원하도록 변경"
```

새로운 변경 요청에서 처음 RQ를 생성해야 하는 경우에는 아직 Zero-to-One intake 연결이 없으므로 WP-03이 필요합니다. 내부 Canonical을 신규 사용자가 수동 편집해 우회하지 않습니다.
