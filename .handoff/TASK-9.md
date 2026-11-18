# Task 9 Handoff: Case State Machine and Investigation Workflow

## Implemented Endpoints

### POST /api/v1/cases/{id}/decision
**Status:** AS MOUNTED

Records an officer decision on a case with full state machine enforcement and separation-of-duties validation.

**Request Body:**
```json
{
  "decision": "APPROVE | REJECT | ESCALATE | CLOSE_FALSE_POSITIVE | REQUEST_INFO",
  "reason": "string (required for REJECT, ESCALATE, CLOSE_FALSE_POSITIVE)",
  "comments": "string (optional)",
  "expected_version": "integer (required for optimistic locking)"
}
```

**Response 200:**
Returns full `CaseDetailResponse` with updated state and decision recorded.

**Error Responses:**
- `401 Unauthorized` - Missing or invalid JWT token
- `403 Forbidden` - Creator attempting to decide own case (CREATOR_DECIDER_CONFLICT)
- `404 Not Found` - Case does not exist
- `409 Conflict (INVALID_CASE_STATE)` - Invalid state transition for current case state
- `409 Conflict (STALE_OBJECT)` - Optimistic lock version mismatch
- `422 Validation Error` - Missing required fields or invalid decision type

## Decision Types and Required Fields

### APPROVE
- **From States:** PENDING_DECISION, ESCALATED
- **To State:** APPROVED (terminal)
- **Required Fields:** decision, expected_version
- **Optional Fields:** reason, comments
- **Restrictions:** Creator cannot approve own case

### REJECT
- **From States:** PENDING_DECISION, ESCALATED
- **To State:** REJECTED (terminal)
- **Required Fields:** decision, reason, expected_version
- **Optional Fields:** comments
- **Restrictions:** Creator cannot reject own case

### ESCALATE
- **From States:** UNDER_INVESTIGATION, PENDING_DECISION
- **To State:** ESCALATED
- **Required Fields:** decision, reason, expected_version
- **Optional Fields:** comments
- **Restrictions:** None (any authorized officer can escalate)

### CLOSE_FALSE_POSITIVE
- **From State:** UNDER_INVESTIGATION
- **To State:** CLOSED (terminal)
- **Required Fields:** decision, reason, expected_version
- **Optional Fields:** comments
- **Restrictions:** Requires officer role or higher

### REQUEST_INFO
- **From States:** UNDER_INVESTIGATION, PENDING_DECISION
- **To State:** INFORMATION_REQUESTED
- **Required Fields:** decision, expected_version
- **Optional Fields:** reason, comments
- **Restrictions:** None (analysts and officers can request)

## State Transitions

The case state machine enforces the following lifecycle:

```
OPEN
  └─ START_INVESTIGATION → UNDER_INVESTIGATION
       ├─ REQUEST_INFO → INFORMATION_REQUESTED
       │    └─ RECORD_RESPONSE → UNDER_INVESTIGATION (loop back)
       ├─ SUBMIT → PENDING_DECISION
       │    ├─ APPROVE → APPROVED (terminal)
       │    ├─ REJECT → REJECTED (terminal)
       │    ├─ ESCALATE → ESCALATED
       │    │    ├─ APPROVE → APPROVED (terminal)
       │    │    └─ REJECT → REJECTED (terminal)
       │    └─ REQUEST_INFO → INFORMATION_REQUESTED (loop)
       ├─ ESCALATE → ESCALATED
       └─ CLOSE_FALSE_POSITIVE → CLOSED (terminal)
```

**Terminal States:** APPROVED, REJECTED, CLOSED
- No further transitions allowed from terminal states
- Returns HTTP 409 if transition attempted from terminal state

## Permitted Actions Matrix

Permitted actions are computed server-side based on:
- Current case state
- Actor role (AML_ANALYST, AML_OFFICER, AML_MANAGER, ADMINISTRATOR, AUDITOR)
- Whether actor is the case creator (separation of duties)
- Presence of open information requests

### By Role and State

| State | AML_ANALYST | AML_OFFICER (not creator) | AML_OFFICER (creator) | AML_MANAGER | ADMINISTRATOR |
|---|---|---|---|---|---|
| OPEN | START_INVESTIGATION | - | - | - | START_INVESTIGATION |
| UNDER_INVESTIGATION | REQUEST_INFO, SUBMIT | REQUEST_INFO, ESCALATE, CLOSE_FALSE_POSITIVE | REQUEST_INFO, ESCALATE, CLOSE_FALSE_POSITIVE | REQUEST_INFO, ESCALATE, CLOSE_FALSE_POSITIVE | All available |
| INFORMATION_REQUESTED | RECORD_RESPONSE | - | - | RECORD_RESPONSE | RECORD_RESPONSE |
| PENDING_DECISION | - | APPROVE, REJECT, ESCALATE, REQUEST_INFO | ESCALATE, REQUEST_INFO | APPROVE, REJECT, ESCALATE, REQUEST_INFO | All available |
| ESCALATED | - | APPROVE, REJECT | - | APPROVE, REJECT | APPROVE, REJECT |
| APPROVED | (none) | (none) | (none) | (none) | (none) |
| REJECTED | (none) | (none) | (none) | (none) | (none) |
| CLOSED | (none) | (none) | (none) | (none) | (none) |

**Separation of Duties:** Case creator CANNOT approve or reject their own case, regardless of role. This returns HTTP 403.

## Investigation Workflow

### Adding Notes
Case notes can be added via `InvestigationService.add_note()`:
- Append-only (no editing or deletion)
- Includes actor, timestamp
- Generates `CASE_NOTE_ADDED` audit event

### Information Requests
Information requests track required information during investigation:
- Created with `requested_what`, `reason`, `due_date`
- Status lifecycle: OPEN → RESPONDED | CANCELLED | OVERDUE
- One-to-one with information response
- Generates `INFORMATION_REQUESTED` audit event
- Open requests affect case permitted actions computation

### Information Responses
Responses to information requests:
- One-to-one relationship with request
- Updates request status to RESPONDED
- Generates `INFORMATION_RESPONSE_RECORDED` audit event
- Cannot respond to already-responded or cancelled requests

## Audit Events

All case workflow actions generate immutable audit events:

- `CASE_CREATED` - Case creation from alerts
- `CASE_DECISION` - Officer decision recorded (includes previous_state, new_state, decision type, reason)
- `CASE_ASSIGNED` - Case assignment or reassignment
- `CASE_NOTE_ADDED` - Note added to case
- `INFORMATION_REQUESTED` - Information request created
- `INFORMATION_RESPONSE_RECORDED` - Information response submitted

All events include:
- Actor (user_id, username, role)
- Entity (type="case", id=case_id)
- Correlation ID for workflow tracing
- Timestamp
- Detailed evidence in `details_json`

## Seed Data

The seed script includes:

### Case Notes
- Multiple notes per case showing investigation progress
- Notes from different analysts and officers
- Timestamps showing workflow progression

### Information Requests
- Sample requests for documentation, statements, verification
- Mix of OPEN and RESPONDED statuses
- Due dates ranging from past (overdue) to future
- Linked to cases in INFORMATION_REQUESTED state

### Information Responses
- Responses to RESPONDED requests
- Response text showing provided information
- Different response actors

### Decisions
- Sample APPROVE, REJECT, ESCALATE decisions
- Proper reason and comments fields
- Linked to cases in terminal states (APPROVED, REJECTED)

## Error Handling

### Invalid State Transitions (HTTP 409)
When an action is not allowed from the current state:
```json
{
  "detail": "Action APPROVE not allowed from state OPEN"
}
```

### Optimistic Lock Conflict (HTTP 409)
When expected_version doesn't match current version:
```json
{
  "detail": "Case {id} version conflict"
}
```
Response includes different `detail` structure to distinguish from invalid state errors.

### Creator-Decider Conflict (HTTP 403)
When case creator attempts to approve/reject:
```json
{
  "detail": "Case creator cannot make decision on their own case"
}
```
This is a forbidden error, NOT a conflict, because it's an authorization issue.

## Integration Points

### With Audit Service
- All state changes write atomic audit events
- Decision recording includes previous/next state
- Correlation IDs link workflow steps

### With Case Management Service
- `record_decision()` orchestrates full decision workflow
- Validates creator ≠ decider before state transition
- Checks open information requests during permitted action computation
- Updates case state with optimistic locking
- Returns full case detail with updated permitted actions

### With State Machine
- `CaseStateMachine.validate_transition()` enforces allowed transitions
- `CaseStateMachine.permitted_actions()` computes allowed actions
- Centralized transition rules prevent unauthorized state changes

## Frontend Integration Notes

1. **Always use `permitted_actions` from case detail response** - Never compute actions client-side
2. **Check `expected_version` before submitting decision** - Get from latest case detail
3. **Handle 409 conflicts distinctly:**
   - INVALID_CASE_STATE - Inform user state changed, refresh case detail
   - STALE_OBJECT - Inform user case was modified, refresh and retry
4. **Enforce required fields per decision type** - See decision types section above
5. **Display creator-decider separation clearly** - Disable approve/reject for case creator
6. **Show open information requests** - Affects available actions and workflow
7. **Audit trail visible in case detail** - Decisions array shows full history

## Testing Coverage

### Unit Tests (test_investigation_service.py)
- Add note success
- Request information success
- Record response success and failure cases
- Request not found, already responded, invalid status

### Integration Tests (test_investigation_integration.py)
- Case detail exposes all workflow data
- Valid officer decisions update case
- Allowed transitions succeed
- Invalid transitions return 409
- Open information requests affect workflow
- State machine supports documented transitions

### State Machine Tests (test_state_machine.py)
- All valid transitions (11 tests)
- Invalid transitions raise errors
- Terminal state enforcement
- Permitted actions by role
- Creator-decider separation in permitted actions
- Administrator access

All tests verify:
- Optimistic locking works correctly
- Audit events are recorded atomically
- Separation of duties is enforced
- State transitions follow LLD specification
- Error responses have correct HTTP status codes
