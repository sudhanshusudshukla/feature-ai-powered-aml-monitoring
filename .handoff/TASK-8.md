# Task 8 Handoff: Case API and State Transitions

## Implemented Endpoints

### POST /api/v1/cases/
Creates a new case from one or more alerts.

**Request:**
```json
{
  "title": "Case title (max 255 chars)",
  "alert_ids": [1, 2, 3]
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "case_number": "CASE-000001",
  "title": "Case title",
  "customer_id": 123,
  "state": "OPEN",
  "priority": "HIGH",
  "created_by_user_id": 5,
  "assigned_to_user_id": null,
  "closure_reason": null,
  "created_at": "2026-11-17T12:00:00Z",
  "updated_at": "2026-11-17T12:00:00Z",
  "version": 1,
  "linked_alerts": [
    {
      "id": 1,
      "alert_number": "ALT-000001",
      "transaction_id": 100,
      "risk_score": 75,
      "priority": "HIGH",
      "status": "NEW"
    }
  ],
  "notes": [],
  "decisions": [],
  "information_requests": [],
  "permitted_actions": ["START_INVESTIGATION"]
}
```

**Error Responses:**
- 401: Not authenticated
- 403: Insufficient permissions
- 404: Alert(s) not found
- 409: Alert already linked to another case (detail: "ALERT_ALREADY_LINKED")

---

### GET /api/v1/cases/{id}
Retrieves complete case detail with permitted actions.

**Response (200 OK):**
```json
{
  "id": 1,
  "case_number": "CASE-000001",
  "title": "Suspicious transfer",
  "customer_id": 123,
  "state": "PENDING_DECISION",
  "priority": "HIGH",
  "created_by_user_id": 5,
  "assigned_to_user_id": 7,
  "closure_reason": null,
  "created_at": "2026-11-17T12:00:00Z",
  "updated_at": "2026-11-17T13:00:00Z",
  "version": 3,
  "linked_alerts": [...],
  "notes": [...],
  "decisions": [...],
  "information_requests": [...],
  "permitted_actions": ["REQUEST_INFO", "APPROVE", "REJECT", "ESCALATE"]
}
```

**Error Responses:**
- 401: Not authenticated
- 403: Insufficient permissions
- 404: Case not found

---

### POST /api/v1/cases/{id}/assign
Assigns or reassigns case to a user.

**Request:**
```json
{
  "assigned_to_user_id": 7,
  "expected_version": 1
}
```

**Response (200 OK):**
Returns updated CaseDetailResponse with new assignment and incremented version.

**Error Responses:**
- 401: Not authenticated
- 403: Insufficient permissions
- 404: Case or user not found
- 409: Version conflict (optimistic locking)

---

### POST /api/v1/cases/{id}/decision
Records a case decision with separation-of-duties enforcement.

**Request:**
```json
{
  "decision": "APPROVE",
  "reason": "Reviewed transaction history, no suspicious activity found",
  "comments": "Customer confirmed legitimate business purpose",
  "expected_version": 3
}
```

**Decision Types:**
- APPROVE
- REJECT
- ESCALATE
- CLOSE_FALSE_POSITIVE
- REQUEST_INFO

**Response (200 OK):**
Returns updated CaseDetailResponse with new state, decision record, and incremented version.

**Error Responses:**
- 401: Not authenticated
- 403: Case creator cannot decide own case (detail: "CREATOR_DECIDER_CONFLICT")
- 404: Case not found
- 409: Invalid state transition, version conflict, or validation error

---

## Case States

| State | Description |
|---|---|
| OPEN | Case created, investigation not started |
| UNDER_INVESTIGATION | Investigation in progress |
| INFORMATION_REQUESTED | Additional information requested |
| PENDING_DECISION | Ready for officer decision |
| ESCALATED | Escalated to higher authority |
| APPROVED | Case approved (terminal) |
| REJECTED | Case rejected (terminal) |
| CLOSED | Case closed as false positive (terminal) |

---

## State Transitions

| From State | Action | To State | Allowed Roles |
|---|---|---|---|
| OPEN | START_INVESTIGATION | UNDER_INVESTIGATION | Analyst |
| UNDER_INVESTIGATION | REQUEST_INFO | INFORMATION_REQUESTED | Analyst, Officer, Manager |
| UNDER_INVESTIGATION | SUBMIT | PENDING_DECISION | Analyst |
| UNDER_INVESTIGATION | ESCALATE | ESCALATED | Analyst, Officer, Manager |
| UNDER_INVESTIGATION | CLOSE_FALSE_POSITIVE | CLOSED | Officer, Manager |
| INFORMATION_REQUESTED | RECORD_RESPONSE | UNDER_INVESTIGATION | Analyst, Manager |
| PENDING_DECISION | REQUEST_INFO | INFORMATION_REQUESTED | Officer, Manager |
| PENDING_DECISION | APPROVE | APPROVED | Officer (not creator), Manager |
| PENDING_DECISION | REJECT | REJECTED | Officer (not creator), Manager |
| PENDING_DECISION | ESCALATE | ESCALATED | Officer, Manager |
| ESCALATED | APPROVE | APPROVED | Officer, Manager |
| ESCALATED | REJECT | REJECTED | Officer, Manager |

Terminal states (APPROVED, REJECTED, CLOSED) allow no further transitions.

---

## Permitted Actions Matrix

The `permitted_actions` field in CaseDetailResponse contains actions available to the current user based on:
- Current case state
- User role
- Whether user is case creator (separation of duties)
- Presence of open information requests

### Analyst Role
| State | Permitted Actions |
|---|---|
| OPEN | START_INVESTIGATION |
| UNDER_INVESTIGATION | REQUEST_INFO, SUBMIT |
| INFORMATION_REQUESTED | RECORD_RESPONSE |

### Officer Role (Non-Creator)
| State | Permitted Actions |
|---|---|
| UNDER_INVESTIGATION | REQUEST_INFO, ESCALATE, CLOSE_FALSE_POSITIVE |
| PENDING_DECISION | REQUEST_INFO, APPROVE, REJECT, ESCALATE |
| ESCALATED | APPROVE, REJECT |

### Officer Role (Creator)
Same as non-creator EXCEPT:
- Cannot APPROVE or REJECT own case (separation of duties)

### Manager Role
| State | Permitted Actions |
|---|---|
| UNDER_INVESTIGATION | REQUEST_INFO, ESCALATE, CLOSE_FALSE_POSITIVE |
| INFORMATION_REQUESTED | RECORD_RESPONSE |
| PENDING_DECISION | REQUEST_INFO, APPROVE, REJECT, ESCALATE |
| ESCALATED | APPROVE, REJECT |

---

## Seed Data

### Sample Cases
Two seed cases are created in the database:

**Case 1:**
- Case number: CASE-000001
- Title: "High-value cross-border transfers"
- State: PENDING_DECISION
- Priority: CRITICAL
- Linked to alerts: ALT-000001, ALT-000002
- Creator: analyst@example.com (user_id varies)
- Can be decided by: officer@example.com

**Case 2:**
- Case number: CASE-000002
- Title: "Structured transaction pattern"
- State: UNDER_INVESTIGATION
- Priority: HIGH
- Linked to alert: ALT-000003
- Creator: analyst@example.com (user_id varies)
- Assigned to: analyst@example.com

### Test Credentials

Use these seed credentials for testing (from app/seed.py):

| Username | Password | Role | Purpose |
|---|---|---|---|
| admin@example.com | admin123 | ADMINISTRATOR | Full access |
| analyst@example.com | analyst123 | AML_ANALYST | Create cases, investigate |
| officer@example.com | officer123 | AML_OFFICER | Make decisions (not own cases) |
| manager@example.com | manager123 | AML_MANAGER | Review and decide |

---

## Key Business Rules

1. **One Alert, One Case**: Each alert can be linked to at most one case. Attempting to create a case with an already-linked alert returns HTTP 409.

2. **Case Priority**: When creating case from multiple alerts, case priority is set to the highest alert priority.

3. **Separation of Duties**: Case creator cannot make APPROVE or REJECT decisions on their own case. This is enforced at service layer and returns HTTP 403.

4. **Optimistic Locking**: Assignment and decision operations require expected_version. Concurrent updates return HTTP 409.

5. **Audit Trail**: All case operations (create, assign, decision) write audit events with correlation IDs for traceability.

6. **Permitted Actions**: The permitted_actions array is computed server-side based on state, role, and creator status. Frontend must not hardcode action availability.

---

## Testing Flows

### Create and Decide Case Flow
1. Login as analyst@example.com
2. POST /api/v1/cases/ with alert_ids from seed data
3. GET /api/v1/cases/{id} to verify creation
4. Login as officer@example.com (different user)
5. POST /api/v1/cases/{id}/decision with decision="APPROVE"
6. Verify state changed to APPROVED

### Creator-Decider Rejection Flow
1. Login as officer@example.com
2. POST /api/v1/cases/ to create case (officer is creator)
3. Attempt POST /api/v1/cases/{id}/decision as same officer
4. Expect HTTP 403 with "creator cannot decide" message

### Invalid State Transition Flow
1. Create case in OPEN state
2. Attempt decision (APPROVE) without investigation
3. Expect HTTP 409 with state transition error

---

## Integration Points

- **Alert Service**: Cases link to alerts; validates alert eligibility
- **Customer Service**: Cases are associated with customers via linked alerts
- **Audit Service**: All case operations create audit events
- **Security Service**: Authentication and authorization for all endpoints
- **Investigation Service**: Future tasks will implement information requests

---

## Notes for Frontend Implementation

1. Always check `permitted_actions` before showing action buttons
2. Handle version conflicts gracefully with user-friendly retry prompts
3. Display case state and priority with appropriate badges/colors
4. Show linked alerts, notes, and decisions in collapsible sections
5. Enforce creator-decider separation in UI (disable decision buttons for creator)
6. Use consistent error handling for 401/403/404/409 responses
7. Implement loading states for async operations
8. Refresh case detail after successful operations to get updated version

---

## API Base URL
All endpoints are mounted under `/api/v1/cases` with authentication required.
