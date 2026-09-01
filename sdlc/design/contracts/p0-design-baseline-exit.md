# P0 Design Baseline Exit Contract

상태: `ACTIVE_P0_CANDIDATE`

## 목적

P0의 완료를 Production Ready와 분리해 판정한다. P0 Exit은 SDLC Harness의 구조·계약·안전경계가 P1 구현을 시작할 만큼 고정되었는지를 의미한다.

## P0_BASELINE_READY 조건

1. Baseline/Manifest 역할의 authority가 index로 해석 가능하다.
2. Artifact Profile과 Greenfield/Brownfield/Hybrid 설정 경계가 존재한다.
3. Legacy Requirement Normalization과 RQ Boundary Guard가 존재한다.
4. Candidate → Human/L2 Review → Canonical Publish Gate가 존재한다.
5. Stage Input Pack과 Low-Agent execution contract가 존재한다.
6. Source Discovery / Reverse Sync에서 Source Evidence와 Business Truth가 분리된다.
7. Test Contract / Runtime Verification이 분리된다.
8. E2E Status가 Candidate/Fixture/Runtime blocker를 보존한다.
9. Provider Capability Boundary와 Adapter Conformance가 구현되어 있다.
10. Runtime Invocation은 retry/recovery와 UNKNOWN_AFTER_WRITE를 보존한다.
11. `/work`, `/change`, `/check` Command Runtime이 capability 기반으로 연결된다.
12. Core P0.6~P0.9 구현은 Pilot-specific token에 의존하지 않는다.

## P0 Exit을 막지 않는 외부 항목

다음은 Production/실제 프로젝트 실행에는 필요하지만 P0 설계 기준선 자체를 막지 않는다.

- 특정 고객의 Human Requirement Boundary Decision
- 실제 고객 Source Repository
- 실제 프로젝트 Test Command/Runtime
- 실제 Canonical Registry/ID allocator 구현체
- 실제 인증/credential/secret 연결
- Production Verification

이 항목들은 P1+ 구현 또는 프로젝트 onboarding blocker로 관리한다.

## P0 Exit을 막는 항목

- Core contract/reference가 누락됨
- index가 존재하지 않는 authority를 가리킴
- Candidate를 Human Gate 없이 Canonical로 발행 가능
- Source/Test Evidence가 Business Truth를 자동 확정 가능
- 미실행 Test를 VERIFIED_PASS로 만들 수 있음
- Write retry/recovery에 UNKNOWN 상태가 없음
- Provider unavailable인데 Router가 성공 결과를 발명함
- Pilot-specific domain/stack token이 P0.6~P0.9 Core에 하드코딩됨

## Production Ready

`P0_BASELINE_READY != PRODUCTION_READY`

Production Ready는 실제 Provider, 실제 Source, 실제 Runtime Test, Security/Permission, Release/Operational Validation을 별도 통과해야 한다.
