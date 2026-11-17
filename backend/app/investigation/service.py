"""Investigation service for case workflow operations."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.correlation import get_correlation_id
from app.common.enums import InformationRequestStatus
from app.common.errors import DomainValidationError, NotFoundError
from app.investigation.repository import InvestigationRepository
from app.investigation.schemas import (
    CaseNoteResponse,
    InformationRequestResponse,
    InformationResponseResponse,
)
from app.security.models import User


class InvestigationService:
    """Service for investigation workflow operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = InvestigationRepository(db)
        self.audit_service = AuditService(db)
    
    def add_note(
        self,
        case_id: int,
        note_text: str,
        actor_user: User
    ) -> CaseNoteResponse:
        """
        Add a note to a case.
        
        Args:
            case_id: Case ID
            note_text: Note content
            actor_user: User creating the note
        
        Returns:
            Created note response
        """
        now = datetime.utcnow()
        
        note = self.repository.add_note(
            case_id=case_id,
            note_text=note_text,
            created_by_user_id=actor_user.id,
            created_at=now
        )
        
        # Record audit event
        correlation_id = get_correlation_id()
        self.audit_service.record_event(
            action="CASE_NOTE_ADDED",
            entity_type="case",
            entity_id=case_id,
            correlation_id=correlation_id,
            details={
                "note_id": note.id,
                "note_length": len(note_text),
            },
            actor_user_id=actor_user.id,
            actor_username=actor_user.username,
            actor_role=actor_user.role
        )
        
        self.db.commit()
        
        return CaseNoteResponse.model_validate(note)
    
    def request_information(
        self,
        case_id: int,
        requested_what: str,
        reason: str,
        due_date: datetime,
        actor_user: User
    ) -> InformationRequestResponse:
        """
        Create an information request for a case.
        
        Args:
            case_id: Case ID
            requested_what: What information is requested
            reason: Why it's needed
            due_date: When it's due
            actor_user: User making the request
        
        Returns:
            Created information request response
        """
        from app.case_management.repository import CaseRepository
        from app.case_management.state_machine import CaseStateMachine
        
        now = datetime.utcnow()
        
        # Get the case and transition its state
        case_repo = CaseRepository(self.db)
        case = case_repo.get_by_id(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")
        
        # Transition case state to INFORMATION_REQUESTED using the state machine
        state_machine = CaseStateMachine()
        new_state = state_machine.transition(case.state, "REQUEST_INFO")
        case.state = new_state
        case.version += 1
        case.updated_at = now
        
        # Create the information request
        request = self.repository.create_information_request(
            case_id=case_id,
            requested_what=requested_what,
            reason=reason,
            due_date=due_date,
            requested_by_user_id=actor_user.id,
            created_at=now
        )
        
        # Record audit event
        correlation_id = get_correlation_id()
        self.audit_service.record_event(
            action="INFORMATION_REQUESTED",
            entity_type="case",
            entity_id=case_id,
            correlation_id=correlation_id,
            details={
                "request_id": request.id,
                "requested_what": requested_what,
                "due_date": due_date.isoformat(),
            },
            actor_user_id=actor_user.id,
            actor_username=actor_user.username,
            actor_role=actor_user.role
        )
        
        self.db.commit()
        
        return InformationRequestResponse.model_validate(request)
    
    def record_response(
        self,
        request_id: int,
        response_text: str,
        actor_user: User
    ) -> InformationResponseResponse:
        """
        Record a response to an information request.
        
        Args:
            request_id: Information request ID
            response_text: Response content
            actor_user: User providing response
        
        Returns:
            Created response response
        
        Raises:
            NotFoundError: If request not found
            DomainValidationError: If request already has response or is cancelled
        """
        # Get the request
        request = self.repository.get_information_request(request_id)
        if not request:
            raise NotFoundError(f"Information request {request_id} not found")
        
        # Validate request is open
        if request.status != InformationRequestStatus.OPEN.value:
            raise DomainValidationError(
                f"Cannot respond to information request with status {request.status}",
                detail="INVALID_REQUEST_STATUS"
            )
        
        # Check if response already exists
        if request.response is not None:
            raise DomainValidationError(
                "Information request already has a response",
                detail="RESPONSE_ALREADY_EXISTS"
            )
        
        now = datetime.utcnow()
        
        # Create response
        response = self.repository.record_information_response(
            information_request_id=request_id,
            response_text=response_text,
            responded_by_user_id=actor_user.id,
            responded_at=now
        )
        
        # Update request status
        self.repository.update_information_request_with_version(
            request_id=request_id,
            expected_version=request.version,
            updates={
                "status": InformationRequestStatus.RESPONDED.value,
                "updated_at": now
            }
        )
        
        # Record audit event
        correlation_id = get_correlation_id()
        self.audit_service.record_event(
            action="INFORMATION_RESPONSE_RECORDED",
            entity_type="case",
            entity_id=request.case_id,
            correlation_id=correlation_id,
            details={
                "request_id": request_id,
                "response_id": response.id,
                "response_length": len(response_text),
            },
            actor_user_id=actor_user.id,
            actor_username=actor_user.username,
            actor_role=actor_user.role
        )
        
        self.db.commit()
        
        return InformationResponseResponse.model_validate(response)
