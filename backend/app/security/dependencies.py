"""Security dependencies for route protection."""
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.common.errors import AuthenticationError
from app.database import get_db
from app.security.models import User
from app.security.service import SecurityService


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and verify JWT from Authorization header.
    Returns authenticated user.
    Raises 401 if missing or invalid.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Parse Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    token = parts[1]
    
    # Verify token
    security_service = SecurityService(db)
    try:
        payload = security_service.verify_token(token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    
    # Load user from payload
    user_id = int(payload.get('sub'))
    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user
