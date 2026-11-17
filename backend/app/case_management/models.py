"""Case management domain models."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AMLCase(Base):
    """AML case entity with state machine lifecycle."""
    __tablename__ = "aml_cases"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_to_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    closure_reason: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    alert_links: Mapped[list["CaseAlertLink"]] = relationship("CaseAlertLink", back_populates="case")
    notes: Mapped[list["CaseNote"]] = relationship("CaseNote", back_populates="case")
    decisions: Mapped[list["CaseDecision"]] = relationship("CaseDecision", back_populates="case")


class CaseAlertLink(Base):
    """Link between case and alert."""
    __tablename__ = "case_alert_links"
    __table_args__ = (
        UniqueConstraint("case_id", "alert_id", name="uq_case_alert"),
        UniqueConstraint("alert_id", name="uq_alert_case"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("aml_cases.id"), nullable=False, index=True)
    alert_id: Mapped[int] = mapped_column(Integer, ForeignKey("alerts.id"), nullable=False)
    linked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    linked_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    case: Mapped["AMLCase"] = relationship("AMLCase", back_populates="alert_links")


class CaseNote(Base):
    """Immutable case note."""
    __tablename__ = "case_notes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("aml_cases.id"), nullable=False, index=True)
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    case: Mapped["AMLCase"] = relationship("AMLCase", back_populates="notes")


class CaseDecision(Base):
    """Immutable case decision record."""
    __tablename__ = "case_decisions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("aml_cases.id"), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    comments: Mapped[str] = mapped_column(Text, nullable=True)
    decided_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Relationships
    case: Mapped["AMLCase"] = relationship("AMLCase", back_populates="decisions")
