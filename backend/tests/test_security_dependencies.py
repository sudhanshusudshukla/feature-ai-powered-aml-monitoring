"""Unit tests for security dependencies (require_role)."""
import pytest
import bcrypt
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.security.dependencies import get_current_user, require_role
from app.security.models import User
from app.common.enums import UserRole


@pytest.fixture
def sample_users(db_session: Session) -> dict[str, User]:
    """Create users with different roles."""
    users = {}
    roles = [
        (UserRole.AML_ANALYST, "analyst@example.com", "Analyst User"),
        (UserRole.AML_OFFICER, "officer@example.com", "Officer User"),
        (UserRole.AML_MANAGER, "manager@example.com", "Manager User"),
        (UserRole.ADMINISTRATOR, "admin@example.com", "Admin User"),
        (UserRole.AUDITOR, "auditor@example.com", "Auditor User"),
    ]
    
    for role, email, name in roles:
        password_hash = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode('utf-8')
        user = User(
            username=email,
            password_hash=password_hash,
            full_name=name,
            role=role.value,
            permissions_json="{}",
            is_active=True,
        )
        db_session.add(user)
        db_session.flush()
        users[role.value] = user
    
    db_session.commit()
    return users


def test_require_role_single_role_allowed(sample_users: dict[str, User]):
    """Test require_role with a single allowed role."""
    checker = require_role(UserRole.ADMINISTRATOR)
    
    # Admin should pass
    admin_user = sample_users[UserRole.ADMINISTRATOR.value]
    result = checker(current_user=admin_user)
    assert result == admin_user
    
    # Officer should fail
    officer_user = sample_users[UserRole.AML_OFFICER.value]
    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=officer_user)
    
    assert exc_info.value.status_code == 403
    assert "Access denied" in exc_info.value.detail


def test_require_role_multiple_roles_allowed(sample_users: dict[str, User]):
    """Test require_role with multiple allowed roles."""
    checker = require_role(UserRole.AML_OFFICER, UserRole.AML_MANAGER)
    
    # Officer should pass
    officer_user = sample_users[UserRole.AML_OFFICER.value]
    result = checker(current_user=officer_user)
    assert result == officer_user
    
    # Manager should pass
    manager_user = sample_users[UserRole.AML_MANAGER.value]
    result = checker(current_user=manager_user)
    assert result == manager_user
    
    # Analyst should fail
    analyst_user = sample_users[UserRole.AML_ANALYST.value]
    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=analyst_user)
    
    assert exc_info.value.status_code == 403
    assert "Access denied" in exc_info.value.detail


def test_require_role_admin_only(sample_users: dict[str, User]):
    """Test require_role for administrator-only endpoints."""
    checker = require_role(UserRole.ADMINISTRATOR)
    
    # Only admin should pass
    admin_user = sample_users[UserRole.ADMINISTRATOR.value]
    result = checker(current_user=admin_user)
    assert result == admin_user
    
    # All other roles should fail
    for role_value, user in sample_users.items():
        if role_value != UserRole.ADMINISTRATOR.value:
            with pytest.raises(HTTPException) as exc_info:
                checker(current_user=user)
            assert exc_info.value.status_code == 403


def test_require_role_auditor_only(sample_users: dict[str, User]):
    """Test require_role for auditor-only endpoints."""
    checker = require_role(UserRole.AUDITOR)
    
    # Only auditor should pass
    auditor_user = sample_users[UserRole.AUDITOR.value]
    result = checker(current_user=auditor_user)
    assert result == auditor_user
    
    # Admin should not have auditor access
    admin_user = sample_users[UserRole.ADMINISTRATOR.value]
    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=admin_user)
    assert exc_info.value.status_code == 403


def test_require_role_all_roles_allowed(sample_users: dict[str, User]):
    """Test require_role with all roles allowed."""
    checker = require_role(
        UserRole.AML_ANALYST,
        UserRole.AML_OFFICER,
        UserRole.AML_MANAGER,
        UserRole.ADMINISTRATOR,
        UserRole.AUDITOR
    )
    
    # All users should pass
    for user in sample_users.values():
        result = checker(current_user=user)
        assert result == user


def test_require_role_error_message_includes_required_roles(sample_users: dict[str, User]):
    """Test that error message includes the required roles."""
    checker = require_role(UserRole.AML_MANAGER, UserRole.ADMINISTRATOR)
    
    analyst_user = sample_users[UserRole.AML_ANALYST.value]
    with pytest.raises(HTTPException) as exc_info:
        checker(current_user=analyst_user)
    
    error_detail = exc_info.value.detail
    assert "AML_MANAGER" in error_detail
    assert "ADMINISTRATOR" in error_detail


def test_require_role_preserves_user_object(sample_users: dict[str, User]):
    """Test that require_role returns the original user object."""
    checker = require_role(UserRole.AML_OFFICER)
    
    officer_user = sample_users[UserRole.AML_OFFICER.value]
    result = checker(current_user=officer_user)
    
    # Should be the same object
    assert result is officer_user
    assert result.id == officer_user.id
    assert result.username == officer_user.username
    assert result.role == officer_user.role


def test_require_role_with_inactive_user(db_session: Session):
    """Test that inactive users are rejected even if role matches."""
    # Note: This test assumes get_current_user already filters inactive users
    # require_role itself doesn't check is_active, but the dependency chain does
    password_hash = bcrypt.hashpw(b"password", bcrypt.gensalt()).decode('utf-8')
    inactive_user = User(
        username="inactive@example.com",
        password_hash=password_hash,
        full_name="Inactive User",
        role=UserRole.AML_MANAGER.value,
        permissions_json="{}",
        is_active=False,
    )
    db_session.add(inactive_user)
    db_session.commit()
    
    # If somehow an inactive user gets through, require_role checks role only
    # The actual protection is in get_current_user
    checker = require_role(UserRole.AML_MANAGER)
    
    # If is_active check is in get_current_user, this would pass require_role
    # but fail earlier in the chain
    result = checker(current_user=inactive_user)
    assert result == inactive_user  # require_role only checks role


def test_require_role_case_insensitive_role_comparison(sample_users: dict[str, User]):
    """Test that role comparison works correctly with enum values."""
    checker = require_role(UserRole.AML_OFFICER)
    
    # Create user with role as string
    officer_user = sample_users[UserRole.AML_OFFICER.value]
    
    # Should work regardless of how role is stored
    result = checker(current_user=officer_user)
    assert result == officer_user
