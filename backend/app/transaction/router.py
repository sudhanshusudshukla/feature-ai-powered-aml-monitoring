"""Transaction API router."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.common.correlation import generate_correlation_id
from app.common.errors import DomainValidationError, NotFoundError
from app.common.pagination import PaginatedResponse
from app.customer.models import Account, Customer
from app.database import get_db
from app.security.dependencies import get_current_user
from app.security.models import User
from app.transaction.models import Transaction
from app.transaction.schemas import (
    TransactionDetailResponse,
    TransactionIngestRequest,
    TransactionIngestResponse,
    TransactionListItem,
)
from app.transaction.service import TransactionService

router = APIRouter()


@router.get("", response_model=PaginatedResponse[TransactionListItem])
def list_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    outcome: Optional[str] = Query(None, description="Filter by outcome: alert_raised or no_alert"),
    amount_min: Optional[Decimal] = Query(None, description="Minimum amount"),
    amount_max: Optional[Decimal] = Query(None, description="Maximum amount"),
    date_from: Optional[datetime] = Query(None, description="Filter by timestamp >= date_from"),
    date_to: Optional[datetime] = Query(None, description="Filter by timestamp <= date_to"),
    sort_by: str = Query("timestamp", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List transactions with pagination, filtering, and sorting.
    
    Requires authentication.
    """
    # Build base query - left join with Alert to get alert_raised status
    from app.alert.models import Alert
    from app.rules.models import RuleEvaluationResult
    
    query = (
        db.query(
            Transaction.id,
            Transaction.transaction_reference,
            Transaction.account_id,
            Customer.full_name.label("customer_name"),
            Transaction.amount,
            Transaction.currency,
            Transaction.transaction_type,
            Transaction.origin_country,
            Transaction.destination_country,
            Transaction.transaction_timestamp.label("timestamp"),
            func.count(func.distinct(RuleEvaluationResult.id)).label("matched_rules_count"),
            Alert.id.label("alert_id")
        )
        .join(Account, Transaction.account_id == Account.id)
        .join(Customer, Account.customer_id == Customer.id)
        .outerjoin(Alert, Alert.transaction_id == Transaction.id)
        .outerjoin(RuleEvaluationResult, RuleEvaluationResult.transaction_id == Transaction.id)
        .group_by(
            Transaction.id,
            Transaction.transaction_reference,
            Transaction.account_id,
            Customer.full_name,
            Transaction.amount,
            Transaction.currency,
            Transaction.transaction_type,
            Transaction.origin_country,
            Transaction.destination_country,
            Transaction.transaction_timestamp,
            Alert.id
        )
    )
    
    # Apply filters
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    if outcome:
        if outcome == "alert_raised":
            query = query.filter(Alert.id.isnot(None))
        elif outcome == "no_alert":
            query = query.filter(Alert.id.is_(None))
    if amount_min is not None:
        query = query.filter(Transaction.amount >= amount_min)
    if amount_max is not None:
        query = query.filter(Transaction.amount <= amount_max)
    if date_from:
        query = query.filter(Transaction.transaction_timestamp >= date_from)
    if date_to:
        query = query.filter(Transaction.transaction_timestamp <= date_to)
    
    # Get total count before pagination
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(Transaction, sort_by if sort_by != "timestamp" else "transaction_timestamp", Transaction.transaction_timestamp)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Apply pagination
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()
    
    # Convert to response models
    items = [
        TransactionListItem(
            id=row.id,
            transaction_reference=row.transaction_reference,
            account_id=row.account_id,
            customer_name=row.customer_name,
            amount=str(row.amount),
            currency=row.currency,
            transaction_type=row.transaction_type,
            origin_country=row.origin_country,
            destination_country=row.destination_country,
            timestamp=row.timestamp,
            matched_rules_count=row.matched_rules_count or 0,
            alert_raised=row.alert_id is not None,
            alert_id=row.alert_id
        )
        for row in results
    ]
    
    return PaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total
    )


@router.post("", response_model=TransactionIngestResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    request: TransactionIngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingest a new transaction.
    
    Protected endpoint requiring authentication.
    Returns HTTP 201 with transaction details and evaluation summary.
    """
    service = TransactionService(db)
    correlation_id = generate_correlation_id()
    
    try:
        response = service.ingest_transaction(request, correlation_id)
        return response
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{transaction_id}", response_model=TransactionDetailResponse)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve transaction detail.
    
    Protected endpoint requiring authentication.
    Returns HTTP 200 with complete transaction and evaluation results.
    Returns HTTP 404 if transaction not found.
    """
    service = TransactionService(db)
    
    try:
        response = service.get_transaction_detail(transaction_id)
        return response
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
