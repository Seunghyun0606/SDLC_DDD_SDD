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
8. 고객 기존 문서는 재작성시키지 말고 원본 + `BR Intake Manifest` 구조로 등록한다.
9. Core를 수정하지 않고 `sdlc/custom/project/`, `sdlc/custom/domain/<domain>/`에 차이를 둔다.
10. `python sdlc/scripts/validate_harness_structure.py .`와 `python sdlc/scripts/validate_document_experience.py .`로 구조와 문서 경험 계약을 검증한다.
11. 위험한 실행 설정만 명시적으로 Guard하고 일반 Workflow는 non-blocking으로 유지한다.

## 준비도 안내
- Starter Kit 최소값 충족은 `STARTABLE`을 의미할 뿐 `IMPLEMENTATION_READY`가 아니다.
- Brownfield는 Repository 기준점이 없으면 Source 기반 영향 분석을 `CONFIRMED`로 판정하지 않는다.
- Production Source 구현은 Program DoR와 실제 Target이 충족되어야 한다.
