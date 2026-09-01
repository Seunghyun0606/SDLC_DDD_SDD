# Provider Extension Model — P0.6

Provider Type은 닫힌 enum이 아니다. Core가 기본으로 사용하는 `SOURCE`, `TEST`, `CANONICAL_REGISTRY`, `COMMAND_ROUTER` 외에도 대문자 식별자 규칙을 만족하면 새로운 Provider Type을 추가할 수 있다.

예:
- `DEPLOYMENT`
- `MONITORING`
- `NOTIFICATION`
- `ISSUE_PM`
- `BUSINESS_DOCUMENT`

Router는 Provider Type에 대한 switch/case가 아니라 Capability exact match로 Provider를 선택한다.

따라서 새 Provider를 추가할 때 기본 절차는 다음이다.

1. Provider Registry entry 추가
2. `provider_type` 지정
3. Capability 광고
4. Adapter 구현
5. Provider Request/Response Envelope 준수
6. Conformance Test 추가

Core Router/Envelope Schema 변경은 새 Capability가 기존 Envelope로 표현 불가능한 경우에만 검토한다.

구현체 고유 필드는 `extensions`를 사용한다.
