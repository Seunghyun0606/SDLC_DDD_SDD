# Greenfield Starter Kit

## 목적
Source가 아직 없거나 새 기능 영역을 처음 만드는 프로젝트에서 요구를 빠르게 구조화하되, 설계에 필요한 사실과 아직 결정되지 않은 사항을 분리하기 위한 시작 패키지다.

## 최소 시작 가능 입력
다음 두 가지면 `/setup`과 `/work`를 시작할 수 있다.

1. `project-brief.md` 또는 이에 준하는 프로젝트 목적/문제 설명
2. `requirements/originals/`에 최소 1개의 요구/요청 원문 또는 `starter-manifest.yaml`의 `requirement_sources`

이 단계는 **STARTABLE**일 뿐 구현 준비 완료를 의미하지 않는다.

SOP/업무매뉴얼은 있으면 좋은 Evidence지만 **필수 입력이 아니다**. 부족한 정보는 `OPEN Resolution Workbook`을 통해 인터뷰, Workshop, Project Standard, 설계자/개발자 제안으로 구체화한다.

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
│  ├─ ui-ux-and-menu-standard.md        # 화면 프로젝트이면 권장
│  ├─ data-query-convention.md          # DB/조회 설계 기준이 있으면 권장
│  ├─ common-code-dictionary.md         # 공통코드 체계가 있으면 권장
│  ├─ nfr-security-compliance.md        # 권장
│  └─ integration-inventory.md          # 외부 연계가 있으면 권장
└─ profiles/
   ├─ terminology-profile.json          # 선택
   ├─ customer-document-profile.json    # 선택
   └─ open-resolution-profile.yaml      # 결정권한 Customizing 시 권장
```

## OPEN 해소 기본 경로
Greenfield에서는 Source가 없다는 이유로 상세설계를 멈추지 않는다.

1. 업무 목적/정책/Why/권한은 Customer/Business Owner 인터뷰 또는 Workshop으로 확인한다.
2. 화면/동선/Field는 Designer가 후보안을 만들 수 있다.
3. API/Transaction/Query/Error/Integration/NFR는 Developer/Architect가 Project Standard 기반 후보안을 만들 수 있다.
4. 후보안에는 선택 이유와 대안을 기록한다.
5. Business 영역은 권한자 확인 후 `CONFIRMED_BUSINESS`, 기술 영역은 Project Authority가 채택하면 `ACCEPTED_DESIGN`으로 해소한다.
6. 고객에게 모든 기술 세부를 묻지 않는다.

## 입력 수준별 기대 결과
| 입력 수준 | 기대 결과 | 금지되는 과장 |
|---|---|---|
| 프로젝트 목적 + 요구 원문만 있음 | RQ/FR/AC 후보, 6W 업무 시나리오 후보, OPEN Resolution Workbook | 상세 DTO/Table/API/화면을 확정값으로 생성 |
| 인터뷰/설계자 제안으로 Actor/프로세스/화면 후보가 있음 | Functional Design 구체화 | 제안안을 고객 확정 업무정책처럼 표현 |
| UI/Data/Common Code/Integration/기술 기준까지 있음 | 화면/필드/CRUD/Query/Code 포함 Program Spec 상세화 | 상세 명세 OPEN을 숨기고 READY 표시 |
| 실제 Scaffold/Repository까지 생성됨 | Source Evidence를 연결하며 Development 진행 | 생성된 Reference Source를 Business Truth로 승격 |

## Greenfield에서 특히 확인할 항목
- 6하원칙 기준 업무 시나리오: 누가/언제/어디서/무엇을/어떻게/왜
- 업무 목표와 성공 기준
- 주요 사용자/Actor와 권한 경계
- 정상 흐름, 예외 흐름, 상태 전이
- 화면/메뉴/Field와 사용자 동선(해당 시)
- CRUD와 핵심 업무 판단/계산 규칙
- 핵심 업무 데이터의 의미와 소유권
- Query/Data Model/공통코드 기준
- 외부 시스템/이벤트/배치 여부
- 보안/개인정보/감사 요구
- 성능/가용성/운영 제약
- 배포·운영 환경 제약

## 준비도 판정
### STARTABLE
프로젝트 목적과 최소 요구 원문이 존재한다.

### DESIGN_READY
6W Scenario와 주요 Design OPEN이 `CONFIRMED_BUSINESS`, `ACCEPTED_DESIGN`, 합리적 `PROPOSED` 중 하나로 구조화되어 있고, 남은 확인사항과 결정권자가 명시되어 있다.

### IMPLEMENTATION_READY
실제 또는 승인된 Target Architecture가 있고 `developer-spec-contract.json`의 적용 가능한 상세 항목과 Program DoR 17항목의 OPEN이 해소되어야 한다.

## 비고
Greenfield Starter Kit은 상세한 설계서를 선행 입력으로 강제하지 않는다. Harness가 정형화된 Template과 질문/분석/제안 경로를 제공하고 설계자·개발자가 이를 채워가며 산출물을 완성하는 것이 원칙이다.
