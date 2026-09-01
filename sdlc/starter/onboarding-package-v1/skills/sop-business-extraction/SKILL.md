# Skill — SoP / Business Source Extraction

## Purpose
PPT/XLSX/Word/PDF/MD 원본문서에서 원문 Provenance를 유지하면서 6W/RQ/FR/BR/UI/Data/Integration 후보를 추출한다.

## Required Input
- Business Source Manifest
- Original Document
- Glossary
- Project/domain hints

## Steps
1. 문서 구조 식별
2. Locator 생성
3. Actor/Trigger/Location/Object/Action/Purpose 추출
4. CRUD/Rule/Exception/State 추출
5. UI/Data/Code/Integration 추출
6. 6W Candidate
7. RQ/FR/BR/AC Candidate
8. 충돌/결측 질문

## Format Hints
### XLSX
Sheet/Header/Merged Cell/Legacy ID/대상/권한/CRUD/Code/Table/Program

### PPT
Slide/Actor lane/Process/Decision/Screenshot/AS-IS/TO-BE/Note

### Word/PDF
Heading/Page/정책문장/조건/예외/책임주체/변경이력

## Output
각 값:
- value
- truth
- source_id
- locator
- confidence
- question if OPEN

## Do Not
- 없는 Why 창작
- Screenshot만 보고 hidden validation 추정
- 회의록 자동 공식정책 승격
- 최신 문서=최고 Authority 간주
- Source 구현=BR 자동 승격
