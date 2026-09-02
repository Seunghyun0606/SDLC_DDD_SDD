# Greenfield 시작 안내

처음 사용하는 경우 먼저 `docs/00_시작/START_HERE.md`를 읽으세요.

이 문서는 **기존 Source가 없거나 새 시스템/기능 영역을 만드는 프로젝트**에서 어떤 자료를 준비하면 되는지만 설명합니다. 일반 사용자가 Starter Manifest나 내부 Profile을 먼저 작성할 필요는 없습니다.

## 최소 시작 자료

처음부터 상세 설계서가 필요하지 않습니다.

최소한 다음이 있으면 프로젝트 맥락을 잡을 수 있습니다.

1. 프로젝트가 해결하려는 문제 또는 목표
2. 최소 한 건의 요구사항/요청 원문

예:

```text
고객이 주문을 취소하면 결제를 취소하고 재고를 복구한다.
```

SOP, Architecture, 보안 기준이 아직 없으면 없는 상태로 시작하고 `확인 필요`로 남깁니다. **SOP는 프로젝트 시작의 필수 입력이 아니다.**

## 있으면 좋은 자료

- 요구사항 Excel/문서/메일/회의 결과
- SOP/업무매뉴얼/정책 문서
- 주요 사용자/조직/권한 정보
- 프로젝트 개발표준
- Architecture/기술 선택 결정사항
- 화면/UI 표준
- Data/공통코드 기준
- 외부 API/Event/Batch 기준
- Security/NFR/개인정보/운영 제약

자료가 부족하다는 이유로 Agent가 화면·API·Table·업무정책을 확정값으로 발명하면 안 됩니다.

## 사용자가 하는 일

```text
자료 제공
→ setup 결과 확인
→ Agent 초안 검토
→ 업무정책/범위/권한/승인처럼 사람이 결정해야 하는 항목만 확인
```

사람이 빈 Template의 수십 개 항목을 먼저 채우는 방식은 권장하지 않습니다.

## Agent가 먼저 해야 하는 일

- 요구 원문을 훼손하지 않고 정리
- 목표와 기능 요구 후보 작성
- 인수조건 후보 작성
- 정상/예외 흐름 후보 작성
- 제공된 표준에 기반한 기술 설계 후보 작성
- 확인할 수 없는 내용은 `확인 필요`로 분리
- 다음 작업 안내

업무정책을 사람 확인 없이 확정하지 않습니다.

## 시작 명령

```bash
python sdlc/scripts/harness.py setup \
  --name <project-name> \
  --mode GREENFIELD \
  --delivery STANDARD

python sdlc/scripts/harness.py check --setup
```

프로젝트 유형이 애매하면 `--mode AUTO`를 사용합니다.

## 현재 연결 한계

현재 이 Branch에는 `harness.py intake`가 아직 없습니다. 따라서 빈 Greenfield 프로젝트에서 한 줄 요구사항을 RQ ID로 자동 등록하고 바로 `work`로 넘기는 Zero-to-One 흐름은 아직 완성되지 않았습니다.

XLSX 요구사항 후보 추출 Runtime은 있지만 Canonical RQ 등록과 Target 반환까지는 연결되지 않습니다. 신규 사용자가 내부 저장 구조를 수동 편집해 이 문제를 우회하지 않도록 합니다.

이 연결은 Session 3 / WP-03에서 구현해야 합니다.

## 하지 말아야 할 것

- Source가 없다는 이유로 기술 상세를 업무 사실처럼 확정
- 고객에게 모든 기술 세부를 직접 작성하도록 요구
- 내부 Status/Contract/Canonical 용어를 사용자 입력값으로 요구
- 불확실한 내용을 숨긴 채 READY로 표현
- 첫 사용자가 Starter Manifest/Profile을 이해해야 시작할 수 있다고 안내

## 다음 단계

setup 뒤에는 `docs/00_시작/START_HERE.md`의 요구사항 등록 절차로 돌아갑니다.

RQ Target이 이미 있다면:

```bash
python sdlc/scripts/harness.py work --target <RQ-ID> --plan-only
```

첫 RQ가 없다면 WP-03 intake 연결 전까지 내부 Canonical을 직접 수정하지 않습니다.
