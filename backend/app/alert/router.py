"""Alert API router."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.security.dependencies import get_current_user
from app.security.models import User
from app.alert.models import Alert
from app.alert.schemas import AlertDetailResponse, AlertListItem, TransactionSummary, RuleEvaluationSummary, CustomerSnapshotData
from app.transaction.models import Transaction
from app.rules.models import RuleEvaluationResult
from app.customer.models import Account, Customer, CustomerRiskProfile
from app.common.errors import NotFoundError
from app.common.pagination import PaginatedResponse
from app.customer.models import Account, Customer

router = APIRouter()


@router.get("", response_model=PaginatedResponse[AlertListItem])
def list_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assignee: Optional[int] = Query(None, description="Filter by assignee user ID"),
    date_from: Optional[datetime] = Query(None, description="Filter by created_at >= date_from"),
    date_to: Optional[datetime] = Query(None, description="Filter by created_at <= date_to"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List alerts with pagination, filtering, and sorting.
    
    Requires authentication.
    """
    # Build base query
    query = (
        db.query(
            Alert.id,
            Alert.alert_number,
            Alert.transaction_id,
            Alert.risk_score,
            Alert.priority,
            Alert.status,
            Alert.created_at,
            Alert.assigned_to_user_id,
            Customer.full_name.label("customer_name"),
            Transaction.transaction_reference,
            Transaction.amount.label("transaction_amount"),
            Transaction.currency.label("transaction_currency")
        )
        .join(Transaction, Alert.transaction_id == Transaction.id)
        .join(Account, Transaction.account_id == Account.id)
        .join(Customer, Account.customer_id == Customer.id)
    )
    
    # Apply filters
    if status:
        query = query.filter(Alert.status == status)
    if priority:
        query = query.filter(Alert.priority == priority)
    if assignee:
        query = query.filter(Alert.assigned_to_user_id == assignee)
    if date_from:
        query = query.filter(Alert.created_at >= date_from)
    if date_to:
        query = query.filter(Alert.created_at <= date_to)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(Alert, sort_by, Alert.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Apply pagination
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()
    
    # Convert to response models
    items = [
        AlertListItem(
            id=row.id,
            alert_number=row.alert_number,
            transaction_id=row.transaction_id,
            risk_score=row.risk_score,
            priority=row.priority,
            status=row.status,
            created_at=row.created_at,
            assigned_to_user_id=row.assigned_to_user_id,
            customer_name=row.customer_name,
            transaction_reference=row.transaction_reference,
            transaction_amount=str(row.transaction_amount),
            transaction_currency=row.transaction_currency
        )
        for row in results
    ]
    
    return PaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total
    )


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
