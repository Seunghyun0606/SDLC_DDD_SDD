# 11. Validation & Handoff Checklist

## A. Onboarding
- [ ] Project 기본정보
- [ ] Business Source 원본
- [ ] Manifest
- [ ] Glossary
- [ ] Artifact Selection
- [ ] Source Profile
- [ ] Repo/Snapshot
- [ ] Build/Test command

## B. Business Analysis
- [ ] Scenario별 6W
- [ ] Who 권한/Profile
- [ ] When Trigger/State
- [ ] Where Menu/Channel
- [ ] What Object/Field
- [ ] How CRUD/Rule/Exception
- [ ] Why Goal/Policy
- [ ] RQ/FR/BR/AC Trace
- [ ] OPEN/INFERRED
- [ ] 고객 확인사항

## C. Customer Artifact
- [ ] AS-IS/TO-BE
- [ ] 6W
- [ ] Process
- [ ] Rule/Exception
- [ ] UI/업무접점
- [ ] Scope/Out
- [ ] AC
- [ ] Decision
- [ ] 변경이력

## D. Existing Source
- [ ] Entry Point
- [ ] Controller/Service
- [ ] Transaction
- [ ] Mapper Interface/XML
- [ ] Table/View/Procedure
- [ ] Code Master
- [ ] Auth
- [ ] Integration
- [ ] Similar Pattern
- [ ] Protected/Generated
- [ ] revision/hash
- [ ] Blind Spot

## E. Skillization
- [ ] 반복 가능한가
- [ ] 특정 RQ Rule을 Skill화하지 않았는가
- [ ] Evidence/Verified Revision
- [ ] Do Not
- [ ] Quality Check

## F. Development Blueprint
- [ ] UI/Field
- [ ] CRUD
- [ ] Logic/Decision
- [ ] State/Error
- [ ] Integration
- [ ] Query/Data
- [ ] Common Code actual
- [ ] Transaction/Auth/Audit
- [ ] Source Mapping
- [ ] Test Mapping

## G. Source Proposal
- [ ] File/Symbol confirmed
- [ ] Change boundary
- [ ] Preserve pattern
- [ ] No unrelated refactor
- [ ] Data write boundary
- [ ] Regression impact
- [ ] Patch Proposal
- [ ] Readiness

## H. 실제 Write Critical Gate
- [ ] actual repo revision
- [ ] Role/Profile mapping
- [ ] Common Code
- [ ] DB PK/UK/Index/Lock
- [ ] Interface contract
- [ ] Build/Test env
- [ ] Test plan
- [ ] Rollback/Recovery
- [ ] 승인 Branch/Workspace

하나라도 Critical하면 `PROPOSAL_ONLY`.
