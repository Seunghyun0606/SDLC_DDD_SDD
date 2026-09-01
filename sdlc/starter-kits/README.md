# SDLC Starter Kit

Greenfield와 Brownfield는 같은 SDLC Core를 사용하지만 시작점과 필요한 근거가 다르다. Starter Kit은 고객에게 완성된 BR/설계서를 다시 작성시키는 양식이 아니라, 기존 자료를 최대한 그대로 받고 Harness가 어떤 근거를 어디까지 사용할 수 있는지 명확히 하는 최소 입력 계약이다.

## 공통 원칙
1. **최소 시작 가능(STARTABLE)**과 **설계 준비(DESIGN_READY)**, **구현 준비(IMPLEMENTATION_READY)**를 구분한다.
2. 필수 정보가 부족해도 위험한 실행을 제외한 분석 Workflow는 중단하지 않는다. 부족한 정보는 `OPEN / CHECK_REQUIRED / ASSUMPTION`으로 남긴다.
3. 고객 원본문서는 다시 작성시키지 않고 원본과 provenance를 보존한다.
4. Canonical ID와 내부 추적 정보는 Starter Kit의 표시 형식과 무관하게 유지한다.
5. Greenfield에서 Source가 없는 것은 정상이다. Brownfield에서는 실제 Repository 기준점 없이 Source 기반 영향 분석을 `CONFIRMED`로 판정하지 않는다.
6. Starter Kit에 문서가 많이 들어있다고 Business Truth가 되는 것은 아니다. 권위/유효성/충돌 여부를 별도로 판정한다.
7. 비밀번호, 토큰, 개인키, 운영 비밀값 등 Secret은 Starter Kit에 넣지 않는다.

## Mode별 시작점
| Mode | 최소 시작점 | 핵심 추가 근거 | 기본 목적 |
|---|---|---|---|
| GREENFIELD | 프로젝트 목적 + 요구/문제 원문 | 업무 맥락, 제약, NFR, 데이터/연계 후보 | 요구를 설계·구현 가능한 명세로 구체화 |
| BROWNFIELD | 변경/분석 목적 + Repository 기준점 | Source Profile, Build/Test, DB/Interface, 기존 문서 | 실제 Source 기반 영향·재사용·변경 범위 분석 |

## 준비도 정의
### STARTABLE
Workflow를 시작할 수 있다. 미확정이 존재해도 분석은 진행한다.

### DESIGN_READY
기능 설계의 핵심 업무 흐름, 주요 Actor, 데이터 의미, 예외/제약을 작성할 근거가 충분하다. 아직 Program DoR가 열려 있을 수 있다.

### IMPLEMENTATION_READY
`program-spec-readiness.json`의 필수 DoR 항목이 충족되고 실제 Source/Architecture Target이 확정되어 Production Source 구현을 시작할 수 있다.

## 구성
- `greenfield/`: 신규 시스템/신규 영역용 Starter Kit
- `brownfield/`: 기존 시스템 분석/변경용 Starter Kit

Starter Kit은 Project Profile, Source Profile, Terminology Profile, Customer Document Profile, BR Intake와 연결되지만 Core 자체를 고객별로 Fork하지 않는다.
