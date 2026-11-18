# Task 6 Handoff: Audit Service Implementation

## Overview
Implemented complete audit service for immutable event recording and retrieval, integrated with transaction ingestion and alert generation workflows. The audit service provides end-to-end traceability from transaction receipt through rule evaluation and alert generation.

## API Endpoints

### GET /api/v1/audit
Retrieve audit events with optional filters and pagination.

**Query Parameters:**
- `entity_type` (optional): Filter by entity type (transaction, alert, case, etc.)
- `entity_id` (optional): Filter by specific entity ID
- `actor_id` (optional): Filter by actor user ID
- `correlation_id` (optional): Filter by correlation ID for tracing related events
- `page` (optional, default=1): Page number (1-indexed)
- `page_size` (optional, default=50, max=100): Items per page

**Response:**
```json
{
  "items": [
    {
      "id": 1,
      "timestamp": "2026-11-17T10:30:00Z",
      "actor_user_id": null,
      "actor_username": "system",
      "actor_role": "system",
      "action": "TRANSACTION_INGESTED",
      "entity_type": "transaction",
      "entity_id": 123,
      "correlation_id": "abc-123-def",
      "details_json": "{...}"
    }
  ],
  "page": 1,
  "page_size": 50,
  "total": 100
}
```

**Authentication:** Required (JWT Bearer token)

## Audit Event Action Types

### Transaction Workflow Events
- **TRANSACTION_INGESTED**: Recorded when a transaction is successfully persisted
  - Entity type: `transaction`
  - Details: transaction_reference, account_id, amount, currency, transaction_type, origin_country, destination_country

- **RULE_EVALUATED**: Recorded for each rule evaluation (8 per transaction)
  - Entity type: `transaction`
  - Details: rule_code, rule_name, rule_version, outcome, severity, score, explanation

- **ALERT_GENERATED**: Recorded when an alert is created due to rule matches
  - Entity type: `alert`
  - Details: alert_number, transaction_id, risk_score, priority, matched_rules_count

### Future Case Workflow Events (Supported Structure)
The audit service schema and API support the following case management events that will be implemented in later tasks:

- **CASE_CREATED**: When a new AML case is opened
  - Entity type: `case`
  - Details: case_number, title, priority, customer_id, created_by_user_id

- **CASE_DECISION**: When an officer makes a case decision
  - Entity type: `case`
  - Details: decision, reason, comments, decided_by_user_id, decided_at

- **INFORMATION_REQUESTED**: When additional information is requested
  - Entity type: `information_request`
  - Details: case_id, requested_what, reason, due_date, requested_by_user_id

- **INFORMATION_RESPONSE_RECORDED**: When requested information is provided
  - Entity type: `information_response`
  - Details: information_request_id, response_text, responded_by_user_id, responded_at

## Correlation ID Usage

All audit events within a single transaction workflow share the same correlation ID:
1. Transaction ingestion receives or generates a correlation_id
2. This ID propagates to all rule evaluations (8 events)
3. Alert generation uses the same correlation_id
4. Future case workflow events will use the same correlation_id

This enables complete workflow reconstruction by querying: `GET /api/v1/audit?correlation_id=<id>`

## Integration Points

### TransactionService Integration
The transaction service now writes audit events atomically within the same database transaction:

```python
# Transaction ingestion flow:
1. Persist transaction
2. Write TRANSACTION_INGESTED audit event
3. Evaluate 8 rules
4. Write 8 RULE_EVALUATED audit events
5. Create alert (if rules matched)
6. Write ALERT_GENERATED audit event (if alert created)
7. Commit all changes atomically
```

If any step fails, the entire transaction (including all audit events) rolls back, ensuring no orphaned audit records.

## Atomic Behavior Guarantees

### Success Case
When a transaction is successfully ingested:
- Transaction persisted ✓
- TRANSACTION_INGESTED event recorded ✓
- 8 rule evaluations persisted ✓
- 8 RULE_EVALUATED events recorded ✓
- Alert created (if matched) ✓
- ALERT_GENERATED event recorded (if alert created) ✓
- All committed together ✓

### Failure Case
When transaction ingestion fails (e.g., account not found):
- Transaction NOT persisted ✗
- No audit events recorded ✗
- HTTP 404 returned to client
- Database remains consistent

This prevents orphaned audit events where the business action failed but an audit record was left behind.

## Immutability Enforcement

Audit events are immutable by design:

1. **Repository Level**: `AuditRepository` only provides `insert()` method, no update or delete
2. **Service Level**: `AuditService.record_event()` only creates new events
3. **API Level**: Audit router only exposes GET endpoint, no PUT/PATCH/DELETE routes
4. **Database Level**: Application never updates or deletes audit_events rows

## Seed Data

The seed script creates sample audit events for demonstration:
- TRANSACTION_INGESTED events for sample transactions
- ALERT_GENERATED events for sample alerts

Seed is idempotent - checks for existing events before creating.

## Test Coverage

### Unit Tests (test_audit_service.py)
- Event recording with user actor
- Event recording with system actor
- Paginated retrieval
- Filter by entity_type
- Filter by entity_id
- Filter by actor_id
- Filter by correlation_id
- Timestamp ordering (descending)
- Combined filters
- Immutability verification

### Integration Tests (test_audit_integration.py)
- Transaction ingestion creates TRANSACTION_INGESTED event
- Rule evaluation creates RULE_EVALUATED events
- Alert generation creates ALERT_GENERATED event
- Correlation ID propagation across workflow
- Failed transaction creates no orphaned audit events
- API endpoint authentication requirement
- API retrieval by entity filters
- API retrieval by correlation_id
- API pagination
- API immutability (no PUT/PATCH/DELETE endpoints)

## Security

- **Authentication**: All audit endpoints require JWT authentication
- **Authorization**: Currently authenticated users can view all audit events (no row-level restrictions yet)
- **Immutability**: No edit or delete operations exposed
- **Audit Trail**: All events record actor information (user_id, username, role)

## Future Enhancements (Out of Current Scope)

The audit service is ready to support case management workflow events when those features are implemented:
- CASE_CREATED
- CASE_DECISION
- INFORMATION_REQUESTED
- INFORMATION_RESPONSE_RECORDED
- CASE_ASSIGNMENT_CHANGED
- CASE_STATE_TRANSITION

The schema, repository, service, and API already support these event types through the flexible action/entity_type/details structure.
