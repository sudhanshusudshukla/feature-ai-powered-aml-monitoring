"""Investigation domain models: information requests and responses."""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class InformationRequest(Base):
    """Information request linked to case."""
    __tablename__ = "information_requests"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[int] = mapped_column(Integer, ForeignKey("aml_cases.id"), nullable=False, index=True)
    requested_what: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    requested_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    # Relationships
    response: Mapped["InformationResponse"] = relationship("InformationResponse", back_populates="request", uselist=False)


class InformationResponse(Base):
    """Response to information request (one-to-one)."""
    __tablename__ = "information_responses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    information_request_id: Mapped[int] = mapped_column(Integer, ForeignKey("information_requests.id"), unique=True, nullable=False)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    responded_by_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    responded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Relationships
    request: Mapped["InformationRequest"] = relationship("InformationRequest", back_populates="response")
