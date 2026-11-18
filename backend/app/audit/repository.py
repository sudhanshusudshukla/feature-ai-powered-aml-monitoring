"""Audit repository: insert-only persistence and filtered retrieval."""
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.audit.models import AuditEvent


class AuditRepository:
    """Repository for audit event persistence and retrieval."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def insert(self, event: AuditEvent) -> AuditEvent:
        """
        Insert a new audit event (insert-only, no updates allowed).
        Returns the persisted event.
        """
        self.db.add(event)
        self.db.flush()
        self.db.refresh(event)
        return event
    
    def list_events(
        self,
        entity_type: str | None = None,
        entity_id: int | None = None,
        actor_id: int | None = None,
        correlation_id: str | None = None,
        offset: int = 0,
        limit: int = 50
    ) -> tuple[list[AuditEvent], int]:
        """
        Retrieve audit events with optional filters.
        
        Returns:
            tuple: (list of events, total count)
        """
        query = self.db.query(AuditEvent)
        
        # Apply filters
        filters = []
        if entity_type is not None:
            filters.append(AuditEvent.entity_type == entity_type)
        if entity_id is not None:
            filters.append(AuditEvent.entity_id == entity_id)
        if actor_id is not None:
            filters.append(AuditEvent.actor_user_id == actor_id)
        if correlation_id is not None:
            filters.append(AuditEvent.correlation_id == correlation_id)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        events = query.order_by(AuditEvent.timestamp.desc()).offset(offset).limit(limit).all()
        
        return events, total
