# Provider State Model — P0.6

Provider Registry 선언과 실제 Runtime 연결상태를 분리한다.

## States

- `AVAILABLE`: 현재 요청에 사용 가능
- `DEGRADED`: 제한사항/경고를 포함해 사용 가능
- `UNAVAILABLE`: 설정은 있으나 현재 접근 불가
- `UNCONFIGURED`: 계약/slot만 있고 실제 Adapter/Connection이 아직 없음
- `DISABLED`: 프로젝트 설정으로 사용하지 않음

## Selection Rule

Command Router는 `enabled: true`이면서 `provider_state`가 `AVAILABLE` 또는 `DEGRADED`인 Provider만 선택한다.

Capability가 Registry에 선언되어 있으나 해당 Provider가 `UNCONFIGURED/UNAVAILABLE/DISABLED`이면 성공으로 간주하지 않는다.

- Capability 자체가 없음 → `MISSING_CAPABILITY`
- Capability는 있으나 사용 가능한 Provider 없음 → `PROVIDER_UNAVAILABLE`
- 동일 우선순위의 사용 가능한 Provider가 둘 이상 → `AMBIGUOUS_PROVIDER`

## Example Registry Rule

Starter의 `provider-registry.example.yaml`은 실제 연결정보를 포함하지 않는 예제다. 따라서 Source/Test Provider 기본상태는 `UNCONFIGURED`이며, Local Command Router만 `AVAILABLE`이다.

이 원칙은 Example/Template가 실제 실행환경처럼 오인되는 것을 방지한다.
