# Program Reference

## Purpose
기존 Program 재사용을 우선하고 실제 Artifact/Symbol 근거 없이 PGM/테이블을 발명하지 않는다.

## Required Input
- Stage: `PROGRAM`
- Functional Design + Impact + Source

## Optional Input
- Architecture/Standards/Program Summary

## Retrieval Strategy
1. 기존 PGM/ART relation
2. 유사 Program/Package Convention
3. Source Symbol/Call/Data evidence
4. 관련 Standards

## Steps
1. 기존 Program 재사용 가능성을 판단한다.
2. PGM Change Type/Spec Level을 정한다.
3. Physical Artifact/Symbol Evidence를 연결한다.
4. TASK/AC/TC 후보를 연결한다.

## Output
- PGM list/spec + TASK candidates
- Template: `sdlc/templates/core/program-spec.md`

## Quality Check
- PGM과 실제 Artifact 관계에 Evidence가 있는가
- 신규 Program 판단이 Architecture Convention과 일치하는가

## Alert Conditions
- 신규 Interface/Batch/Table
- High Risk scope expansion
- Program target ambiguity

## Token Strategy
Program Summary와 relevant symbol부터 읽는다.

## Do Not
- 존재하지 않는 Program/Table/API를 사실처럼 만들지 않는다.
- 다른 Logical Program을 무단으로 함께 수정하지 않는다.
