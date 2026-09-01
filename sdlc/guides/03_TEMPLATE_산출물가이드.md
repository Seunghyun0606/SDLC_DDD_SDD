# TEMPLATE / 산출물 가이드

## Quick Start

산출물은 사용자가 빈 문서부터 작성하는 것이 아니라 Agent 초안을 검토·수정하는 것을 기본으로 한다. 같은 업무정보는 여러 문서에 복사하지 않고 기준 문서를 참조한다.

```mermaid
flowchart LR
    I["입력/Canonical"] --> T["Template"] --> A["Agent 초안"] --> H["사람 검토"] --> O["현재 산출물"]
```

## 파일명 규칙

`<대표ID>_<짧은업무명>_<산출물종류>.<확장자>`

예: `RQ-0042_휴가취소근태반영_영향분석.md`

## Template 공통 Section

1. 문서 목적
2. 한눈에 보기
3. 업무 흐름
4. 입력 및 근거
5. 상세 내용
6. 미확정 사항·주의·가정
7. 관련 ID 및 추적성
8. 다음 작업

## 활성 주요 산출물

| 산출물 | 목적 | 중복 방지 원칙 | 대표 파일명 |
|---|---|---|---|
| 요구사항 정의 | 원문/외부ID/목표/범위/FR/BR 후보/AC를 한 곳에서 관리 | 별도 요구분석 문서를 신규 생성하지 않음 | `RQ-xxxx_업무명_요구사항.md` |
| 미확정 사항 해소표 | 실제 결과를 바꾸는 미확정의 확인방법/담당/상태 관리 | Machine taxonomy는 본문에 반복하지 않음 | `RQ-xxxx_업무명_OPEN해소.md` |
| 프로세스 분석 | 6하원칙과 AS-IS/TO-BE 업무 흐름 | 요구사항 정의를 다시 쓰지 않고 관련 ID 참조 | `RQ-xxxx_업무명_프로세스분석.md` |
| 영향 분석 | Business/Functional/Technical 영향과 Source 후보 | Source 관찰을 업무정책으로 복사하지 않음 | `RQ-xxxx_업무명_영향분석.md` |
| 기능 설계 | 목표 시스템의 업무/기능 의미를 정의하는 기준 문서 | 6W/Field/CRUD/Rule의 의미상 Source of Truth | `RQ-xxxx_업무명_기능설계.md` |
| 프로그램 구현 명세 | 실제 PGM/Source/Data Mapping과 구현 Delta | 기능설계 내용을 재작성하지 않음 | `PGM-xxxx_업무명_프로그램구현명세.md` |
| 구현 결과 | 실제 Source 변경 결과 | Program Spec과 Source 차이만 기록 | `RQ-xxxx_업무명_구현결과.md` |
| 테스트 시나리오 | AC 기반 TC와 실행 조건 | AC를 재정의하지 않고 연결 | `RQ-xxxx_업무명_테스트시나리오.md` |
| 검증 결과 | AC/TC/PGM/Source 기준 최종 검증 | 실패/미수행을 숨기지 않음 | `RQ-xxxx_업무명_검증결과.md` |
| 전체 작업 목록 | PM/작업자 공통 Work List | Canonical의 관리 View이며 별도 업무 Truth가 아님 | `전체작업목록.md/.xlsx` |

## Legacy View

`sdlc/templates/core/requirement-analysis.md`는 v1.6부터 신규 Workflow의 활성 산출물이 아니다. 기존 링크 호환을 위한 `DEPRECATED_COMPATIBILITY_VIEW`이며 새 FR/BR/AC를 작성하지 않는다.

## Functional Design과 Program Spec 경계

Functional Design에는 **무엇을 어떻게 동작시켜야 하는가**를 기록한다.

Program Spec에는 **그 기능을 어느 PGM/Source/API/DTO/Query/Table로 구현하는가**와 기능설계 대비 구현 차이만 기록한다.

Program Spec의 17개 구현 준비도는 17개 별도 Section이 아니라 하나의 준비도 표에서 관리한다.

## Mermaid Template 규칙

Template에 Mermaid를 포함할 경우 사람이 입력하는 라벨은 기본적으로 quoted label을 사용한다.

```text
A["일반 노드"]
Q{"확인이 필요한가?"}
```

특히 `/work`, `/setup`, `AS-IS/TO-BE`, `AC/TC`처럼 `/`가 포함된 문자열을 따옴표 없는 `[...]`에 직접 넣지 않는다.
