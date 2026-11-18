"""Admin API router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.admin.schemas import UserListItem
from app.common.enums import UserRole
from app.common.pagination import PaginatedResponse
from app.database import get_db
from app.security.dependencies import require_role
from app.security.models import User

router = APIRouter()


@router.get(
    "/users",
    response_model=PaginatedResponse[UserListItem],
    dependencies=[Depends(require_role(UserRole.ADMINISTRATOR))]
)
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db)
):
    """
    List users with pagination.
    
    Requires ADMINISTRATOR role.
    """
    # Build base query
    query = db.query(User)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(User, sort_by, User.created_at)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Apply pagination
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()
    
    # Convert to response models
    items = [
        UserListItem(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at
        )
        for user in results
    ]
    
    return PaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total
    )
