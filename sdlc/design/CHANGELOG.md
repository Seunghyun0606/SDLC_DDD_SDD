# Design Changelog

## v1.5 — 2026-09-01

### ENHANCED

- Brownfield JIT Harness를 Brownfield / Greenfield / Hybrid 공통 Contract로 확장
- Approval-free / Alert-driven 원칙을 `Process Never Blocked`로 명확화
- 기존 Hard Block을 Workflow Block이 아닌 `Execution Guard`로 의미 축소
- PM 관리 구조를 RQ→FR→PGM→TASK→AC/TC Drill-down으로 강화
- PM 담당자/일정/공수를 Optional로 명시
- Excel Generated Artifact를 `전체작업목록.md/.xlsx` 양방향 Canonical View Contract로 강화
- Config/Template/Standard Customizing을 Preset→Project Profile→Domain Overlay→Local Override로 강화
- 사용자 가이드를 Quick Start + 주요 단락별 Mermaid workflow로 강화

### SUPERSEDED

- `requirement.md`, `impact-analysis.md`, `PGM-xxxx.md` 같은 일반 산출물 파일명
- 새 규칙: `<대표ID>_<짧은업무명>_<산출물종류>`

### UNCHANGED

- Canonical Model
- Human Truth / System Evidence / Agent Inference
- Brownfield JIT Documentation 핵심 원리
- `/work /change /check`
- Static Analysis First
- Context Pack / Token Economy
- Knowledge Promotion / Conflict / Freshness
- Git File Merge + Semantic Canonical Merge
- Hook Telemetry / Verified Task Metrics
- Capability / Decision / Contract / Continuity Governance

### PoC Follow-up

- 실제 `전체작업목록.md ↔ 전체작업목록.xlsx` converter 구현
- stable ID + revision 기반 import/export 및 `SYNC_CONFLICT` 계약 테스트
- Brownfield Existing Asset Bootstrap 탐색기
- Greenfield Preset materialization
