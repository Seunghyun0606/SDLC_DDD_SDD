# 프로젝트 개발가이드 Agent 적용 가이드

## 1. 목적

프로젝트별 Java/DB/Test/Security/배포 가이드와 Architecture 금지사항을 Repository에 넣었는데도 Agent가 작업 중 놓치는 문제를 방지하기 위한 가이드다.

핵심 원칙은 간단하다.

```text
참고하고 따라야 하는 개발 가이드
→ sdlc/custom/project/standards/

반드시 지켜야 하는 강제 규칙/금지사항
→ sdlc/custom/project/rules/
```

고객이 제공한 원본 PDF/DOCX/PPTX 같은 문서는 `br-input/originals/`에 보존한다.

## 2. 권장 폴더 구조

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
│  └─ deployment-guide.md
│
├─ config/
└─ templates/
```

## 3. `rules/`와 `standards/`의 차이

### `rules/`

Agent가 작업하면서 위반하면 안 되는 내용이다.

예:

```text
- Controller에서 DB에 직접 접근하지 않는다.
- SQL은 프로젝트에서 지정한 Mapper 계층에 작성한다.
- 운영 DB에 Write하는 Tool을 사용하지 않는다.
- Java 영향 분석 전 프로젝트 정적분석 Tool을 우선 사용한다.
- 인증/권한 공통 모듈을 임의 우회하지 않는다.
```

즉 **MUST / 금지 / Architecture Constraint** 성격이다.

### `standards/`

현재 작업을 어떻게 구현할지 판단할 때 참고하고 따라야 하는 개발 표준이다.

예:

```text
java-coding-guide.md
- Naming
- Exception 처리
- Transaction 처리
- Logging
- 공통 Utility 사용법

database-guide.md
- Table/Column Naming
- PK/FK 정책
- Index 작성 원칙
- Procedure 작성 기준

test-guide.md
- 단위 테스트 기준
- 통합 테스트 기준
- 테스트 데이터 작성법
```

## 4. Agent가 실제로 읽는 순서

`/work` 수행 시 다음 순서를 적용한다.

```text
Core 안전/권한 규칙
        ↓
.sdlc/project.yaml
        ↓
sdlc/custom/project/rules/
        ↓
현재 작업에 관련된 sdlc/custom/project/standards/
        ↓
필요한 경우 Domain Rule/Standard
        ↓
br-input/glossary.csv
        ↓
현재 RQ와 관련된 Source / DB / Evidence
        ↓
설계 / 개발 / 테스트
```

`rules/`는 프로젝트에 존재하면 먼저 확인한다.

`standards/`는 매번 전부 읽지 않고 현재 작업에 관련된 문서만 읽는다.

예:

```text
Java Service 변경
→ java-coding-guide.md
→ 관련 architecture/security rule

SQL 변경
→ database-guide.md
→ sql-guide.md
→ DB Tool 사용 Rule

테스트 작성
→ test-guide.md
```

이렇게 해서 Context가 불필요하게 커지는 것을 막는다.

## 5. 개발 가이드 문서 작성 방법

각 Guide는 가능한 한 다음 구조로 간결하게 작성한다.

```markdown
# Java 개발 가이드

## 목적
이 프로젝트의 Java 구현 시 따라야 하는 기준을 설명한다.

## 적용 대상
- Service
- DAO
- Batch

## 반드시 지킬 내용
- ...

## 권장 내용
- ...

## 사용하면 안 되는 방식
- ...

## 예시
- ...

## 관련 Tool
- Static Analysis Tool
```

규칙의 강도를 명확히 표현하는 것을 권장한다.

```text
MUST     반드시 적용
SHOULD   특별한 이유가 없으면 적용
REFERENCE 참고
```

단, 사람에게 보여주는 가이드 본문에서는 필요한 경우 `반드시`, `권장`, `참고`처럼 쉬운 한국어를 우선한다.

## 6. 고객에게 받은 기존 개발표준 문서가 있는 경우

예를 들어 고객에게 다음 파일을 받았다고 가정한다.

```text
고객_Java개발표준_v3.pdf
고객_DB표준.docx
```

원본은 변경하지 않고 보존한다.

```text
br-input/originals/
├─ 고객_Java개발표준_v3.pdf
└─ 고객_DB표준.docx
```

Agent가 개발하면서 반복해서 따라야 하는 현재 프로젝트 기준은 필요한 부분을 정리하여:

```text
sdlc/custom/project/standards/java-coding-guide.md
sdlc/custom/project/standards/database-guide.md
```

에 둔다.

원본과 정리본이 충돌하면 Agent가 임의로 새로운 정책을 만들지 않는다. 원본의 적용 버전/권위가 불명확하면 확인 필요로 남긴다.

## 7. Tool 사용 가이드

정적분석 Tool, DB MCP 등 프로젝트에서 제공된 Tool을 사용해야 한다면 역할을 분리한다.

```text
sdlc/custom/project/rules/tool-usage.mdc
→ 언제 Tool 사용이 필수인지

sdlc/custom/project/standards/tools/static-analysis.md
→ Tool 사용 방법과 결과 해석

sdlc/custom/project/standards/tools/db-mcp.md
→ DB MCP 사용 방법과 제한사항
```

예:

```text
Rule:
Java 영향 분석 시 정적분석 Tool을 우선 사용한다.

Standard:
정적분석 Tool에서 Caller/Callee를 확인하는 방법,
결과를 Source 근거로 해석하는 방법을 설명한다.
```

Password, Token, DB 접속 비밀번호는 Guide에 기록하지 않는다.

## 8. Domain 가이드와의 구분

현재 프로젝트에서만 사용하는 기준:

```text
sdlc/custom/project/standards/
sdlc/custom/project/rules/
```

여러 프로젝트에서 같은 Domain에 반복 적용할 재사용 규칙/표준:

```text
sdlc/custom/domain/<domain>/standards/
sdlc/custom/domain/<domain>/rules/
```

프로젝트/고객이 실제로 사용하는 업무 용어:

```text
br-input/glossary.csv
```

## 9. Agent 적용 여부 확인

Agent에게 다음처럼 물어볼 수 있다.

```text
RQ-001 작업 전에 적용해야 하는 프로젝트 개발 가이드와 Rule을 알려줘.
```

Agent는 현재 작업과 관련해 읽은 문서명을 간결하게 알려줘야 한다.

예:

```text
이번 작업에 적용할 프로젝트 기준
- architecture.mdc: Service 계층을 통한 DB 접근
- java-coding-guide.md: 예외/Transaction 기준
- database-guide.md: SQL 및 Column 변경 기준
- tool-usage.mdc: DB 구조 확인 시 DB MCP 사용
```

문서가 존재하는데도 적용 가능한 Guide를 읽지 않은 채 Source를 수정하면 정상적인 `/work` 수행으로 보지 않는다.

## 10. 점검 결과와 현재 Framework 보완

기존 구조에서는 Cursor의 `.cursor/rules/10-project.mdc`가 `sdlc/custom/project/`를 읽도록 안내했지만, 다른 Repository Agent에서는 정확히 `rules/`와 `standards/`를 어떤 순서로 읽을지가 충분히 명확하지 않았다.

현재는 다음 공통 Reference를 추가해 Host와 무관하게 같은 기준을 사용하도록 한다.

```text
sdlc/agent/skills/work/references/project-development-context.md
```

`AGENTS.md`와 Host Adapter는 이 Reference 및 프로젝트 Rule/Standard 위치를 작업 시작 Context로 사용한다.
