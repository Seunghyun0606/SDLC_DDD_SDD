# /setup

관리자용 프로젝트 초기 설정 Skill.

## 기본 원칙
신규 프로젝트 담당자가 Harness 내부 Profile 구조를 모두 이해하지 않아도 시작할 수 있어야 한다. 최초 설정은 **5개 질문 Fast Path**로 끝내고, 실제 필요가 확인된 설정만 Advanced Setup에서 연다.

## Fast Path — 최초 5개 입력

1. **프로젝트 유형**
   - `GREENFIELD / BROWNFIELD / HYBRID / AUTO`
   - 모르면 `AUTO`로 시작한다.
2. **요구사항 또는 변경요청 위치**
   - 파일, 폴더, 이슈, 문서 위치 중 실제 사용 가능한 기준점을 기록한다.
3. **Source/Repository 위치**
   - Greenfield로 Source가 없으면 `없음`으로 둔다.
   - Brownfield는 Repository 또는 Source bundle 기준점이 필요하다.
4. **Build/Test 경로**
   - 알고 있으면 기록한다.
   - 모르면 `AUTO_DISCOVER`로 두고 README/build file/test root를 탐색한다.
5. **고객용 문서 필요 여부**
   - `internal / customer / both`

이 5개가 있으면 `/work`를 시작할 수 있다. 나머지 Profile 미설정은 기본값을 사용하며 프로젝트 시작을 막지 않는다.

## Fast Path 자동 기본값
- Starter Kit과 Preset은 Project Mode에 맞게 자동 선택한다.
- 문서 언어는 `ko-KR`을 기본으로 한다.
- Terminology Profile은 기본 용어를 사용하고 고객 고유 용어가 발견되면 그때 확장한다.
- Customer Document Profile은 표준 Customer View를 사용한다.
- BR Intake는 원본 보존 + 최소 manifest 방식으로 시작한다.
- OPEN Resolution은 SOP를 요구하지 않으며 기본 Authority 예시를 사용한다.
- Brownfield Impact Adapter가 없으면 분석을 중단하지 않고 `PARTIAL_PROJECT_ADAPTER_REQUIRED`로 표시한다.
- Source root/build/test를 모르면 탐색 결과를 Candidate로 제시하고 근거 없이 확정하지 않는다.

## Mode별 시작
- `GREENFIELD` → `sdlc/starter-kits/greenfield/`
- `BROWNFIELD` → `sdlc/starter-kits/brownfield/`
- `HYBRID` → Brownfield Source 기준을 우선하고 신규 영역 요구를 함께 등록한다.
- `AUTO` → 실제 Repository/기존 Source 존재 여부를 탐색해 Mode Candidate를 만들고 확정되지 않으면 `AUTO_DISCOVER`로 진행한다.

## Advanced Setup — 필요한 경우에만 설정

### 1. 용어/문서 표시
다음 상황에서만 설정한다.
- 고객사 고유 업무용어가 중요함
- 고객문서 Section을 바꿔야 함
- 내부/고객 문서의 Required/Optional 구성이 달라야 함

관련 Profile:
- `sdlc/config/terminology-profile.example.json`
- `sdlc/config/customer-document-profile.example.json`

### 2. 업무문서/BR Intake
SOP/PPTX/XLSX/정책/회의자료를 실제 Evidence로 사용할 때 설정한다.
- 원본은 재작성하지 않는다.
- `BR Intake Manifest`로 등록한다.
- 포맷 Parser와 semantic extraction은 별개다.

관련 Profile:
- `sdlc/config/br-intake-profile.example.json`

### 3. 결정 권한
기본 Authority 역할이 실제 프로젝트 조직과 다를 때만 조정한다.

관련 Profile:
- `sdlc/config/open-resolution-profile.example.yaml`

사용자 문서에는 `Decision Domain`, `Basis Class`, 내부 Status code를 직접 입력시키지 않는다. 실제 권한 판단에 필요한 Machine metadata로 관리한다.

### 4. Brownfield Impact Adapter
Brownfield/Hybrid에서 Framework 수준 영향분석이 필요할 때 검토한다.

Core가 제공하는 것:
- `brownfield-impact-contract.json`의 공통 Node/Edge/Coverage/Output 계약

Project에서 구현해야 하는 것:
- Java/Spring/.NET/Node Call/Symbol 관계
- JPA/MyBatis/JDBC/ORM/SQL/Table lineage
- Stored Procedure/Trigger/ETL
- Kafka/JMS/Event/외부 API
- Reflection/Dynamic dispatch/Runtime wiring
- 프로젝트 고유 Config/Feature Flag/Scheduler

구현 위치:
- `sdlc/custom/project/adapters/impact/`

관련 Profile:
- `sdlc/config/impact-adapter-profile.example.yaml`

**Profile을 채우는 것만으로 Adapter 기능이 구현되는 것은 아니다.**

### 5. Project/Domain Overlay
Core를 수정하지 않고 실제 프로젝트 차이만 둘 때 사용한다.
- `sdlc/custom/project/`
- `sdlc/custom/domain/<domain>/`

기본적으로 Core → Project → Domain의 3계층만 이해하면 된다. Preset/local override 등 내부 resolution order는 `/setup`이 처리하며 일반 사용자가 직접 관리하지 않는다.

## OPEN 처리
초기 요구사항/Source 분석 후 미확정 사항은 `sdlc/templates/core/open-resolution-workbook.md`에 기록한다.

사람이 기본적으로 관리하는 값은 다음뿐이다.
- 무엇을 확인/결정해야 하는가
- 어떻게 확인할 것인가
- 현재 확인된 내용 또는 제안
- 누가 확인/결정하는가
- 진행 상태: `미확정 / 확인중 / 제안 / 확정 / 보류`

Category/Decision Domain/Resolution Method/Basis Class/내부 status/downstream impact는 가능한 경우 Agent/Script가 내부 metadata로 만든다.

## Validation
최소 검증:
- `python sdlc/scripts/validate_harness_structure.py .`
- `python sdlc/scripts/validate_document_experience.py .`

Brownfield에서 기존 Source Evidence freshness를 확인할 때:
- `detect_source_drift.py`

이 기능은 Source Drift와 Reverse Review Candidate를 계산하며, 전체 Reverse Engineering 또는 문서 자동 갱신 기능으로 간주하지 않는다.

## 준비도 안내
- Starter Kit 최소값 충족은 `STARTABLE`이며 `IMPLEMENTATION_READY`가 아니다.
- OPEN이 존재하는 것 자체는 실패가 아니다.
- Business Truth가 필요한 항목은 권한자의 확인 없이 확정하지 않는다.
- Brownfield에서 Repository 기준점이나 Project Impact Adapter가 부족하면 영향분석을 COMPLETE로 표시하지 않는다.
- Production Source 구현은 실제 Target과 Execution Guard가 충족되어야 한다.
