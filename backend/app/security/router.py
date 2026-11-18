"""Security router for authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.schemas import LoginRequest, LoginResponse, UserResponse
from app.security.service import SecurityService
from app.common.errors import AuthenticationError


router = APIRouter(prefix="/v1/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse, status_code=200)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    
    POST /api/v1/auth/login
    Request body: {"email": "user@example.com", "password": "password"}
    Returns: {"access_token": "jwt_token", "token_type": "bearer", "user": {...}}
    """
    try:
        service = SecurityService(db)
        
        # Authenticate user
        user = service.authenticate_user(request.email, request.password)
        
        # Generate token
        token, _ = service.generate_token(user)
        
        # Return response
        return LoginResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse.model_validate(user)
        )
    
    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
