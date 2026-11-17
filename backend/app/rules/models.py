"""Rules domain models: detection rules, versions, and evaluation results."""
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DetectionRule(Base):
    """Detection rule catalog with stable identity."""
    __tablename__ = "detection_rules"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_code: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    versions: Mapped[list["RuleVersion"]] = relationship("RuleVersion", back_populates="rule")
    evaluations: Mapped[list["RuleEvaluationResult"]] = relationship("RuleEvaluationResult", back_populates="rule")


class RuleVersion(Base):
    """Rule parameter version snapshot."""
    __tablename__ = "rule_versions"
    __table_args__ = (
        UniqueConstraint("rule_id", "version_number", name="uq_rule_version"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("detection_rules.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    parameters_json: Mapped[str] = mapped_column(Text, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    changed_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    change_reason: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    rule: Mapped["DetectionRule"] = relationship("DetectionRule", back_populates="versions")


class RuleEvaluationResult(Base):
    """Immutable rule evaluation result per transaction-rule pair."""
    __tablename__ = "rule_evaluation_results"
    __table_args__ = (
        UniqueConstraint("transaction_id", "rule_id", name="uq_transaction_rule"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(Integer, ForeignKey("transactions.id"), nullable=False, index=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("detection_rules.id"), nullable=False)
    rule_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    result: Mapped[str] = mapped_column(String(10), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    rule: Mapped["DetectionRule"] = relationship("DetectionRule", back_populates="evaluations")
    transaction = relationship("Transaction", back_populates="evaluation_results")
