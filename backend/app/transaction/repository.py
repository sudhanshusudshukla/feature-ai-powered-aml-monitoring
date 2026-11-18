"""Transaction repository for database operations."""

from sqlalchemy.orm import Session

from app.transaction.models import Transaction


class TransactionRepository:
    """Repository for transaction persistence."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, transaction: Transaction) -> Transaction:
        """
        Persist a new transaction.
        Returns the persisted transaction with ID.
        """
        self.db.add(transaction)
        self.db.flush()
        self.db.refresh(transaction)
        return transaction
    
    def get_by_id(self, transaction_id: int) -> Transaction | None:
        """
        Retrieve transaction by ID.
        Returns None if not found.
        """
        return self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
