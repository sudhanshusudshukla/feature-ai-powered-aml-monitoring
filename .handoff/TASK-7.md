# TASK-7 Handoff: Backend Feature B5 - Case Workflow Persistence

## Completion Summary
Case workflow table structures and concurrency patterns are verified and complete. All case-related tables exist in the database schema with proper foreign keys, unique constraints, and optimistic locking for mutable entities.

## Case Workflow Table Structures

### Core Case Table: `aml_cases`
**Purpose:** Persistent case entity with state machine lifecycle

**Columns:**
- `id` — Integer primary key (auto-increment)
- `case_number` — String(32), UNIQUE, NOT NULL (stable business identifier)
- `title` — String(255), NOT NULL
- `customer_id` — Integer FK to customers.id, NOT NULL, indexed
- `state` — String(32), NOT NULL, indexed (CaseState enum values)
- `priority` — String(20), NOT NULL (AlertPriority values)
- `created_by_user_id` — Integer FK to users.id, NOT NULL
- `assigned_to_user_id` — Integer FK to users.id, NULL, indexed
- `closure_reason` — Text, NULL
- `created_at` — DateTime, NOT NULL
- `updated_at` — DateTime, NOT NULL (auto-updated)
- `version` — Integer, NOT NULL, default 1 (optimistic locking)

**Constraints:**
- UNIQUE(case_number)
- FK(customer_id) → customers(id)
- FK(created_by_user_id) → users(id)
- FK(assigned_to_user_id) → users(id)
- Optimistic locking via version field

**Relationships:**
- `alert_links`: one-to-many CaseAlertLink
- `notes`: one-to-many CaseNote
- `decisions`: one-to-many CaseDecision

### Alert Linking: `case_alert_links`
**Purpose:** Many-to-many link between cases and alerts with append-only behavior

**Columns:**
- `id` — Integer primary key (auto-increment)
- `case_id` — Integer FK to aml_cases.id, NOT NULL, indexed
- `alert_id` — Integer FK to alerts.id, NOT NULL
- `linked_at` — DateTime, NOT NULL
- `linked_by_user_id` — Integer FK to users.id, NOT NULL

**Constraints:**
- UNIQUE(case_id, alert_id) — no duplicate links within same case
- UNIQUE(alert_id) — each alert can belong to at most one case
- FK(case_id) → aml_cases(id)
- FK(alert_id) → alerts(id)
- FK(linked_by_user_id) → users(id)
- Append-only: no version field, no updates

### Investigation Notes: `case_notes`
**Purpose:** Immutable append-only case notes

**Columns:**
- `id` — Integer primary key (auto-increment)
- `case_id` — Integer FK to aml_cases.id, NOT NULL, indexed
- `note_text` — Text, NOT NULL
- `created_by_user_id` — Integer FK to users.id, NOT NULL
- `created_at` — DateTime, NOT NULL

**Constraints:**
- FK(case_id) → aml_cases(id)
- FK(created_by_user_id) → users(id)
- Append-only: no version field, no updated_at, no updates

### Information Requests: `information_requests`
**Purpose:** Mutable information request entity with status lifecycle

**Columns:**
- `id` — Integer primary key (auto-increment)
- `case_id` — Integer FK to aml_cases.id, NOT NULL, indexed
- `requested_what` — Text, NOT NULL
- `reason` — Text, NOT NULL
- `due_date` — DateTime, NOT NULL
- `status` — String(20), NOT NULL, indexed (InformationRequestStatus enum)
- `requested_by_user_id` — Integer FK to users.id, NOT NULL
- `created_at` — DateTime, NOT NULL
- `updated_at` — DateTime, NOT NULL (auto-updated)
- `version` — Integer, NOT NULL, default 1 (optimistic locking)

**Constraints:**
- FK(case_id) → aml_cases(id)
- FK(requested_by_user_id) → users(id)
- Optimistic locking via version field (status is mutable)

**Relationships:**
- `response`: one-to-one InformationResponse

### Information Responses: `information_responses`
**Purpose:** One-to-one immutable response to information request

**Columns:**
- `id` — Integer primary key (auto-increment)
- `information_request_id` — Integer FK to information_requests.id, UNIQUE, NOT NULL
- `response_text` — Text, NOT NULL
- `responded_by_user_id` — Integer FK to users.id, NOT NULL
- `responded_at` — DateTime, NOT NULL

**Constraints:**
- UNIQUE(information_request_id) — one-to-one relationship
- FK(information_request_id) → information_requests(id)
- FK(responded_by_user_id) → users(id)
- Append-only: no version field, no updates

### Case Decisions: `case_decisions`
**Purpose:** Immutable append-only case decision records

**Columns:**
- `id` — Integer primary key (auto-increment)
- `case_id` — Integer FK to aml_cases.id, NOT NULL, indexed
- `decision` — String(32), NOT NULL (CaseDecision enum values)
- `reason` — Text, NULL
- `comments` — Text, NULL
- `decided_by_user_id` — Integer FK to users.id, NOT NULL
- `decided_at` — DateTime, NOT NULL

**Constraints:**
- FK(case_id) → aml_cases(id)
- FK(decided_by_user_id) → users(id)
- Append-only: no version field, no updated_at, no updates
- Decisions are final once recorded

## Concurrency Patterns

### Optimistic Locking (Mutable Entities)
**Entities with version field:**
- `aml_cases`: state, priority, assignee are mutable
- `information_requests`: status is mutable

**Update Pattern:**
```sql
UPDATE aml_cases
SET state = :new_state,
    updated_at = :updated_at,
    version = version + 1
WHERE id = :id AND version = :expected_version;
```

If affected row count is zero, the service layer raises `OptimisticLockConflictError` (HTTP 409 with detail `STALE_OBJECT`).

### Append-Only Entities (No Updates)
**Entities without version field:**
- `case_alert_links`: created once, never modified
- `case_notes`: immutable after creation
- `information_responses`: one-time response, never edited
- `case_decisions`: final and immutable

Application layer enforces append-only behavior by never calling UPDATE on these tables.

## SQLAlchemy Models

### Location
- `/repos/feature-ai-powered-aml-monitoring/backend/app/case_management/models.py`
  - `AMLCase`
  - `CaseAlertLink`
  - `CaseNote`
  - `CaseDecision`
- `/repos/feature-ai-powered-aml-monitoring/backend/app/investigation/models.py`
  - `InformationRequest`
  - `InformationResponse`

### Model Patterns
All models use SQLAlchemy 2.0 declarative style with `Mapped` type hints and `mapped_column`.

**Mutable entities include:**
- `version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)`
- `updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)`

**Append-only entities exclude:**
- No `version` field
- No `updated_at` field (only `created_at`)

## Migration

**Migration file:** `/repos/feature-ai-powered-aml-monitoring/backend/alembic/versions/20261117_initial_schema.py`

All case workflow tables created in initial migration `001_initial`:
- `aml_cases`
- `case_alert_links`
- `case_notes`
- `information_requests`
- `information_responses`
- `case_decisions`

**Migration verified:** ✅ `alembic upgrade head` applies successfully

## Test Coverage

**Test file:** `/repos/feature-ai-powered-aml-monitoring/backend/tests/test_case_persistence.py`

**Tests verify:**
1. ✅ Case table creation with all fields
2. ✅ UNIQUE(case_number) constraint
3. ✅ Foreign key constraints (customer_id, user_ids)
4. ✅ Optimistic locking on aml_cases (version field)
5. ✅ UNIQUE constraints on case_alert_links (case_id+alert_id, alert_id)
6. ✅ Case notes append-only behavior (no version/updated_at)
7. ✅ Case decisions append-only and final
8. ✅ Optimistic locking on information_requests
9. ✅ UNIQUE(information_request_id) on information_responses (one-to-one)
10. ✅ Complete case workflow relationships traverse correctly
11. ✅ Multiple cases for same customer allowed

**Test results:** 11/11 tests PASSED

## Data Model Guarantees

### Workflow Chain Traceability
Persisted records support joins and queries across full workflow:
- Customer → AMLCase (one-to-many)
- AMLCase → CaseAlertLink → Alert → Transaction (full chain)
- AMLCase → CaseNote (audit notes)
- AMLCase → InformationRequest → InformationResponse (one-to-one)
- AMLCase → CaseDecision (append-only decision log)

### Cross-Database Compatibility
Schema runs on both SQLite (local) and PostgreSQL (deployed) without behavior changes:
- Portable column types (Integer, String, Text, DateTime, Numeric)
- No database-specific SQL operators in queries
- Foreign key constraints enforced on both engines
- Optimistic locking pattern compatible with both engines

### State Machine Support
Case states from `app.common.enums.CaseState`:
- OPEN
- UNDER_INVESTIGATION
- INFORMATION_REQUESTED
- PENDING_DECISION
- ESCALATED
- APPROVED
- REJECTED
- CLOSED

State transitions enforced by `CaseStateMachine` (implementation in future task).

## Next Steps for UI Implementation

### Required Backend Endpoints (Future Tasks)
The following endpoints are NOT implemented in this task. They will be built in subsequent tasks:
- Case creation, retrieval, and decision endpoints (future task)
- Case notes endpoint (future task)
- Information request/response endpoints (future task)

### Case Detail Response Structure
When case detail endpoint is implemented, it will return:
- Case summary (id, case_number, title, customer, state, priority, assignee, creator)
- Linked alerts array (alert summary objects)
- Notes array (chronological)
- Information requests array (with nested responses when present)
- Decision (when recorded)
- Permitted actions array (computed from state + actor role + creator status)
- Version (for optimistic locking)
- Correlation ID

### Seed Data
Case workflow seed data should include:
- Sample cases in various states (OPEN, UNDER_INVESTIGATION, PENDING_DECISION, CLOSED)
- Case-alert links demonstrating one alert per case constraint
- Sample notes showing investigation timeline
- Sample information request with response
- Sample decision records (APPROVE, REJECT, CLOSE_FALSE_POSITIVE)

## Known Constraints

1. **Alert Exclusivity:** Each alert can belong to at most one case (UNIQUE(alert_id))
2. **Creator-Decider Separation:** Application layer must enforce that case creator cannot decide the same case (not DB constraint)
3. **One-to-One Response:** Each information request can have at most one response (UNIQUE(information_request_id))
4. **Append-Only Decisions:** Case decisions are never updated or deleted after recording
5. **Optimistic Conflicts:** Concurrent case/request updates return HTTP 409 STALE_OBJECT when version mismatches

## Acceptance Criteria Status

✅ Migrations apply successfully (`alembic upgrade head`)  
✅ Tests pass (11/11 tests in test_case_persistence.py)  
✅ Persisted transaction, alert, and evaluation records support joins across full workflow chain  
✅ Every mutable entity supports optimistic concurrency handling (aml_cases, information_requests have version fields)  
✅ Data model supports both SQLite and PostgreSQL without changing business behavior  
✅ Case records persist unique identifiers, case numbers, state, priority, creator, assignee, and timestamps  
✅ Linked alerts, notes, information requests, and decisions remain retrievable from persisted case record  
✅ Case decisions are append-only and final once recorded (no version/updated_at fields)
