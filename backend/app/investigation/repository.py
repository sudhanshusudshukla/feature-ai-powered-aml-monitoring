"""Investigation repository for case workflow persistence."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.case_management.models import CaseNote
from app.common.enums import InformationRequestStatus
from app.common.errors import NotFoundError, OptimisticLockConflictError
from app.investigation.models import InformationRequest, InformationResponse


class InvestigationRepository:
    """Repository for investigation workflow persistence."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_note(
        self,
        case_id: int,
        note_text: str,
        created_by_user_id: int,
        created_at: datetime
    ) -> CaseNote:
        """
        Add a note to a case.
        
        Args:
            case_id: Case ID
            note_text: Note content
            created_by_user_id: User creating the note
            created_at: Creation timestamp
        
        Returns:
            Created note entity
        """
        note = CaseNote(
            case_id=case_id,
            note_text=note_text,
            created_by_user_id=created_by_user_id,
            created_at=created_at
        )
        self.db.add(note)
        self.db.flush()
        return note
    
    def create_information_request(
        self,
        case_id: int,
        requested_what: str,
        reason: str,
        due_date: datetime,
        requested_by_user_id: int,
        created_at: datetime
    ) -> InformationRequest:
        """
        Create an information request for a case.
        
        Args:
            case_id: Case ID
            requested_what: What information is requested
            reason: Why it's needed
            due_date: When it's due
            requested_by_user_id: User making the request
            created_at: Creation timestamp
        
        Returns:
            Created information request entity
        """
        request = InformationRequest(
            case_id=case_id,
            requested_what=requested_what,
            reason=reason,
            due_date=due_date,
            status=InformationRequestStatus.OPEN.value,
            requested_by_user_id=requested_by_user_id,
            created_at=created_at,
            updated_at=created_at,
            version=1
        )
        self.db.add(request)
        self.db.flush()
        return request
    
    def get_information_request(self, request_id: int) -> InformationRequest | None:
        """
        Get an information request by ID.
        
        Args:
            request_id: Request ID
        
        Returns:
            Information request or None
        """
        return self.db.query(InformationRequest).filter(
            InformationRequest.id == request_id
        ).first()
    
    def get_open_information_requests(self, case_id: int) -> list[InformationRequest]:
        """
        Get all open information requests for a case.
        
        Args:
            case_id: Case ID
        
        Returns:
            List of open information requests
        """
        return self.db.query(InformationRequest).filter(
            InformationRequest.case_id == case_id,
            InformationRequest.status == InformationRequestStatus.OPEN.value
        ).all()
    
    def update_information_request_with_version(
        self,
        request_id: int,
        expected_version: int,
        updates: dict
    ) -> InformationRequest:
        """
        Update an information request with optimistic locking.
        
        Args:
            request_id: Request ID
            expected_version: Expected current version
            updates: Fields to update
        
        Returns:
            Updated information request
        
        Raises:
            OptimisticLockConflictError: If version mismatch
            NotFoundError: If request not found
        """
        # Include version increment
        updates["version"] = InformationRequest.version + 1
        
        # Execute update with version check
        result = self.db.query(InformationRequest).filter(
            InformationRequest.id == request_id,
            InformationRequest.version == expected_version
        ).update(updates, synchronize_session=False)
        
        if result == 0:
            # Check if request exists
            existing = self.get_information_request(request_id)
            if not existing:
                raise NotFoundError(f"Information request {request_id} not found")
            raise OptimisticLockConflictError(
                f"Information request {request_id} was modified",
                detail="STALE_OBJECT"
            )
        
        # Reload and return
        self.db.expire_all()
        request = self.get_information_request(request_id)
        if not request:
            raise NotFoundError(f"Information request {request_id} not found after update")
        
        return request
    
    def record_information_response(
        self,
        information_request_id: int,
        response_text: str,
        responded_by_user_id: int,
        responded_at: datetime
    ) -> InformationResponse:
        """
        Record a response to an information request.
        
        Args:
            information_request_id: Request ID being responded to
            response_text: Response content
            responded_by_user_id: User providing response
            responded_at: Response timestamp
        
        Returns:
            Created response entity
        """
        response = InformationResponse(
            information_request_id=information_request_id,
            response_text=response_text,
            responded_by_user_id=responded_by_user_id,
            responded_at=responded_at
        )
        self.db.add(response)
        self.db.flush()
        return response
