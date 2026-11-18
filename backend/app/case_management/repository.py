"""Case management repository for persistence operations."""
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.alert.models import Alert
from app.case_management.models import AMLCase, CaseAlertLink, CaseDecision, CaseNote
from app.common.errors import NotFoundError, OptimisticLockConflictError
from app.investigation.models import InformationRequest


class CaseRepository:
    """Repository for case persistence operations with optimistic locking."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, case: AMLCase) -> AMLCase:
        """Create a new case."""
        self.db.add(case)
        self.db.flush()
        return case
    
    def get_by_id(self, case_id: int, eager_load: bool = False) -> AMLCase | None:
        """
        Get case by ID.
        
        Args:
            case_id: Case ID
            eager_load: Whether to eager load relationships
        
        Returns:
            Case entity or None if not found
        """
        query = self.db.query(AMLCase).filter(AMLCase.id == case_id)
        
        if eager_load:
            query = query.options(
                joinedload(AMLCase.alert_links),
                joinedload(AMLCase.notes),
                joinedload(AMLCase.decisions)
            )
        
        return query.first()
    
    def update_with_version(
        self,
        case_id: int,
        expected_version: int,
        updates: dict
    ) -> AMLCase:
        """
        Update case with optimistic locking.
        
        Args:
            case_id: Case ID
            expected_version: Expected version for concurrency control
            updates: Dictionary of fields to update
        
        Returns:
            Updated case entity
        
        Raises:
            OptimisticLockConflictError: If version mismatch
            NotFoundError: If case not found
        """
        # Build update dictionary with version increment
        update_dict = {**updates, "version": expected_version + 1}
        
        result = self.db.query(AMLCase).filter(
            AMLCase.id == case_id,
            AMLCase.version == expected_version
        ).update(update_dict)
        
        if result == 0:
            # Check if case exists at all
            exists = self.db.query(AMLCase.id).filter(AMLCase.id == case_id).first()
            if not exists:
                raise NotFoundError(f"Case {case_id} not found")
            raise OptimisticLockConflictError(f"Case {case_id} version conflict")
        
        self.db.flush()
        
        # Reload and return updated case
        case = self.get_by_id(case_id, eager_load=True)
        if not case:
            raise NotFoundError(f"Case {case_id} not found after update")
        
        return case
    
    def generate_case_number(self) -> str:
        """Generate a unique case number."""
        # Get max case ID to generate sequential number
        max_id = self.db.query(AMLCase.id).order_by(AMLCase.id.desc()).first()
        next_id = (max_id[0] + 1) if max_id else 1
        return f"CASE-{next_id:06d}"
    
    def link_alerts(
        self,
        case_id: int,
        alert_ids: list[int],
        linked_by_user_id: int,
        linked_at: datetime
    ) -> list[CaseAlertLink]:
        """
        Create links between case and alerts.
        
        Args:
            case_id: Case ID
            alert_ids: List of alert IDs to link
            linked_by_user_id: User performing the link
            linked_at: Timestamp of link
        
        Returns:
            List of created link entities
        """
        links = []
        for alert_id in alert_ids:
            link = CaseAlertLink(
                case_id=case_id,
                alert_id=alert_id,
                linked_by_user_id=linked_by_user_id,
                linked_at=linked_at
            )
            self.db.add(link)
            links.append(link)
        
        self.db.flush()
        return links
    
    def add_note(
        self,
        case_id: int,
        note_text: str,
        created_by_user_id: int
    ) -> CaseNote:
        """Add a note to a case."""
        note = CaseNote(
            case_id=case_id,
            note_text=note_text,
            created_by_user_id=created_by_user_id,
            created_at=datetime.utcnow()
        )
        self.db.add(note)
        self.db.flush()
        return note
    
    def add_decision(
        self,
        case_id: int,
        decision: str,
        decided_by_user_id: int,
        reason: str | None = None,
        comments: str | None = None
    ) -> CaseDecision:
        """Add a decision record to a case."""
        decision_record = CaseDecision(
            case_id=case_id,
            decision=decision,
            reason=reason,
            comments=comments,
            decided_by_user_id=decided_by_user_id,
            decided_at=datetime.utcnow()
        )
        self.db.add(decision_record)
        self.db.flush()
        return decision_record
    
    def get_linked_alerts(self, case_id: int) -> list[Alert]:
        """Get all alerts linked to a case."""
        return (
            self.db.query(Alert)
            .join(CaseAlertLink, CaseAlertLink.alert_id == Alert.id)
            .filter(CaseAlertLink.case_id == case_id)
            .all()
        )
    
    def get_information_requests(self, case_id: int) -> list[InformationRequest]:
        """Get all information requests for a case."""
        return (
            self.db.query(InformationRequest)
            .filter(InformationRequest.case_id == case_id)
            .order_by(InformationRequest.created_at.desc())
            .all()
        )
    
    def is_alert_already_linked(self, alert_id: int) -> bool:
        """Check if an alert is already linked to any case."""
        link = (
            self.db.query(CaseAlertLink.id)
            .filter(CaseAlertLink.alert_id == alert_id)
            .first()
        )
        return link is not None
