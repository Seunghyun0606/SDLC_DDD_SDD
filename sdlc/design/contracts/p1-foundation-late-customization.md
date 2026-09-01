# P1 Foundation / Late Customization Contract

## 목적
P1은 실제 프로젝트를 시작하기 전에 모든 프로젝트 차이를 미리 설정하지 않는다. Core Default로 바로 시작하고, 진행 중 관찰된 프로젝트 사실이 Default/Profile과 충돌할 때만 Overlay를 추가한다.

## 1. Bootstrap
Brownfield 최소 진입정보는 `project_id`, `project_mode`, `source_provider_state`다. README, Build, Test, DB, Interface, Standard 등은 JIT 탐색 대상으로 두며 발견되지 않았다고 프로젝트 전체를 중지하지 않는다.

## 2. Late-bound customization
Overlay 생성은 다음 경우에만 허용한다.
- 관찰된 프로젝트 사실과 Core/Profile이 충돌한다.
- 프로젝트 고유 용어/경로/Provider/표준/Stage 차이가 실제 작업에 필요하다.

다음 이유만으로는 Overlay를 만들지 않는다.
- 나중에 필요할 것 같음
- Pilot/Sample에 값이 있었음
- 프로젝트 근거 없는 선호

Overlay는 변경 대상 key, 기존값, 프로젝트값, scope, reason, evidence/GIVEN source, revision을 기록한다. Core 계약의 전체 사본을 Overlay에 복제하지 않는다.

## 3. Precedence
`LOCAL_OVERRIDE > DOMAIN_OVERLAY > PROJECT_OVERLAY > PROJECT_PROFILE > PRESET > CORE_DEFAULT`

상위 Layer가 적용되더라도 낮은 Layer의 Truth를 삭제하지 않는다. 충돌은 기록하고 검토한다.

## 4. Knowledge bootstrap
프로젝트에서 재사용할 지식은 provenance를 가진 Candidate로 시작한다. Source에서 관찰한 동작은 `OBSERVED`이며 Business Truth를 자동 `CONFIRMED`하지 않는다. Promotion은 Evidence와 Review 후 수행한다.

## 5. Reference graph
RQ/FR/PGM/ART/SYMBOL/DATA/AC/TC/TASK/Knowledge 등 관계는 Graph로 연결할 수 있다. 모든 Edge는 provenance를 가지며, dangling reference를 조용히 삭제하지 않고 OPEN으로 남긴다.

## 6. OPEN item
정보 부족은 분석/설계의 기본 차단 사유가 아니다. Side effect가 있는 Source/DB/Publish/Deploy/Test execution 등 위험 Action만 Guard할 수 있다.

## 7. Baseline cache/index
Index/Cache는 파생물이다. Truth를 복제하지 않고 재생성 가능해야 한다. Source revision이 바뀌면 관련 cache를 STALE 처리한다.

## 8. Real Brownfield scale-out
실제 요구사항 전체 확장 전 대표 Vertical Slice 1건 이상을 실제 Source 기준으로 검토한다. 실제 Source가 없는 상태에서는 Source claim, 실제 Test command가 없는 상태에서는 Runtime PASS를 만들지 않는다.

## 9. Sample isolation
요구사항 샘플이나 Pilot 데이터는 P1 Core Foundation의 필수 입력이 아니다. Sample은 regression/conformance fixture로만 사용할 수 있다.
