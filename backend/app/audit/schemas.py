"""Audit domain schemas: request and response models for audit events."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditEventCreate(BaseModel):
    """Schema for creating an audit event."""
    action: str
    entity_type: str
    entity_id: int
    details: dict[str, Any]
    
    model_config = ConfigDict(from_attributes=True)


class AuditEventResponse(BaseModel):
    """Schema for audit event response."""
    id: int
    timestamp: datetime
    actor_user_id: int | None
    actor_username: str
    actor_role: str
    action: str
    entity_type: str
    entity_id: int
    correlation_id: str
    details_json: str
    
    model_config = ConfigDict(from_attributes=True)


class AuditEventListResponse(BaseModel):
    """Schema for paginated audit event list response."""
    items: list[AuditEventResponse]
    page: int
    page_size: int
    total: int
    
    model_config = ConfigDict(from_attributes=True)
