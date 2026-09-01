# {{task_id}} / {{program_id}} — Development Blueprint

## 1. Business Scenario Reference
- 6W Scenario IDs:
- RQ/FR/BR/AC:
- Change Request:

## 2. Screen / Channel Spec
- UI Change: YES / NO / OPEN
- Menu/Screen ID:
- Screen Name:
- Entry Role/Profile:
- Search Conditions:
- Grid/Form:
- Buttons/Actions:

### Field Spec
| Field | Label | Type | Required | Editable | Visible Condition | Validation | Data/Code Source |
|---|---|---|---|---|---|---|---|

## 3. CRUD Matrix
| Scenario/Action | Service | Mapper/API | Target | C/R/U/D | Condition | Result |
|---|---|---|---|---|---|---|

## 4. Core Business Logic
### Decision Table
| Condition | Case A | Case B | Case C |
|---|---|---|---|
|  |  |  |  |
| Result |  |  |  |

### Processing Sequence
1. 
2. 
3. 

## 5. State / Validation / Error
- State transitions:
- Validation order:
- Error code/message:
- Rollback/compensation:

## 6. Integration Contract
| Direction | System/Program | Interface | Sync/Async | Payload | Auth | Retry/Duplicate | Failure |
|---|---|---|---|---|---|---|---|

If none: `NONE_CONFIRMED` or `NONE_ASSUMED`.

## 7. Query / Data Contract
### Query List
| Query ID | Purpose | Parameters | Tables/Views | Key Join/Filter | Lock/Performance | Result |
|---|---|---|---|---|---|---|

### Data CRUD
| Table | Column/Meaning | CRUD | Key | Null/Default | Rule |
|---|---|---|---|---|---|

## 8. Common Code
| Code Group | Code | Meaning | Usage | Authority/Evidence |
|---|---|---|---|---|

## 9. Transaction / Authorization / Audit
- Transaction owner:
- Isolation/Lock:
- Required Role/Profile:
- Audit/Logging:
- Secret/PII handling:

## 10. Brownfield Source Mapping
| Layer | File | Symbol/Statement | AS-IS | TO-BE | Change |
|---|---|---|---|---|---|

- Similar existing implementation:
- Protected/generated paths:
- Legacy deviations:

## 11. Test Mapping
| AC | Unit | Integration | UI/API | Data Check | Negative/Boundary |
|---|---|---|---|---|---|

## 12. Open / Assumption
| Item | Type | Blocking Scope | Owner | Resolution Evidence |
|---|---|---|---|---|

## 13. Source-ready Checklist
- [ ] 6W Scenario complete enough for affected flow
- [ ] UI/Field change explicit, including NO_CHANGE
- [ ] CRUD explicit
- [ ] Business logic/exception explicit
- [ ] Integration explicit, including NONE
- [ ] Query/Table/Key explicit
- [ ] Common Code verified or OPEN
- [ ] Transaction/Auth/Error explicit
- [ ] Current source mapping verified
- [ ] Test mapping present
