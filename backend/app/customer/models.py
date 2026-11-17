"""Customer domain models: customers, accounts, and risk profiles."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    """Customer entity with synthetic data markers."""
    __tablename__ = "customers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    residency_country: Mapped[str] = mapped_column(String(2), nullable=False)
    pep_status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sanctioned_status: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    synthetic_source: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    accounts: Mapped[list["Account"]] = relationship("Account", back_populates="customer")
    risk_profile: Mapped["CustomerRiskProfile"] = relationship("CustomerRiskProfile", back_populates="customer", uselist=False)


class CustomerRiskProfile(Base):
    """Customer risk assessment profile."""
    __tablename__ = "customer_risk_profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), unique=True, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    base_score: Mapped[int] = mapped_column(Integer, nullable=False)
    last_reviewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reviewed_by: Mapped[str] = mapped_column(String(64), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="risk_profile")


class Account(Base):
    """Account entity linked to customer."""
    __tablename__ = "accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", lazy="select")
