# RQC-017 Requirement Candidate — 근태마감

> 상태: `CANDIDATE / NOT PUBLISHED`
> Topic Group: `TG-017`
> Legacy Source: `REQ_TM_TE016~REQ_TM_TE054`
> Raw Items: 39
> Boundary Review: `SPLIT_REVIEW_REQUIRED`

## Purpose

원본 제목 `10분단위 근무계획 개선 근태마감 반영을 구현`을 하나의 RQ로 확정하지 않고 Business Boundary를 확인한다.

## Current Problem

원본 Excel에는 명시적인 현재 문제 서술이 없다.

- truth: `OPEN`
- alert: `CURRENT_PROBLEM_MISSING`

## Desired Outcome Candidate

`10분 단위 근무계획 정보가 관련 근태마감 기능에 반영된다.`

- truth: `INFERRED`
- 근거: 요구사항명 + 39개 세부 요구 문구
- 업무 담당자 확인 없음

## Boundary Card

| Boundary | 값 | Truth |
|---|---|---|
| Business Goal | 10분단위 근무계획의 근태마감 반영 | INFERRED |
| Actor / Trigger | 미확인 | OPEN |
| Observable Outcome | 관련 마감 결과에 근무계획이 반영됨 | INFERRED |
| Policy / State Scope | 일/월/전사/강제/선택적 마감이 섞여 있음 | OBSERVED_FROM_TEXT |
| Acceptance / Release Scope | 독립 배포 필요 여부 미확인 | OPEN |

## Split Candidate Proposal

아래는 RQ 확정안이 아니라 질문을 만들기 위한 텍스트 기반 Cluster다.

| Cluster | 원본 ID | 수량 | 상태 |
|---|---|---:|---|
| 월근태 확인 | REQ_TM_TE016 | 1 | NOT_DECIDED |
| 일근태 입력/마감 | REQ_TM_TE017~024 | 8 | NOT_DECIDED |
| 월마감 | REQ_TM_TE025~032 | 8 | NOT_DECIDED |
| 마감후 수정요청 | REQ_TM_TE033~039 | 7 | NOT_DECIDED |
| 퇴직자 근태마감 | REQ_TM_TE040~044 | 5 | NOT_DECIDED |
| 전사 근태마감 | REQ_TM_TE045~046 | 2 | NOT_DECIDED |
| 일근태 강제마감 | REQ_TM_TE047~048 | 2 | NOT_DECIDED |
| 선택적 근로마감 | REQ_TM_TE049~054 | 6 | NOT_DECIDED |

## Publish

`DENY`

이유: Actor/Trigger, State Scope, Independent Acceptance/Release가 확인되지 않았다.
