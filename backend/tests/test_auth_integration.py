"""Integration tests for authentication endpoints."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.security.models import User
from app.security.service import SecurityService


def test_login_success(client: TestClient, db_session: Session, test_user: User):
    """Test successful login with valid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "officer@example.com",
            "password": "Officer-pass-1"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["username"] == "officer@example.com"
    assert data["user"]["role"] == "AML_OFFICER"


def test_login_invalid_email(client: TestClient):
    """Test login with non-existent email."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123"
        }
    )
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_invalid_password(client: TestClient, test_user: User):
    """Test login with incorrect password."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "officer@example.com",
            "password": "WrongPassword123"
        }
    )
    
    assert response.status_code == 401
    assert "Invalid credentials" in response.json()["detail"]


def test_login_inactive_user(client: TestClient, db_session: Session, test_user: User):
    """Test login with inactive user account."""
    # Mark user as inactive
    test_user.is_active = False
    db_session.commit()
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "officer@example.com",
            "password": "Officer-pass-1"
        }
    )
    
    assert response.status_code == 401


def test_login_creates_session(client: TestClient, db_session: Session, test_user: User):
    """Test that login creates a user session record."""
    from app.security.models import UserSession
    
    # Check no sessions exist initially
    initial_count = db_session.query(UserSession).count()
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "officer@example.com",
            "password": "Officer-pass-1"
        }
    )
    
    assert response.status_code == 200
    
    # Verify session was created
    final_count = db_session.query(UserSession).count()
    assert final_count == initial_count + 1
    
    # Verify session belongs to the user
    session = db_session.query(UserSession).filter(UserSession.user_id == test_user.id).first()
    assert session is not None
    assert session.user_id == test_user.id


def test_token_verification(client: TestClient, db_session: Session, test_user: User):
    """Test that generated token can be verified."""
    service = SecurityService(db_session)
    
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "officer@example.com",
            "password": "Officer-pass-1"
        }
    )
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Verify token
    payload = service.verify_token(token)
    assert payload is not None
    assert payload["username"] == "officer@example.com"
    assert payload["role"] == "AML_OFFICER"
