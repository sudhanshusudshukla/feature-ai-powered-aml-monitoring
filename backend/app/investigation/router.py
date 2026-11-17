"""Investigation workflow API endpoints for case notes and information requests."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.errors import NotFoundError, DomainValidationError, InvalidStateTransitionError
from app.database import get_db
from app.investigation.schemas import (
    AddNoteRequest,
    AddNoteResponse,
    RequestInformationRequest,
    RequestInformationResponse,
    RecordResponseRequest,
    RecordResponseResponse,
)
from app.investigation.service import InvestigationService
from app.security.dependencies import get_current_user
from app.security.models import User

router = APIRouter()


@router.post(
    "/{case_id}/notes",
    response_model=AddNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add note to case"
)
def add_note(
    case_id: int,
    request: AddNoteRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> AddNoteResponse:
    """
    Add a note to a case.
    
    Notes are append-only and immutable. They provide a chronological record
    of investigation activity.
    
    Returns HTTP 201 with note details on success.
    Returns HTTP 404 if case not found.
    """
    service = InvestigationService(db)
    
    try:
        note = service.add_note(
            case_id=case_id,
            note_text=request.note_text,
            actor_user=current_user
        )
        return AddNoteResponse(
            id=note.id,
            case_id=note.case_id,
            note_text=note.note_text,
            created_by_user_id=note.created_by_user_id,
            created_at=note.created_at.isoformat()
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{case_id}/request-info",
    response_model=RequestInformationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Request information for case"
)
def request_information(
    case_id: int,
    request: RequestInformationRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> RequestInformationResponse:
    """
    Create an information request for a case.
    
    Information requests track required information during investigation.
    The case state is updated to INFORMATION_REQUESTED.
    
    Returns HTTP 201 with request details on success.
    Returns HTTP 404 if case not found.
    Returns HTTP 409 if case state doesn't allow information requests.
    """
    service = InvestigationService(db)
    
    try:
        info_request = service.request_information(
            case_id=case_id,
            requested_what=request.requested_what,
            reason=request.reason,
            due_date=request.due_date,
            actor_user=current_user
        )
        return RequestInformationResponse(
            id=info_request.id,
            case_id=info_request.case_id,
            requested_what=info_request.requested_what,
            reason=info_request.reason,
            due_date=info_request.due_date.isoformat(),
            status=info_request.status,
            requested_by_user_id=info_request.requested_by_user_id,
            created_at=info_request.created_at.isoformat()
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except (InvalidStateTransitionError, DomainValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post(
    "/{case_id}/information-requests/{request_id}/respond",
    response_model=RecordResponseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record response to information request"
)
def record_response(
    case_id: int,
    request_id: int,
    request: RecordResponseRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> RecordResponseResponse:
    """
    Record a response to an information request.
    
    Updates the request status to RESPONDED and creates an immutable response record.
    
    Returns HTTP 201 with response details on success.
    Returns HTTP 404 if request not found.
    Returns HTTP 409 if request already responded or cancelled.
    """
    service = InvestigationService(db)
    
    try:
        response = service.record_response(
            request_id=request_id,
            response_text=request.response_text,
            actor_user=current_user
        )
        return RecordResponseResponse(
            id=response.id,
            information_request_id=response.information_request_id,
            response_text=response.response_text,
            responded_by_user_id=response.responded_by_user_id,
            responded_at=response.responded_at.isoformat()
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
