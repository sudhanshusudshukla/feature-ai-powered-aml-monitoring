"""Customer service for business logic."""
from sqlalchemy.orm import Session

from app.common.errors import NotFoundError
from app.customer.repository import AccountRepository, CustomerRepository
from app.customer.schemas import AccountResponse, CustomerResponse, ScreeningContext


class CustomerService:
    """Service for customer and account operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.customer_repository = CustomerRepository(db)
        self.account_repository = AccountRepository(db)
    
    def get_customer(self, customer_id: int) -> CustomerResponse:
        """Retrieve customer by ID."""
        customer = self.customer_repository.get_customer_by_id(customer_id)
        if not customer:
            raise NotFoundError("Customer not found")
        return CustomerResponse.model_validate(customer)
    
    def get_account(self, account_id: int) -> AccountResponse:
        """Retrieve account by ID."""
        account = self.customer_repository.get_account_by_id(account_id)
        if not account:
            raise NotFoundError("Account not found")
        return AccountResponse.from_orm_with_decimal(account)
    
    def get_screening_context(self, account_id: int, correlation_id: str) -> ScreeningContext:
        """
        Retrieve complete screening context for transaction evaluation.
        
        This is the primary entry point for rule evaluation context loading.
        """
        return self.account_repository.get_screening_context(
            account_id=account_id,
            correlation_id=correlation_id
        )
