"""Case management API endpoints."""
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.case_management.models import AMLCase, CaseAlertLink
from app.case_management.schemas import (
    CaseAssignRequest,
    CaseCreateRequest,
    CaseDecisionRequest,
    CaseDetailResponse,
    CaseListItem,
)
from app.case_management.service import CaseManagementService
from app.common.errors import (
    AuthorizationError,
    DomainValidationError,
    InvalidStateTransitionError,
    NotFoundError,
    OptimisticLockConflictError,
)
from app.common.pagination import PaginatedResponse
from app.customer.models import Customer
from app.database import get_db
from app.security.dependencies import get_current_user
from app.security.models import User

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[CaseListItem],
    summary="List cases"
)
def list_cases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    state: Optional[str] = Query(None, description="Filter by state"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assignee: Optional[int] = Query(None, description="Filter by assignee user ID"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Annotated[Session, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None
) -> PaginatedResponse[CaseListItem]:
    """
    List cases with pagination, filtering, and sorting.
    
    Requires authentication.
    """
    # Build base query with alert count
    query = (
        db.query(
            AMLCase.id,
            AMLCase.case_number,
            AMLCase.title,
            AMLCase.customer_id,
            Customer.full_name.label("customer_name"),
            AMLCase.state,
            AMLCase.priority,
            AMLCase.created_by_user_id,
            AMLCase.assigned_to_user_id,
            AMLCase.created_at,
            AMLCase.updated_at,
            func.count(CaseAlertLink.alert_id).label("alert_count")
        )
        .join(Customer, AMLCase.customer_id == Customer.id)
        .outerjoin(CaseAlertLink, AMLCase.id == CaseAlertLink.case_id)
        .group_by(
            AMLCase.id,
            AMLCase.case_number,
            AMLCase.title,
            AMLCase.customer_id,
            Customer.full_name,
            AMLCase.state,
            AMLCase.priority,
            AMLCase.created_by_user_id,
            AMLCase.assigned_to_user_id,
            AMLCase.created_at,
            AMLCase.updated_at
        )
    )
    
    # Apply filters
    if state:
        query = query.filter(AMLCase.state == state)
    if priority:
        query = query.filter(AMLCase.priority == priority)
    if assignee:
        query = query.filter(AMLCase.assigned_to_user_id == assignee)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(AMLCase, sort_by, AMLCase.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Apply pagination
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()
    
    # Convert to response models
    items = [
        CaseListItem(
            id=row.id,
            case_number=row.case_number,
            title=row.title,
            customer_id=row.customer_id,
            customer_name=row.customer_name,
            state=row.state,
            priority=row.priority,
            created_by_user_id=row.created_by_user_id,
            assigned_to_user_id=row.assigned_to_user_id,
            created_at=row.created_at,
            updated_at=row.updated_at,
            alert_count=row.alert_count
        )
        for row in results
    ]
    
    return PaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total
    )


@router.post(
    "",
    response_model=CaseDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create case from alerts"
)
def create_case(
    request: CaseCreateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> CaseDetailResponse:
    """
    Create a new case from one or more alerts.
    
    - Validates that all alerts exist and are eligible
    - Links alerts to the case
    - Initializes case in OPEN state
    - Records audit event
    
    Returns HTTP 201 with case detail on success.
    Returns HTTP 404 if alerts not found.
    Returns HTTP 409 if alerts already linked to other cases.
    """
    service = CaseManagementService(db)
    
    try:
        return service.create_case(
            title=request.title,
            alert_ids=request.alert_ids,
            actor_user=current_user
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except DomainValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.detail or str(e)
        )


@router.get(
    "/{case_id}",
    response_model=CaseDetailResponse,
    summary="Get case detail"
)
def get_case_detail(
    case_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> CaseDetailResponse:
    """
    Get complete case detail including linked alerts, notes, decisions,
    information requests, and permitted actions for the current user.
    
    Returns HTTP 200 with case detail on success.
    Returns HTTP 404 if case not found.
    """
    service = CaseManagementService(db)
    
    try:
        return service.get_case_detail(case_id, current_user)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post(
    "/{case_id}/assign",
    response_model=CaseDetailResponse,
    summary="Assign case to user"
)
def assign_case(
    case_id: int,
    request: CaseAssignRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> CaseDetailResponse:
    """
    Assign or reassign a case to a user.
    
    - Records previous and new assignee in audit trail
    - Uses optimistic locking for concurrency control
    
    Returns HTTP 200 with updated case detail on success.
    Returns HTTP 404 if case or user not found.
    Returns HTTP 409 if version conflict.
    """
    service = CaseManagementService(db)
    
    try:
        return service.assign_case(
            case_id=case_id,
            assigned_to_user_id=request.assigned_to_user_id,
            expected_version=request.expected_version,
            actor_user=current_user
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except OptimisticLockConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )


@router.post(
    "/{case_id}/decision",
    response_model=CaseDetailResponse,
    summary="Record case decision"
)
def record_decision(
    case_id: int,
    request: CaseDecisionRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> CaseDetailResponse:
    """
    Record a case decision (APPROVE, REJECT, ESCALATE, etc.).
    
    - Enforces separation of duties: creator cannot decide own case
    - Validates state transition
    - Records decision and updates case state
    - Creates audit trail
    
    Returns HTTP 200 with updated case detail on success.
    Returns HTTP 403 if creator tries to decide own case.
    Returns HTTP 404 if case not found.
    Returns HTTP 409 if state transition invalid or version conflict.
    """
    service = CaseManagementService(db)
    
    try:
        return service.record_decision(
            case_id=case_id,
            decision=request.decision,
            expected_version=request.expected_version,
            actor_user=current_user,
            reason=request.reason,
            comments=request.comments
        )
    except AuthorizationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.detail or str(e)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except (InvalidStateTransitionError, OptimisticLockConflictError, DomainValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
