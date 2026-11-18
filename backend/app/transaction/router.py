"""Transaction API router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.correlation import generate_correlation_id
from app.common.errors import DomainValidationError, NotFoundError
from app.database import get_db
from app.security.dependencies import get_current_user
from app.security.models import User
from app.transaction.schemas import (
    TransactionDetailResponse,
    TransactionIngestRequest,
    TransactionIngestResponse,
)
from app.transaction.service import TransactionService

router = APIRouter()


@router.post("/", response_model=TransactionIngestResponse, status_code=status.HTTP_201_CREATED)
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
