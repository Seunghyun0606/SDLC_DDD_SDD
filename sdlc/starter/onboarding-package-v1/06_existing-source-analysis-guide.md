# 06. Existing Source Analysis Guide

## 목적
Brownfield Source를 파일 검색이 아니라 **업무 Scenario와 실제 변경 Target을 연결하는 Evidence**로 분석한다.

## 입력
- 6W Business Definition
- RQ/FR/BR/AC
- Source Profile
- current repository revision
- 고객 문서 locator
- 기존 Test/장애/문의

## 순서

### 1. Business Anchor
업무용어/Menu/문구/Code Name/Legacy Program ID에서 검색어를 만든다.

### 2. Entry Point
```text
Menu/URL → JSP → JS/Ajax/Form → Controller → Service
```
URL, Request/Response, 권한 Check, 공통 Handler를 확인한다.

### 3. Service/Transaction
Service method, Transaction, Validation, 계산, 다른 Service, Exception/Logging/Audit 확인.

### 4. MyBatis
```text
Mapper Interface
↔ namespace
↔ statement id
↔ parameter/result
↔ SQL
```
dynamic SQL, include, resultMap, procedure call까지 확인한다.

### 5. Oracle/Data
- Table/View/PK/UK/Join
- Code Master
- Date/Null/default
- Sequence/MERGE
- Procedure/Function/Trigger
- Lock/Index

DDL을 확인할 수 없으면 `NOT_VERIFIED`.

### 6. Downstream/Integration
- 동일 Table Consumer
- Batch/Scheduler
- API/File/MQ
- Report
- Stored Procedure/Trigger

직접 호출 없음만으로 영향 없음 판정 금지.

## 결과
`templates/source-analysis-result.yaml`

## Truth
- Source `% 30` → OBSERVED
- 정책서 `10분` → GIVEN/OBSERVED_DOCUMENT
- “10분 코드가 있을 것” → INFERRED/OPEN
- Code Master + Owner 확인 → CONFIRMED

## 종료 조건
- Entry Point?
- 책임 Program/File/Symbol?
- Data Read/Write?
- Transaction/Auth?
- Integration?
- Preserve Pattern?
- OPEN?
