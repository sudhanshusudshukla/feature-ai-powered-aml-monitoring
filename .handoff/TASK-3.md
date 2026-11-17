# TASK-3 Handoff: Transaction Ingestion and API Transport

## Endpoints Mounted

- `POST /api/v1/transactions/` - Transaction ingestion endpoint (protected, requires authentication)
- `GET /api/v1/transactions/{id}` - Transaction detail retrieval (protected, requires authentication)

## Request/Response Shapes

### POST /api/v1/transactions/

**Request:**
```json
{
  "transaction_reference": "string",
  "account_id": integer,
  "amount": "decimal string",
  "currency": "string (default: INR)",
  "transaction_type": "TRANSFER | DEPOSIT | WITHDRAWAL | PAYMENT",
  "origin_country": "2-char code",
  "destination_country": "2-char code",
  "counterparty_name": "string (optional)",
  "counterparty_account": "string (optional)",
  "timestamp": "ISO datetime"
}
```

**Response (201):**
```json
{
  "id": integer,
  "transaction_reference": "string",
  "account_id": integer,
  "amount": "string",
  "currency": "string",
  "transaction_type": "string",
  "origin_country": "string",
  "destination_country": "string",
  "timestamp": "ISO datetime",
  "matched_rules_count": integer,
  "alert_raised": boolean,
  "alert_id": integer | null,
  "correlation_id": "string",
  "evaluation_results": []
}
```

### GET /api/v1/transactions/{id}

**Response (200):**
```json
{
  "id": integer,
  "transaction_reference": "string",
  "account_id": integer,
  "amount": "string",
  "currency": "string",
  "transaction_type": "string",
  "origin_country": "string",
  "destination_country": "string",
  "counterparty_name": "string | null",
  "counterparty_account": "string | null",
  "timestamp": "ISO datetime",
  "matched_rules_count": integer,
  "alert_raised": boolean,
  "alert_id": integer | null,
  "evaluation_results": [],
  "correlation_id": "string"
}
```

## Placeholder Notes

**Rule Evaluation:** The `evaluation_results` field returns an empty array for now. Rule evaluation logic (AML-001 through AML-008) will be implemented in task B2. Each evaluation will produce a `RuleEvaluationItem` with:
- `rule_code`, `rule_name`, `rule_version`
- `outcome` (PASS or MATCH)
- `severity`, `score`, `explanation`, `evidence_snapshot`

**Alert Logic:** The `matched_rules_count` is currently 0, `alert_raised` is always false, and `alert_id` is always null. Alert creation based on rule matches will be implemented in task B3.

**Audit Events:** Audit event recording for transaction ingestion, rule evaluation, and alert generation will be added in subsequent tasks when the audit service is wired.

## Authentication

Both endpoints are protected and require:
```
Authorization: Bearer <jwt-token>
```

Returns 401 if missing/invalid authentication.

## Error Responses

- 400: Validation error (missing required fields)
- 401: Not authenticated
- 404: Account not found (ingestion) or Transaction not found (detail)
- 422: Validation error (Pydantic)

## Seed Data for Testing

Use the existing test user credentials from the seed:
- Email: `officer@example.com`
- Password: `Officer-pass-1`

Create test customers and accounts via fixtures or seed script for transaction testing.

## Implementation Status

**Complete:**
- Transaction model (from TASK-1)
- Transaction schemas with Pydantic validation
- TransactionRepository with create and get_by_id
- TransactionService with ingest and detail retrieval stubs
- TransactionRouter with both endpoints
- Security dependencies for JWT verification
- Router mounted under /api/v1/transactions
- Unit tests for service layer
- Integration tests for API endpoints

**Deferred to Later Tasks:**
- Rule evaluation engine (TASK B2)
- Alert creation logic (TASK B3)
- Audit event recording (TASK B4+)
