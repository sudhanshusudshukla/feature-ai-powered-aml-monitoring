# TASK-4 Handoff: Transaction Screening Service and Account Context

## Completed Work

This task implemented account context retrieval and screening service infrastructure needed for rule evaluation in the AML Transaction Monitoring Platform.

## Backend Endpoints Added

API prefix: /api/v1

### Customer Endpoints

GET /api/v1/customers/{customer_id}

GET /api/v1/customers/accounts/{account_id}

## Account Context Data Structure

### ScreeningContext

Complete screening context loaded for every transaction evaluation:

```python
{
    "account_id": int,
    "account_number": str,
    "account_status": str,
    "customer_id": int,
    "customer_number": str,
    "customer_full_name": str,
    "residency_country": str,
    "pep_status": bool,
    "sanctioned_status": bool,
    "risk_level": str,
    "risk_base_score": int,
    "historical_metrics": HistoricalMetrics,
    "correlation_id": str
}
```

### HistoricalMetrics

Historical transaction metrics computed from account transaction history:

```python
{
    "rolling_24h_total": Decimal,      # Sum of amounts in last 24 hours
    "rolling_7d_count": int,            # Count of transactions in last 7 days
    "rolling_30m_count": int,           # Count of transactions in last 30 minutes
    "rolling_30m_total": Decimal,       # Sum of amounts in last 30 minutes
    "rolling_90d_average": Decimal,     # Average transaction amount over 90 days
    "cross_border_count": int,          # Count of cross-border transactions (origin != destination)
    "high_risk_country_flag": bool,     # Whether any recent transaction involved high-risk countries (stub)
    "prior_alert_count": int            # Count of alerts for this account
}
```

## Service Integration

### TransactionService Integration

The transaction ingestion flow now:
1. Loads complete `ScreeningContext` via `AccountRepository.get_screening_context()`
2. Validates account exists, customer exists, and risk profile exists
3. Computes historical metrics from transaction history
4. Fails cleanly with `NotFoundError` if account, customer, or risk profile missing

### Repository Methods

`AccountRepository.get_screening_context(account_id, correlation_id)`:
- Loads account with eager-loaded customer and risk profile relationships
- Computes historical metrics
- Returns complete `ScreeningContext` ready for rule evaluation
- Raises `NotFoundError` if any required entity is missing

`AccountRepository.get_transaction_window_metrics(account_id, customer_id, as_of)`:
- Computes rolling time window aggregates (24h, 7d, 30m, 90d)
- Counts cross-border transactions
- Counts prior alerts for the account
- Returns zero values for empty history

## Transaction Ingestion Behavior

### Successful Ingestion
- Account exists with complete customer and risk profile
- Screening context loads successfully
- Transaction persists with correlation ID
- Historical metrics computed from prior transactions
- Returns HTTP 201 with transaction details

### Failed Ingestion
- Missing account: HTTP 404 "Account not found"
- Missing customer: HTTP 404 "Customer not found for account"
- Missing risk profile: HTTP 404 "Risk profile not found for customer"
- No partial transaction created on failure

## Seed Data Requirements

For successful transaction ingestion, the following seed data must exist:

1. Customer record with `customer_number`, `full_name`, `residency_country`, `pep_status`, `sanctioned_status`
2. CustomerRiskProfile record linked to customer with `risk_level`, `base_score`
3. Account record linked to customer with `account_number`, `status`, `current_balance`

Example seed records in `backend/app/seed.py`:
- Customer: CUST001, CUST002
- Risk profiles: One per customer
- Accounts: ACC001 (CUST001), ACC002 (CUST002)

## Historical Metrics Computation

All metrics are account-scoped (not customer-scoped):
- Queries filter by `account_id` only
- Multiple accounts for same customer maintain separate histories
- Time windows calculated relative to `as_of` parameter
- Cross-border detection: `origin_country != destination_country`
- Prior alerts counted via `Alert JOIN Transaction ON transaction_id`

## Testing Coverage

### Unit Tests (test_customer_service.py)
- Customer and account retrieval success/not found
- Screening context loading with complete data
- Missing account, customer, risk profile failures
- Empty transaction history metrics (all zeros)
- Historical metrics with multiple time windows
- Prior alert count computation

### Integration Tests (test_customer_integration.py)
- Customer and account API endpoints
- Transaction ingestion with context loading
- Transaction ingestion failures (missing account, risk profile)
- Historical metrics included in screening context
- Account-level metric isolation (not customer-wide)

## Next Tasks

This task provides the foundation for:
- **TASK-5 (Rule Evaluation Engine)**: Use `ScreeningContext` and `HistoricalMetrics` for eight deterministic AML rules
- **TASK-6 (Alert Generation)**: Use risk attributes (PEP status, sanctioned status, risk level) for priority calculation
- **TASK-7 (Audit Service)**: Correlation IDs propagated through screening context

## Known Limitations

- `high_risk_country_flag` is stubbed as `False` - will be implemented when CountryRisk table is seeded
- No caching of historical metrics (computed fresh each time)
- Metrics computation uses UTC timestamps consistently

## Files Modified

- `/repos/feature-ai-powered-aml-monitoring/backend/app/customer/schemas.py` (new)
- `/repos/feature-ai-powered-aml-monitoring/backend/app/customer/repository.py` (new)
- `/repos/feature-ai-powered-aml-monitoring/backend/app/customer/service.py` (new)
- `/repos/feature-ai-powered-aml-monitoring/backend/app/customer/router.py` (new)
- `/repos/feature-ai-powered-aml-monitoring/backend/app/transaction/service.py` (modified)
- `/repos/feature-ai-powered-aml-monitoring/backend/app/main.py` (modified)
- `/repos/feature-ai-powered-aml-monitoring/backend/tests/test_customer_service.py` (new)
- `/repos/feature-ai-powered-aml-monitoring/backend/tests/test_customer_integration.py` (new)
