"""Case management schemas for request/response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CaseCreateRequest(BaseModel):
    """Request to create a new case from alerts."""
    model_config = ConfigDict(from_attributes=True)
    
    title: str = Field(..., max_length=255, description="Case title")
    alert_ids: list[int] = Field(..., min_length=1, description="Alert IDs to link to case")


class CaseListItem(BaseModel):
    """Case list item for paginated list endpoint."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    case_number: str
    title: str
    customer_id: int
    customer_name: str
    state: str
    priority: str
    created_by_user_id: int
    assigned_to_user_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    alert_count: int


class AlertSummary(BaseModel):
    """Alert summary in case detail response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    alert_number: str
    transaction_id: int
    risk_score: int
    priority: str
    status: str


class NoteSummary(BaseModel):
    """Case note summary."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    note_text: str
    created_by_user_id: int
    created_at: datetime


class DecisionSummary(BaseModel):
    """Case decision summary."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    decision: str
    reason: str | None
    comments: str | None
    decided_by_user_id: int
    decided_at: datetime


class InformationRequestSummary(BaseModel):
    """Information request summary."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    requested_what: str
    reason: str
    due_date: datetime
    status: str
    requested_by_user_id: int
    created_at: datetime


class CaseDetailResponse(BaseModel):
    """Complete case detail response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    case_number: str
    title: str
    customer_id: int
    state: str
    priority: str
    created_by_user_id: int
    assigned_to_user_id: int | None
    closure_reason: str | None
    created_at: datetime
    updated_at: datetime
    version: int
    
    # Related entities
    linked_alerts: list[AlertSummary]
    notes: list[NoteSummary]
    decisions: list[DecisionSummary]
    information_requests: list[InformationRequestSummary]
    
    # Computed fields
    permitted_actions: list[str]


class CaseAssignRequest(BaseModel):
    """Request to assign or reassign a case."""
    model_config = ConfigDict(from_attributes=True)
    
    assigned_to_user_id: int = Field(..., description="User ID to assign case to")
    expected_version: int = Field(..., description="Expected version for optimistic locking")


class CaseDecisionRequest(BaseModel):
    """Request to record a case decision."""
    model_config = ConfigDict(from_attributes=True)
    
    decision: str = Field(..., description="Decision type: APPROVE, REJECT, ESCALATE, CLOSE_FALSE_POSITIVE, REQUEST_INFO")
    reason: str | None = Field(None, description="Reason for decision")
    comments: str | None = Field(None, description="Additional comments")
    expected_version: int = Field(..., description="Expected version for optimistic locking")
