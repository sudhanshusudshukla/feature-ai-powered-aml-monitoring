"""Transaction domain models."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Transaction(Base):
    """Transaction entity with full ingestion details."""
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_reference: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    origin_country: Mapped[str] = mapped_column(String(2), nullable=False)
    destination_country: Mapped[str] = mapped_column(String(2), nullable=False)
    counterparty_name: Mapped[str] = mapped_column(String(255), nullable=True)
    counterparty_account: Mapped[str] = mapped_column(String(100), nullable=True)
    transaction_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    account = relationship("Account", back_populates="transactions", lazy="select")
    evaluation_results = relationship("RuleEvaluationResult", back_populates="transaction", lazy="select")
    alert = relationship("Alert", back_populates="transaction", uselist=False, lazy="select")
