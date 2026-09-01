# /setup

관리자용 프로젝트 초기 설정 Skill.

1. Project Mode(`AUTO / BROWNFIELD / GREENFIELD / HYBRID`)를 결정한다.
2. Mode에 맞는 Starter Kit을 선택한다.
   - `GREENFIELD` → `sdlc/starter-kits/greenfield/`
   - `BROWNFIELD` → `sdlc/starter-kits/brownfield/`
   - `HYBRID` → Brownfield Source 기준을 먼저 적용하고 Greenfield 신규 영역 입력을 함께 등록한다.
   - `AUTO` → 실제 Repository/기존 Source 존재 여부를 탐색해 Mode Candidate를 만들고, 확정되지 않으면 `AUTO_DISCOVER`로 진행한다.
3. Mode에 맞는 Preset을 선택한다.
   - `GREENFIELD` → `greenfield-default`
   - `BROWNFIELD` → `brownfield-auto`
   - `HYBRID` → `brownfield-auto`를 기반으로 Project Overlay에서 신규 영역 차이를 추가한다.
4. README/Guide/Build/Test/Source/DB/Interface 자산을 탐색한다.
5. `sdlc/config/project-profile.example.yaml`을 복사해 실제 Profile을 만든다.
6. Brownfield/Hybrid이면 `sdlc/config/source-profile.example.yaml`을 기준으로 Source root/build/test/제외 경로를 설정한다. Greenfield에 Source가 아직 없으면 `OPEN`으로 두어도 된다.
7. `terminology-profile`, `customer-document-profile`, `br-intake-profile`을 고객/프로젝트 특성에 맞춰 설정한다.
8. Brownfield/Hybrid이면 `sdlc/config/impact-adapter-profile.example.yaml`을 검토한다.
   - Core는 `brownfield-impact-contract.json`의 공통 Node/Edge/Coverage/출력 계약만 제공한다.
   - 실제 Java/Spring/.NET/Node, ORM/SQL, Messaging, Stored Procedure, Reflection 등 관계 탐색은 `sdlc/custom/project/adapters/impact/`에 **프로젝트별 별도 구현**한다.
   - Project Impact Adapter가 없으면 일반 Workflow는 계속하지만 영향분석 상태는 `PARTIAL_PROJECT_ADAPTER_REQUIRED`로 유지한다.
9. 고객 기존 문서는 재작성시키지 말고 원본 + `BR Intake Manifest` 구조로 등록한다.
10. Core를 수정하지 않고 `sdlc/custom/project/`, `sdlc/custom/domain/<domain>/`에 차이를 둔다.
11. `python sdlc/scripts/validate_harness_structure.py .`와 `python sdlc/scripts/validate_document_experience.py .`로 구조와 문서 경험 계약을 검증한다.
12. 기존 Source Evidence가 있는 Brownfield/Hybrid 프로젝트에서 기준 Source가 변경되면 `detect_source_drift.py`로 직접 STALE/역방향 검토 Candidate를 먼저 계산한다. 자동 문서/Business Truth 덮어쓰기는 하지 않는다.
13. 위험한 실행 설정만 명시적으로 Guard하고 일반 Workflow는 non-blocking으로 유지한다.

## 준비도 안내
- Starter Kit 최소값 충족은 `STARTABLE`을 의미할 뿐 `IMPLEMENTATION_READY`가 아니다.
- Brownfield는 Repository 기준점이 없으면 Source 기반 영향 분석을 `CONFIRMED`로 판정하지 않는다.
- Project Impact Adapter가 없거나 Coverage Gap이 남으면 Brownfield 영향분석을 완전하다고 표시하지 않는다.
- Production Source 구현은 Program DoR와 실제 Target이 충족되어야 한다.
