"""Alert domain models."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Alert(Base):
    """Alert generated from matched transaction."""
    __tablename__ = "alerts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id"), unique=True, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    assigned_to_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    priority_rationale: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="alert")
