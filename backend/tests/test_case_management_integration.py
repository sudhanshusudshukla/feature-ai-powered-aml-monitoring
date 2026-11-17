"""Integration tests for case management API endpoints."""
from datetime import datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.alert.models import Alert
from app.case_management.models import AMLCase
from app.common.enums import (
    AccountStatus,
    AlertPriority,
    AlertStatus,
    CaseState,
    RiskLevel,
    TransactionType,
    UserRole,
)
from app.customer.models import Account, Customer, CustomerRiskProfile
from app.security.models import User
from app.transaction.models import Transaction


def test_create_case_returns_201_with_case_detail(client: TestClient, db_session: Session, auth_client: TestClient):
    """Test POST /api/v1/cases/ creates case and returns 201."""
    # Setup: create alert
    customer = Customer(
        customer_number="C001",
        full_name="Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="TEST"
    )
    db_session.add(customer)
    db_session.commit()
    
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level=RiskLevel.MEDIUM.value,
        base_score=50,
        last_reviewed_at=datetime.utcnow(),
        reviewed_by="system"
    )
    db_session.add(risk_profile)
    
    account = Account(
        account_number="ACC001",
        customer_id=customer.id,
        status=AccountStatus.ACTIVE.value,
        opened_at=datetime.utcnow(),
        current_balance="1000.00",
        currency="INR"
    )
    db_session.add(account)
    db_session.flush()
    
    transaction = Transaction(
        transaction_reference="TXN001",
        account_id=account.id,
        amount="15000.00",
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="US",
        destination_country="IN",
        transaction_timestamp=datetime.utcnow(), correlation_id="test-corr-id"
    )
    db_session.add(transaction)
    db_session.flush()
    
    alert = Alert(
        alert_number="ALT-000001",
        transaction_id=transaction.id,
        risk_score=75,
        priority=AlertPriority.HIGH.value,
        status=AlertStatus.NEW.value,
        priority_rationale="High value transaction"
    )
    db_session.add(alert)
    db_session.commit()
    
    # Act
    response = auth_client.post(
        "/api/v1/cases/",
        json={
            "title": "Suspicious transfer",
            "alert_ids": [alert.id]
        }
    )
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["case_number"].startswith("CASE-")
    assert data["title"] == "Suspicious transfer"
    assert data["state"] == CaseState.OPEN.value
    assert data["priority"] == AlertPriority.HIGH.value
    assert len(data["linked_alerts"]) == 1
    assert data["linked_alerts"][0]["id"] == alert.id


def test_create_case_with_nonexistent_alert_returns_404(auth_client: TestClient):
    """Test creating case with nonexistent alert returns 404."""
    response = auth_client.post(
        "/api/v1/cases/",
        json={
            "title": "Invalid case",
            "alert_ids": [99999]
        }
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_case_with_already_linked_alert_returns_409(client: TestClient, db_session: Session, auth_client: TestClient):
    """Test creating case with already-linked alert returns 409."""
    # Setup: create alert and first case
    customer = Customer(
        customer_number="C001",
        full_name="Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="TEST"
    )
    db_session.add(customer)
    db_session.commit()
    
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level=RiskLevel.MEDIUM.value,
        base_score=50,
        last_reviewed_at=datetime.utcnow(),
        reviewed_by="system"
    )
    db_session.add(risk_profile)
    
    account = Account(
        account_number="ACC001",
        customer_id=customer.id,
        status=AccountStatus.ACTIVE.value,
        opened_at=datetime.utcnow(),
        current_balance="1000.00",
        currency="INR"
    )
    db_session.add(account)
    db_session.flush()
    
    transaction = Transaction(
        transaction_reference="TXN001",
        account_id=account.id,
        amount="15000.00",
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="US",
        destination_country="IN",
        transaction_timestamp=datetime.utcnow(), correlation_id="test-corr-id"
    )
    db_session.add(transaction)
    db_session.flush()
    
    alert = Alert(
        alert_number="ALT-000001",
        transaction_id=transaction.id,
        risk_score=75,
        priority=AlertPriority.HIGH.value,
        status=AlertStatus.NEW.value,
        priority_rationale="High value"
    )
    db_session.add(alert)
    db_session.commit()
    
    # Create first case
    auth_client.post(
        "/api/v1/cases/",
        json={
            "title": "First case",
            "alert_ids": [alert.id]
        }
    )
    
    # Act: try to create second case with same alert
    response = auth_client.post(
        "/api/v1/cases/",
        json={
            "title": "Second case",
            "alert_ids": [alert.id]
        }
    )
    
    # Assert
    assert response.status_code == 409


def test_get_case_detail_returns_200_with_complete_info(client: TestClient, db_session: Session, auth_client: TestClient, test_user):
    """Test GET /api/v1/cases/{id} returns complete case detail."""
    # Setup
    user = test_user
    
    customer = Customer(
        customer_number="C001",
        full_name="Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="TEST"
    )
    db_session.add(customer)
    db_session.commit()
    
    case = AMLCase(
        case_number="CASE-000001",
        title="Test case",
        customer_id=customer.id,
        state=CaseState.OPEN.value,
        priority=AlertPriority.HIGH.value,
        created_by_user_id=user.id
    )
    db_session.add(case)
    db_session.commit()
    
    # Act
    response = auth_client.get(f"/api/v1/cases/{case.id}")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == case.id
    assert data["case_number"] == "CASE-000001"
    assert data["title"] == "Test case"
    assert data["state"] == CaseState.OPEN.value
    assert "permitted_actions" in data
    assert isinstance(data["linked_alerts"], list)
    assert isinstance(data["notes"], list)
    assert isinstance(data["decisions"], list)


def test_get_nonexistent_case_returns_404(auth_client: TestClient):
    """Test getting nonexistent case returns 404."""
    response = auth_client.get("/api/v1/cases/99999")
    
    assert response.status_code == 404


def test_unauthenticated_request_returns_401(client: TestClient):
    """Test that unauthenticated request returns 401."""
    response = client.post(
        "/api/v1/cases/",
        json={"title": "Test", "alert_ids": [1]}
    )
    
    assert response.status_code == 401


def test_creator_attempting_decision_returns_403(client: TestClient, db_session: Session, test_user):
    """Test that case creator attempting decision returns 403."""
    # Setup: create officer user and case
    officer = test_user
    
    customer = Customer(
        customer_number="C001",
        full_name="Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="TEST"
    )
    db_session.add(customer)
    db_session.commit()
    
    case = AMLCase(
        case_number="CASE-000001",
        title="Test case",
        customer_id=customer.id,
        state=CaseState.PENDING_DECISION.value,
        priority=AlertPriority.HIGH.value,
        created_by_user_id=officer.id
    )
    db_session.add(case)
    db_session.commit()
    
    # Login as creator
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "officer@example.com",
            "password": "Officer-pass-1"
        }
    )
    
    # Attempt decision
    response = client.post(
        f"/api/v1/cases/{case.id}/decision",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
        json={
            "decision": "APPROVE",
            "expected_version": 1
        }
    )
    
    # Assert
    assert response.status_code == 403
    assert "creator" in response.json()["detail"].lower()


def test_assign_case_updates_assignment(client: TestClient, db_session: Session, auth_client: TestClient, test_user):
    """Test assigning case to user."""
    # Setup
    user = test_user
    
    assignee = User(
        username="assignee@example.com",
        full_name="Assignee User",
        role=UserRole.AML_ANALYST.value,
        is_active=True,
        password_hash="hashed",
        permissions_json="{}"
    )
    db_session.add(assignee)
    
    customer = Customer(
        customer_number="C001",
        full_name="Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="TEST"
    )
    db_session.add(customer)
    db_session.commit()
    
    case = AMLCase(
        case_number="CASE-000001",
        title="Test case",
        customer_id=customer.id,
        state=CaseState.OPEN.value,
        priority=AlertPriority.HIGH.value,
        created_by_user_id=user.id
    )
    db_session.add(case)
    db_session.commit()
    
    # Act
    response = auth_client.post(
        f"/api/v1/cases/{case.id}/assign",
        json={
            "assigned_to_user_id": assignee.id,
            "expected_version": 1
        }
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["assigned_to_user_id"] == assignee.id
    assert data["version"] == 2  # Version incremented


def test_record_decision_updates_state(client: TestClient, db_session: Session):
    """Test recording decision updates case state."""
    # Setup: create two officers (creator and decider)
    import bcrypt
    
    creator_password = "Creator-pass-1"
    creator_hash = bcrypt.hashpw(creator_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    creator = User(
        username="creator@example.com",
        full_name="Creator Officer",
        role=UserRole.AML_OFFICER.value,
        is_active=True,
        password_hash=creator_hash,
        permissions_json="{}"
    )
    db_session.add(creator)
    
    decider_password = "Decider-pass-1"
    decider_hash = bcrypt.hashpw(decider_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    decider = User(
        username="decider@example.com",
        full_name="Decider Officer",
        role=UserRole.AML_OFFICER.value,
        is_active=True,
        password_hash=decider_hash,
        permissions_json="{}"
    )
    db_session.add(decider)
    
    customer = Customer(
        customer_number="C001",
        full_name="Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="TEST"
    )
    db_session.add(customer)
    db_session.commit()
    
    case = AMLCase(
        case_number="CASE-000001",
        title="Test case",
        customer_id=customer.id,
        state=CaseState.PENDING_DECISION.value,
        priority=AlertPriority.HIGH.value,
        created_by_user_id=creator.id
    )
    db_session.add(case)
    db_session.commit()
    
    # Login as decider
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "decider@example.com",
            "password": "Decider-pass-1"
        }
    )
    
    # Act: record decision
    response = client.post(
        f"/api/v1/cases/{case.id}/decision",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
        json={
            "decision": "APPROVE",
            "reason": "Reviewed and approved",
            "expected_version": 1
        }
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == CaseState.APPROVED.value
    assert len(data["decisions"]) == 1
    assert data["decisions"][0]["decision"] == "APPROVE"


def test_invalid_state_transition_returns_409(client: TestClient, db_session: Session, auth_client: TestClient, test_user):
    """Test that invalid state transition returns 409."""
    # Setup: need two users for separation of duties
    import bcrypt
    
    creator = test_user
    
    decider_password = "Decider2-pass-1"
    decider_hash = bcrypt.hashpw(decider_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    decider = User(
        username="decider2@example.com",
        full_name="Decider Officer 2",
        role=UserRole.AML_OFFICER.value,
        is_active=True,
        password_hash=decider_hash,
        permissions_json="{}"
    )
    db_session.add(decider)
    
    customer = Customer(
        customer_number="C001",
        full_name="Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="TEST"
    )
    db_session.add(customer)
    db_session.commit()
    
    # Case in OPEN state
    case = AMLCase(
        case_number="CASE-000001",
        title="Test case",
        customer_id=customer.id,
        state=CaseState.OPEN.value,
        priority=AlertPriority.HIGH.value,
        created_by_user_id=creator.id
    )
    db_session.add(case)
    db_session.commit()
    
    # Login as decider (different from creator to avoid 403)
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "decider2@example.com",
            "password": "Decider2-pass-1"
        }
    )
    
    # Act: try invalid transition (APPROVE from OPEN)
    response = client.post(
        f"/api/v1/cases/{case.id}/decision",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
        json={
            "decision": "APPROVE",
            "expected_version": 1
        }
    )
    
    # Assert
    assert response.status_code == 409
