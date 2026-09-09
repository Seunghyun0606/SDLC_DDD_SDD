# 프로젝트 개발가이드 Agent 적용 가이드

이 문서는 프로젝트별 Java/DB/Test/Security/배포 가이드와 Architecture 규칙을 **어디에 두고 Agent가 어떤 순서로 참고해야 하는지** 설명한다.

## 1. 위치를 먼저 구분한다

```text
sdlc/custom/project/standards/
→ 개발자가 따라야 하는 프로젝트 개발 기준

sdlc/custom/project/rules/
→ Agent가 반드시 지켜야 하는 프로젝트 규칙/금지사항

br-input/originals/
→ 고객이 제공한 PDF/DOCX/PPTX/XLSX 원본
```

Core Framework 파일에 고객 개발표준 전체를 직접 넣지 않는다.

## 2. 권장 구조

```text
sdlc/custom/project/
├─ rules/
│  ├─ architecture.mdc
│  ├─ security.mdc
│  └─ tool-usage.mdc
│
├─ standards/
│  ├─ README.md
│  ├─ java-coding-guide.md
│  ├─ jsp-development-guide.md
│  ├─ database-guide.md
│  ├─ sql-guide.md
│  ├─ test-guide.md
│  ├─ deployment-guide.md
│  └─ tools/
│     ├─ static-analysis.md
│     └─ db-mcp.md
│
├─ config/
└─ templates/
```

## 3. Rule과 Standard의 차이

### `rules/`

위반하면 안 되는 프로젝트 제약이다.

예:

```text
- Controller에서 DB에 직접 접근하지 않는다.
- SQL은 지정된 Mapper 계층에 작성한다.
- 운영 DB Write Tool을 사용하지 않는다.
- 인증/권한 공통 모듈을 임의 우회하지 않는다.
```

### `standards/`

구현 방법을 판단할 때 따라야 하는 개발 기준이다.

예:

```text
java-coding-guide.md
→ Naming / Exception / Transaction / Logging

database-guide.md
→ Table/Column / PK/FK / Index 기준

test-guide.md
→ 단위/통합 테스트와 테스트 데이터 기준
```

## 4. `/work`에서 권장하는 읽기 순서

```text
Core 안전 규칙
→ .sdlc/project.yaml
→ sdlc/custom/project/rules/
→ 현재 작업에 관련된 project standards
→ 필요한 경우 domain rules/standards
→ br-input/glossary.csv
→ 현재 RQ 관련 Source / DB / Evidence
→ 설계 / 개발 / 테스트
```

`rules/`는 존재하면 작업 전에 확인한다.

`standards/`는 매 작업마다 모든 파일을 무조건 읽지 않고 현재 변경에 관련된 문서를 선택한다.

예:

```text
Java Service 변경
→ architecture/security rule
→ java-coding-guide.md

SQL 변경
→ DB 관련 rule
→ database-guide.md
→ sql-guide.md

테스트 작성
→ test-guide.md
```

## 5. 중요한 현재 구현 경계

이 읽기 순서는 `sdlc/agent/skills/work/references/project-development-context.md`, Host Adapter, Agent Rule을 통해 **Agent 실행 정책으로 요구**한다.

현재 Core Runtime이 모든 `/work` 실행마다 파일 시스템 Access Log를 검사해 “어떤 standards 파일을 실제로 열었는가”를 독립적으로 증명하는 기능까지 제공하는 것은 아니다.

따라서 현재 보장 수준은 다음처럼 이해한다.

```text
Agent Policy / Skill Contract
→ 관련 Rule/Standard를 읽고 적용하도록 요구

Deterministic Runtime Audit
→ 모든 Guide read event를 강제로 기록·검증하는 기능은 현재 없음
```

즉 “문서가 존재하면 Runtime이 자동으로 전부 읽었다”고 가정하지 않는다. Agent는 작업 결과에서 실제 적용한 프로젝트 기준을 간결하게 설명할 수 있어야 한다.

## 6. 개발가이드 작성 방법

각 Guide는 가능한 한 다음 구조로 짧게 작성한다.

```markdown
# Java 개발 가이드

## 목적
## 적용 대상
## 반드시 지킬 내용
## 권장 내용
## 사용하면 안 되는 방식
## 예시
## 관련 Tool
```

강도는 명확히 구분한다.

```text
반드시 적용
권장
참고
```

## 7. 고객 원본 개발표준이 있는 경우

예:

```text
고객_Java개발표준_v3.pdf
고객_DB표준.docx
```

원본은 그대로 보존한다.

```text
br-input/originals/
```

실제 개발 때 반복 적용할 현재 기준은 필요한 부분을 정리해 다음에 둘 수 있다.

```text
sdlc/custom/project/standards/java-coding-guide.md
sdlc/custom/project/standards/database-guide.md
```

원본과 정리본이 충돌하면 Agent가 임의로 새 정책을 만들지 않는다. 적용 버전이나 권위가 불명확하면 확인 필요로 남긴다.

## 8. Tool 사용 가이드

정적분석 Tool, DB MCP 등 프로젝트 Tool을 사용한다면 두 역할을 나눈다.

```text
sdlc/custom/project/rules/tool-usage.mdc
→ 언제 Tool 사용이 필수인지

sdlc/custom/project/standards/tools/*.md
→ Tool 사용 방법, 결과 해석, 제한사항
```

예:

```text
Rule:
Java 영향 분석 시 프로젝트 정적분석 Tool을 우선 사용한다.

Standard:
Caller/Callee 확인 방법과 결과 해석 방법을 설명한다.
```

Password, Token, DB 비밀번호 같은 Credential은 Repository Guide에 기록하지 않는다.

## 9. Domain 기준과 Project 기준

현재 프로젝트에서만 사용하는 기준:

```text
sdlc/custom/project/standards/
sdlc/custom/project/rules/
```

여러 프로젝트에서 같은 Domain에 재사용할 기준:

```text
sdlc/custom/domain/<domain>/standards/
sdlc/custom/domain/<domain>/rules/
```

현재 고객/프로젝트 업무 용어:

```text
br-input/glossary.csv
```

## 10. 적용 여부 확인 방법

Agent에게 다음처럼 요청할 수 있다.

```text
RQ-001 작업 전에 이번 변경에 적용할 프로젝트 Rule과 개발가이드를 알려줘.
```

작업 후에는 다음을 확인할 수 있다.

```text
이번 Source 변경에 실제 적용한 프로젝트 기준과
어떤 구현에서 반영했는지 알려줘.
```

Agent는 현재 작업에 실제 관련된 문서와 적용 내용을 간결하게 설명해야 한다.

## 11. 관련 Framework Reference

```text
sdlc/agent/skills/work/references/project-development-context.md
```

`AGENTS.md`와 Host Adapter는 이 Reference 및 프로젝트 `rules/`, `standards/` 위치를 작업 Context로 사용한다.

## 12. 관련 문서

- Project 설정: `02_PROJECT_설정가이드.md`
- Input 원본 보관: `11_INPUT_자료_준비가이드.md`
- 역할별 작업: `05_이해관계자별_작업가이드.md`
