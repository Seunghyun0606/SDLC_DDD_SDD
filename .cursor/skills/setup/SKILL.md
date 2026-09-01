# /setup

관리자용 Project Bootstrap Skill.

1. Project Mode(AUTO/BROWNFIELD/GREENFIELD/HYBRID)를 결정한다.
2. README/Guide/Build/Test/Source/DB/Interface 자산을 탐색한다.
3. `sdlc/config/project-profile.example.yaml`을 복사해 실제 Profile을 만든다.
4. `sdlc/config/source-profile.example.yaml`을 기준으로 Source root/build/test/제외 경로를 설정한다.
5. Core를 수정하지 않고 `sdlc/custom/project/`, `sdlc/custom/domain/<domain>/`에 차이를 둔다.
6. `python sdlc/scripts/validate_harness_structure.py .`로 Rule→Skill→Template/Overlay 계약을 검증한다.
7. 위험한 실행 설정만 명시적으로 Guard하고 일반 Workflow는 non-blocking으로 유지한다.
