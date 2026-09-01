# /setup

관리자용 프로젝트 초기 설정 Skill.

1. Project Mode(AUTO/BROWNFIELD/GREENFIELD/HYBRID)를 결정한다.
2. README/Guide/Build/Test/Source/DB/Interface 자산을 탐색한다.
3. `sdlc/config/project-profile.example.yaml`을 복사해 실제 Profile을 만든다.
4. `sdlc/config/source-profile.example.yaml`을 기준으로 Source root/build/test/제외 경로를 설정한다.
5. `terminology-profile`, `customer-document-profile`, `br-intake-profile`을 고객/프로젝트 특성에 맞춰 설정한다.
6. 고객 기존 문서는 재작성시키지 말고 원본 + `BR Intake Manifest` 구조로 등록한다.
7. Core를 수정하지 않고 `sdlc/custom/project/`, `sdlc/custom/domain/<domain>/`에 차이를 둔다.
8. `python sdlc/scripts/validate_harness_structure.py .`와 `python sdlc/scripts/validate_document_experience.py .`로 구조와 문서 경험 계약을 검증한다.
9. 위험한 실행 설정만 명시적으로 Guard하고 일반 Workflow는 non-blocking으로 유지한다.
