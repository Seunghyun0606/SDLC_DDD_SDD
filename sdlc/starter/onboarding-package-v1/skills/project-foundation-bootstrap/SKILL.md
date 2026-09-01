# Project Foundation Bootstrap Skill

## Purpose
실제 프로젝트를 Core Default로 즉시 시작하고, 진행 중 발견되는 프로젝트 차이만 Late-bound Overlay로 기록한다.

## Inputs
- Project identity / mode
- Provider Registry state
- 가능한 경우 기존 README/Architecture/Build/Test/DB/Interface/Standard 위치
- `sdlc/config/p1-foundation.yaml`

## Preconditions
- P0 baseline contract available
- Project mode is known or AUTO
- Source Provider state is explicitly known even when UNCONFIGURED

## Procedure
1. `project-bootstrap-manifest.yaml`을 생성한다.
2. 프로젝트 ID/Mode/Provider state를 기록한다.
3. Brownfield이면 전체 Repository를 먼저 문서화하지 말고 현재 작업에 필요한 자산을 JIT 탐색한다.
4. 발견한 사실은 GIVEN/OBSERVED/INFERRED/CONFIRMED/OPEN으로 구분한다.
5. Core/Profile과 실제 프로젝트 사실이 충돌하지 않으면 Overlay를 만들지 않는다.
6. 충돌이 실제로 확인된 경우에만 `project-overlay.yaml`을 생성한다.
7. Overlay는 처음 `PROPOSED`로 만들고 근거/범위/변경 key/revision을 기록한다.
8. 검토 후 필요한 항목만 `ACTIVE`로 바꾼다.
9. 재사용 가능한 사실은 Knowledge Candidate로 기록하되 Source 관찰만으로 Business Truth를 CONFIRMED하지 않는다.
10. 관련 Entity/Artifact 관계는 Reference Graph에 provenance와 함께 추가한다.
11. 미확정 정보는 OPEN Item으로 남긴다. Side-effect Action이 아니면 다음 분석/설계를 계속한다.
12. 실제 프로젝트 전체 확장 전에 대표 Vertical Slice 1건을 검토한다.

## Decision Rules
- 프로젝트 근거 없는 사전 커스텀: 만들지 않음
- Sample/Pilot만을 위한 커스텀: 만들지 않음
- Project path/provider binding이 실제 필요: Overlay 후보
- Existing standard와 Core default 충돌 관찰: Overlay 후보
- Source behavior에서 업무규칙 추정: Knowledge Candidate + Review
- Source Provider UNCONFIGURED: Source claim 차단, 비Source 분석은 계속 가능

## Outputs
- Project Bootstrap Manifest
- 필요한 경우에만 Project/Domain Overlay
- Knowledge Candidate
- Reference Graph
- OPEN Items

## Quality Checks
```text
python sdlc/scripts/validate_p1_foundation.py config sdlc/config/p1-foundation.yaml
python sdlc/scripts/validate_p1_foundation.py bootstrap <project-bootstrap.yaml>
python sdlc/scripts/validate_p1_foundation.py overlay <overlay.yaml>
python sdlc/scripts/validate_p1_foundation.py graph <reference-graph.yaml>
```

## Stop / Escalation
- 실제 Source write/DB write/Publish/Deploy는 P0 Provider/Permission/Recovery Gate를 따른다.
- Business Boundary/Rule 확정은 L2/Human Review가 필요하다.
- 프로젝트 전체 Scale-out은 실제 Source 기반 대표 Vertical Slice 검토 전에는 보류한다.

## Do Not
- Core Config 전체를 프로젝트 Overlay에 복사하지 않는다.
- 처음부터 모든 프로젝트 차이를 질문하지 않는다.
- Sample 요구사항의 값으로 Core 설정을 바꾸지 않는다.
- OPEN 정보를 임의 CONFIRMED하지 않는다.
