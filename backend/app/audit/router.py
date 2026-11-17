"""Audit router: API endpoints for audit event retrieval."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.audit.schemas import AuditEventListResponse
from app.audit.service import AuditService
from app.database import get_db
from app.security.dependencies import get_current_user
from app.security.models import User

router = APIRouter()


@router.get("/audit", response_model=AuditEventListResponse)
def list_audit_events(
    entity_type: Annotated[str | None, Query(description="Filter by entity type")] = None,
    entity_id: Annotated[int | None, Query(description="Filter by entity ID")] = None,
    actor_id: Annotated[int | None, Query(description="Filter by actor user ID")] = None,
    correlation_id: Annotated[str | None, Query(description="Filter by correlation ID")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page")] = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve audit events with optional filters.
    
    Supports filtering by:
    - entity_type: Type of entity (transaction, alert, case, etc.)
    - entity_id: Specific entity ID
    - actor_id: User who performed the action
    - correlation_id: Correlation ID for tracing related events
    
    Returns paginated results ordered by timestamp (newest first).
    """
    service = AuditService(db)
    return service.list_events(
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        correlation_id=correlation_id,
        page=page,
        page_size=page_size
    )
