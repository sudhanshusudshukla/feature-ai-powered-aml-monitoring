"""Audit service: event recording and retrieval orchestration."""
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.audit.models import AuditEvent
from app.audit.repository import AuditRepository
from app.audit.schemas import AuditEventListResponse, AuditEventResponse


class AuditService:
    """Service for recording and retrieving audit events."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = AuditRepository(db)
    
    def record_event(
        self,
        action: str,
        entity_type: str,
        entity_id: int,
        correlation_id: str,
        details: dict,
        actor_user_id: int | None = None,
        actor_username: str = "system",
        actor_role: str = "system"
    ) -> AuditEvent:
        """
        Record an immutable audit event.
        
        Args:
            action: Action performed (e.g., TRANSACTION_INGESTED, RULE_EVALUATED)
            entity_type: Type of entity (e.g., transaction, alert, case)
            entity_id: ID of the affected entity
            correlation_id: Correlation ID for request tracing
            details: Additional details as dictionary
            actor_user_id: User ID performing the action (None for system actions)
            actor_username: Username or system identifier
            actor_role: Role of the actor
        
        Returns:
            Persisted audit event
        """
        event = AuditEvent(
            timestamp=datetime.utcnow(),
            actor_user_id=actor_user_id,
            actor_username=actor_username,
            actor_role=actor_role,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            correlation_id=correlation_id,
            details_json=json.dumps(details)
        )
        
        return self.repository.insert(event)
    
    def list_events(
        self,
        entity_type: str | None = None,
        entity_id: int | None = None,
        actor_id: int | None = None,
        correlation_id: str | None = None,
        page: int = 1,
        page_size: int = 50
    ) -> AuditEventListResponse:
        """
        Retrieve audit events with optional filters and pagination.
        
        Args:
            entity_type: Filter by entity type
            entity_id: Filter by entity ID
            actor_id: Filter by actor user ID
            correlation_id: Filter by correlation ID
            page: Page number (1-indexed)
            page_size: Number of items per page
        
        Returns:
            Paginated list of audit events
        """
        offset = (page - 1) * page_size
        
        events, total = self.repository.list_events(
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            correlation_id=correlation_id,
            offset=offset,
            limit=page_size
        )
        
        items = [
            AuditEventResponse(
                id=event.id,
                timestamp=event.timestamp,
                actor_user_id=event.actor_user_id,
                actor_username=event.actor_username,
                actor_role=event.actor_role,
                action=event.action,
                entity_type=event.entity_type,
                entity_id=event.entity_id,
                correlation_id=event.correlation_id,
                details_json=event.details_json
            )
            for event in events
        ]
        
        return AuditEventListResponse(
            items=items,
            page=page,
            page_size=page_size,
            total=total
        )
