"""Rules API router."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.common.pagination import PaginatedResponse
from app.database import get_db
from app.rules.models import DetectionRule
from app.rules.schemas import RuleDetailResponse, RuleListItem
from app.security.dependencies import get_current_user
from app.security.models import User

router = APIRouter()


@router.get("", response_model=PaginatedResponse[RuleListItem])
def list_rules(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    sort_by: str = Query("rule_code", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List detection rules with pagination, filtering, and sorting.
    
    Requires authentication.
    """
    # Build base query
    query = db.query(DetectionRule)
    
    # Apply filters
    if is_active is not None:
        query = query.filter(DetectionRule.is_active == is_active)
    if severity:
        query = query.filter(DetectionRule.severity == severity)
    
    # Get total count
    total = query.count()
    
    # Apply sorting
    sort_column = getattr(DetectionRule, sort_by, DetectionRule.rule_code)
    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(sort_column)
    
    # Apply pagination
    offset = (page - 1) * page_size
    results = query.offset(offset).limit(page_size).all()
    
    # Convert to response models
    items = [
        RuleListItem(
            id=rule.id,
            rule_code=rule.rule_code,
            name=rule.name,
            severity=rule.severity,
            description=rule.description,
            is_active=rule.is_active,
            version=rule.version,
            created_at=rule.created_at,
            updated_at=rule.updated_at
        )
        for rule in results
    ]
    
    return PaginatedResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total
    )


@router.get("/{rule_code}", response_model=RuleDetailResponse)
def get_rule_detail(
    rule_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete rule detail including all versions.
    
    Requires authentication.
    """
    rule = (
        db.query(DetectionRule)
        .options(joinedload(DetectionRule.versions))
        .filter(DetectionRule.rule_code == rule_code)
        .first()
    )
    
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_code} not found"
        )
    
    return RuleDetailResponse(
        id=rule.id,
        rule_code=rule.rule_code,
        name=rule.name,
        severity=rule.severity,
        description=rule.description,
        is_active=rule.is_active,
        version=rule.version,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
        versions=[
            {
                "id": v.id,
                "rule_id": v.rule_id,
                "version_number": v.version_number,
                "parameters_json": v.parameters_json,
                "effective_from": v.effective_from
            }
            for v in rule.versions
        ]
    )
