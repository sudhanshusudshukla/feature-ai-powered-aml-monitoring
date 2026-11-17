# TASK-5 Handoff: Rule Evaluation Engine and Alert Service

## Completed Implementation

This task implemented the complete rule evaluation engine with eight independent AML rules, deterministic risk scoring, and alert creation integrated into transaction ingestion.

## Rule Codes and Severity Mappings

All eight AML detection rules are now active and evaluate every transaction:

| Rule Code | Rule Name | Severity | Score (on match) | Description |
|-----------|-----------|----------|------------------|-------------|
| AML-001 | High Value Transaction | HIGH | 30 | Detects transactions exceeding threshold (default: 100,000) |
| AML-002 | Transaction Velocity (Count) | MEDIUM | 20 | Detects unusual transaction frequency (default: >10 in 7 days) |
| AML-003 | Transaction Velocity (Amount) | HIGH | 25 | Detects high volume in short windows (default: >500,000 in 24h) |
| AML-004 | High Risk Geography | MEDIUM | 20 | Detects transactions involving high-risk countries |
| AML-005 | Sanctioned or PEP Customer | CRITICAL | 40 | Detects PEP or sanctioned entity transactions |
| AML-006 | Structuring Pattern | HIGH | 35 | Detects potential structuring (default: >=5 txns in 30m below 50,000) |
| AML-007 | Dormancy Spike | MEDIUM | 25 | Detects sudden activity after dormancy (default: 5x 90-day avg) |
| AML-008 | Round Amount Pattern | LOW | 10 | Detects suspicious round amounts (default: divisible by 10,000) |

## Example Explanations

Each rule generates plain-language explanations in evaluation results:

- **AML-001 Match**: "Transaction amount 150000.00 INR exceeds threshold 100000 INR."
- **AML-001 Pass**: "Transaction amount 50000.00 INR is below threshold 100000 INR."
- **AML-005 Match**: "Customer CUST-003 is flagged as PEP."
- **AML-006 Match**: "Pattern detected: 6 transactions in 30-minute window, current amount 45000.00 INR below threshold 50000."

## Alert Priority Bands

Alerts are created automatically when at least one rule matches. Priority is determined by final risk score:

| Priority | Score Range | Description |
|----------|-------------|-------------|
| CRITICAL | >= 80 | Highest priority, immediate action required |
| HIGH | 60-79 | Urgent review required |
| MEDIUM | 35-59 | Standard review workflow |
| LOW | < 35 | Lower priority monitoring |

**PEP/Sanctioned Floor**: If customer is PEP or sanctioned, priority is raised to at least HIGH regardless of numeric score.

## Risk Score Formula

The risk score is deterministic and bounded to 0-100:

```
base_score = sum(matched_rule_scores)
customer_adjustment = risk_level_adjustment (0, 5, 10, or 15)
geography_adjustment = 10 if high_risk_country else 0
unbounded_score = base_score + customer_adjustment + geography_adjustment
final_score = min(100, max(0, unbounded_score))
```

Customer risk level adjustments:
- LOW: +0
- MEDIUM: +5
- HIGH: +10
- VERY_HIGH: +15

## API Integration

### Transaction Ingestion Response

`POST /api/v1/transactions` now returns complete evaluation results:

```json
{
  "id": 123,
  "transaction_reference": "TX-001",
  "account_id": 456,
  "amount": "150000.00",
  "currency": "INR",
  "transaction_type": "TRANSFER",
  "origin_country": "IN",
  "destination_country": "US",
  "timestamp": "2026-11-17T10:30:00Z",
  "matched_rules_count": 2,
  "alert_raised": true,
  "alert_id": 789,
  "correlation_id": "corr-abc-123",
  "evaluation_results": [
    {
      "rule_code": "AML-001",
      "rule_name": "High Value Transaction",
      "rule_version": 1,
      "outcome": "MATCH",
      "severity": "HIGH",
      "score": 30,
      "explanation": "Transaction amount 150000.00 INR exceeds threshold 100000 INR.",
      "evidence_snapshot": {
        "transaction_amount": "150000.00",
        "currency": "INR",
        "threshold": "100000"
      }
    },
    // ... 7 more evaluation results (one per rule)
  ]
}
```

### Transaction Detail Response

`GET /api/v1/transactions/{id}` retrieves persisted evaluation results from the database, including all 8 rule outcomes and the linked alert (if any).

## Seed Data

### Detection Rules

8 detection rules (AML-001 through AML-008) seeded with version 1 parameters.

### Sample Alerts

Sample alerts created for any transactions that match rules. Alert numbers follow format `ALT-XXXXXX` (6-digit sequential).

### Country Risk

8 countries seeded:
- Low risk: IN, US, GB, SG, CH
- Medium risk: AE
- High risk: KP, IR

### Customers and Accounts

4 sample customers with varying risk profiles:
- CUST-001: Low risk, standard customer
- CUST-002: Medium risk, higher balance
- CUST-003: High risk, PEP status (triggers AML-005)
- CUST-004: Low risk, smaller balance

## Workflow Behavior

1. **Transaction Ingestion**: 
   - Validates account exists
   - Creates transaction record
   - Evaluates all 8 rules synchronously
   - Persists 8 evaluation results
   - Creates alert if matchedRulesCount > 0
   - Commits entire unit of work atomically

2. **Single Rule Failure**: 
   - If any rule evaluation fails, entire ingestion rolls back
   - Returns error to client
   - No partial state persisted

3. **Historical Evaluation Reconstruction**:
   - Each result stores rule_version and evidence_snapshot
   - Historical evaluations remain valid after parameter changes
   - Rule parameters can be versioned without changing evaluator code

## Database Tables Updated

- `detection_rules`: 8 rules inserted
- `rule_versions`: 8 version 1 records
- `rule_evaluation_results`: 8 records per transaction
- `alerts`: 1 record per matched transaction
- `transactions`: Linked to evaluations and alerts

## Testing Coverage

### Unit Tests (test_rules_service.py)
- High value transaction match/pass
- PEP customer match
- Velocity count match
- Structuring pattern match
- All eight rules evaluated

### Unit Tests (test_alert_service.py)
- Alert created for matches
- No alert for zero matches
- Risk score aggregates multiple matches
- PEP priority floor enforcement
- Exact priority band calculations

### Integration Tests (test_rules_integration.py)
- Transaction ingestion evaluates all rules
- High value transaction creates alert
- Transaction detail includes evaluations

### Integration Tests (test_alert_integration.py)
- PEP customer alert priority floor
- Multiple matches aggregate score
- Zero matches no alert

## Notes for Frontend Implementation

1. Display all 8 evaluation results in transaction detail view
2. Show matched rules with highlighted MATCH outcome
3. Display alert badge when alert_raised is true
4. Show priority with color coding (CRITICAL=red, HIGH=orange, MEDIUM=yellow, LOW=gray)
5. Display rule explanations as tooltips or expandable details
6. Link alert_id to alert detail view (when implemented)
7. Show evidence_snapshot in expandable technical details section

## Future Enhancements (Out of Scope for This Task)

- Rule parameter editing UI (deferred to administration tasks)
- Alert assignment and workflow (case management tasks)
- Audit event capture for rule evaluation (audit service tasks)
- Rule versioning UI and history (administration tasks)
