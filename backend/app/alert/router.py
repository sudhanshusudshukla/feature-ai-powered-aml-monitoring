"""Alert API router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.security.dependencies import get_current_user
from app.security.models import User
from app.alert.models import Alert
from app.alert.schemas import AlertDetailResponse, TransactionSummary, RuleEvaluationSummary, CustomerSnapshotData
from app.transaction.models import Transaction
from app.rules.models import RuleEvaluationResult
from app.customer.models import Account, Customer, CustomerRiskProfile
from app.common.errors import NotFoundError

router = APIRouter()


@router.get("/{alert_id}", response_model=AlertDetailResponse)
def get_alert_detail(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve complete alert detail including transaction, matched rules,
    risk score breakdown, and customer snapshot.
    
    Requires authentication.
    """
    alert = (
        db.query(Alert)
        .options(
            joinedload(Alert.transaction)
            .joinedload(Transaction.evaluation_results)
        )
        .options(
            joinedload(Alert.transaction)
            .joinedload(Transaction.account)
            .joinedload(Account.customer)
            .joinedload(Customer.risk_profile)
        )
        .filter(Alert.id == alert_id)
        .first()
    )
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Parse priority_rationale to extract score breakdown
    # Format expected: "Priority X: final score Y. Base score Z. Customer risk adjustment A. Geography adjustment B..."
    base_score = 0
    customer_risk_adjustment = 0
    geography_adjustment = 0
    
    if alert.priority_rationale:
        parts = alert.priority_rationale.split(".")
        for part in parts:
            if "base score" in part.lower():
                try:
                    base_score = int(part.split()[-1])
                except (ValueError, IndexError):
                    pass
            elif "customer risk adjustment" in part.lower():
                try:
                    adj_str = part.split()[-1]
                    customer_risk_adjustment = int(adj_str.replace("+", ""))
                except (ValueError, IndexError):
                    pass
            elif "geography adjustment" in part.lower():
                try:
                    adj_str = part.split()[-1]
                    geography_adjustment = int(adj_str.replace("+", ""))
                except (ValueError, IndexError):
                    pass
    
    # Get matched rules only
    matched_rules = []
    for result in alert.transaction.evaluation_results:
        if result.result == "MATCH":
            # Parse evidence_snapshot JSON
            import json
            try:
                evidence_dict = json.loads(result.evidence_snapshot)
            except (json.JSONDecodeError, TypeError):
                evidence_dict = {}
            
            matched_rules.append(RuleEvaluationSummary(
                rule_code=result.rule_code,
                rule_name=result.rule.name,
                rule_version=result.rule_version,
                outcome=result.result,
                severity=result.severity,
                score=result.score,
                explanation=result.explanation,
                evidence_snapshot=evidence_dict
            ))
    
    # Build customer snapshot
    account = alert.transaction.account
    customer = account.customer
    risk_profile = customer.risk_profile
    
    customer_snapshot = CustomerSnapshotData(
        customer_id=customer.id,
        customer_number=customer.customer_number,
        full_name=customer.full_name,
        residency_country=customer.residency_country,
        pep_status=customer.pep_status,
        sanctioned_status=customer.sanctioned_status,
        risk_level=risk_profile.risk_level if risk_profile else "LOW",
        account_number=account.account_number,
        account_status=account.status
    )
    
    # Build transaction summary manually
    transaction_summary = TransactionSummary(
        id=alert.transaction.id,
        transaction_reference=alert.transaction.transaction_reference,
        amount=str(alert.transaction.amount),
        currency=alert.transaction.currency,
        transaction_type=alert.transaction.transaction_type,
        origin_country=alert.transaction.origin_country,
        destination_country=alert.transaction.destination_country,
        timestamp=alert.transaction.transaction_timestamp
    )
    
    return AlertDetailResponse(
        id=alert.id,
        alert_number=alert.alert_number,
        transaction_id=alert.transaction_id,
        risk_score=alert.risk_score,
        priority=alert.priority,
        status=alert.status,
        created_at=alert.created_at,
        priority_rationale=alert.priority_rationale,
        assigned_to_user_id=alert.assigned_to_user_id,
        base_score=base_score,
        customer_risk_adjustment=customer_risk_adjustment,
        geography_adjustment=geography_adjustment,
        transaction=transaction_summary,
        matched_rules=matched_rules,
        customer_snapshot=customer_snapshot
    )
