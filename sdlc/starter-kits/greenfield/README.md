# Greenfield Starter Kit

## 목적
Source가 아직 없거나 새 기능 영역을 처음 만드는 프로젝트에서 요구를 빠르게 구조화하되, 설계에 필요한 사실과 아직 결정되지 않은 사항을 분리하기 위한 시작 패키지다.

## 최소 시작 가능 입력
다음 두 가지면 `/setup`과 `/work`를 시작할 수 있다.

1. `project-brief.md` 또는 이에 준하는 프로젝트 목적/문제 설명
2. `requirements/originals/`에 최소 1개의 요구/요청 원문 또는 `starter-manifest.yaml`의 `requirement_sources`

이 단계는 **STARTABLE**일 뿐 구현 준비 완료를 의미하지 않는다.

## 권장 패키지
```text
greenfield-starter/
├─ starter-manifest.yaml
├─ project-brief.md                     # 필수에 가까운 최소 프로젝트 맥락
├─ requirements/
│  └─ originals/                        # 요구서, 회의록, 이메일 정리, XLSX 등 원본
├─ business-context/
│  ├─ stakeholder-map.md                # 권장
│  ├─ process-context.md                # 권장
│  ├─ data-concepts.md                  # 권장
│  └─ glossary.csv                      # 선택
├─ constraints/
│  ├─ architecture-and-stack.md         # 결정된 경우 권장
│  ├─ nfr-security-compliance.md        # 권장
│  └─ integration-inventory.md          # 외부 연계가 있으면 권장
└─ profiles/
   ├─ terminology-profile.json          # 선택
   └─ customer-document-profile.json    # 선택
```

## 입력 수준별 기대 결과
| 입력 수준 | 기대 결과 | 금지되는 과장 |
|---|---|---|
| 프로젝트 목적 + 요구 원문만 있음 | RQ/FR/AC 후보, 확인 질문, 업무 흐름 후보 | 상세 DTO/Table/API를 확정값으로 생성 |
| Actor/프로세스/데이터 의미까지 있음 | Functional Design 구체화 | 미정 Architecture를 사실처럼 표현 |
| 기술 Stack/Architecture/NFR/연계 계약까지 있음 | Program Spec 상세화 가능 | Program DoR OPEN을 숨기고 READY 표시 |
| 실제 Scaffold/Repository까지 생성됨 | Source Evidence를 연결하며 Development 진행 | 생성된 Reference Source를 Business Truth로 승격 |

## Greenfield에서 특히 확인할 항목
- 업무 목표와 성공 기준
- 주요 사용자/Actor와 권한 경계
- 정상 흐름, 예외 흐름, 상태 전이
- 핵심 업무 데이터의 의미와 소유권
- 외부 시스템/이벤트/배치 여부
- 보안/개인정보/감사 요구
- 성능/가용성/운영 제약
- 배포·운영 환경 제약

## 준비도 판정
### STARTABLE
프로젝트 목적과 최소 요구 원문이 존재한다.

### DESIGN_READY
Actor, 핵심 Process, 주요 Data Concept, 핵심 예외/제약이 최소 Candidate 수준으로 정리되어 있고, 확인이 필요한 부분이 명시되어 있다.

### IMPLEMENTATION_READY
실제 또는 승인된 Target Architecture가 있고 Program DoR 17항목의 OPEN이 해소되어야 한다.

## 비고
Greenfield Starter Kit은 상세한 설계서를 선행 입력으로 강제하지 않는다. Harness가 요구를 구체화하면서 만들어야 하는 산출물을 고객에게 다시 선제 작성시키지 않는 것이 원칙이다.
