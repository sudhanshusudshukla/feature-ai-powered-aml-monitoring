"""Security service for authentication and token management."""
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import jwt
import bcrypt
from sqlalchemy.orm import Session
from app.config import settings
from app.security.models import User, UserSession
from app.common.errors import AuthenticationError


class SecurityService:
    """Service for JWT token generation and user authentication."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate user with email and password.
        Raises AuthenticationError if credentials are invalid.
        """
        # Find user by email (using username field)
        user = self.db.query(User).filter(User.username == email, User.is_active == True).first()
        
        if not user:
            raise AuthenticationError("Invalid credentials")
        
        # Verify password with bcrypt
        # password_hash is already a string from the database, need to encode it to bytes
        try:
            if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                raise AuthenticationError("Invalid credentials")
        except ValueError:
            # Handle case where password_hash is invalid
            raise AuthenticationError("Invalid credentials")
        
        return user
    
    def generate_token(self, user: User) -> tuple[str, UserSession]:
        """
        Generate JWT token and create session record.
        Returns tuple of (token, session).
        """
        issued_at = datetime.utcnow()
        expires_at = issued_at + timedelta(minutes=settings.jwt_expiry_minutes)
        
        # Create JWT payload
        payload = {
            'sub': str(user.id),
            'username': user.username,
            'role': user.role,
            'iat': issued_at,
            'exp': expires_at,
        }
        
        # Generate token
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
        
        # Hash token for storage using SHA-256 (JWT tokens are too long for bcrypt)
        token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            token_hash=token_hash,
            issued_at=issued_at,
            expires_at=expires_at,
            last_activity_at=issued_at,
        )
        self.db.add(session)
        self.db.commit()
        
        return token, session
    
    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify JWT token and return payload.
        Returns None if token is invalid or expired.
        """
        try:
            payload = jwt.decode(
                token,
                settings.secret_key,
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")
