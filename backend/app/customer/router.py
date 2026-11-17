"""Customer API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.errors import NotFoundError
from app.customer.schemas import AccountResponse, CustomerResponse
from app.customer.service import CustomerService
from app.database import get_db
from app.security.dependencies import get_current_user
from app.security.schemas import UserResponse

router = APIRouter()


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve customer by ID."""
    try:
        service = CustomerService(db)
        return service.get_customer(customer_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/accounts/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """Retrieve account by ID."""
    try:
        service = CustomerService(db)
        return service.get_account(account_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
