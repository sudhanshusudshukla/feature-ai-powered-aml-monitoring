"""Integration tests for transaction API endpoints."""
from datetime import datetime
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.customer.models import Customer, Account, CustomerRiskProfile
from app.common.enums import AccountStatus, TransactionType


@pytest.fixture
def auth_token(client: TestClient, test_user):
    """Get authentication token for protected endpoints."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user.username,
            "password": "Officer-pass-1"
        }
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def customer(db_session: Session):
    """Create a test customer."""
    customer = Customer(
        customer_number="CUST100",
        full_name="Integration Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test"
    )
    db_session.add(customer)
    db_session.flush()
    
    # Add risk profile (required for screening context)
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level="MEDIUM",
        base_score=50,
        last_reviewed_at=datetime.utcnow()
    )
    db_session.add(risk_profile)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def account(db_session: Session, customer):
    """Create a test account."""
    account = Account(
        account_number="ACC100",
        customer_id=customer.id,
        status=AccountStatus.ACTIVE.value,
        opened_at=datetime.utcnow(),
        current_balance=Decimal("50000.00"),
        currency="INR"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


def test_create_transaction_success(client: TestClient, auth_token, account, all_rules_setup):
    """Test successful transaction creation via API."""
    payload = {
        "transaction_reference": "API-TXN-001",
        "account_id": account.id,
        "amount": "15000.00",
        "currency": "INR",
        "transaction_type": TransactionType.TRANSFER.value,
        "origin_country": "IN",
        "destination_country": "US",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post(
        "/api/v1/transactions/",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["id"] > 0
    assert data["transaction_reference"] == "API-TXN-001"
    assert data["account_id"] == account.id
    assert data["amount"] == "15000.00"
    assert data["currency"] == "INR"
    assert data["transaction_type"] == TransactionType.TRANSFER.value
    assert data["origin_country"] == "IN"
    assert data["destination_country"] == "US"
    assert data["matched_rules_count"] >= 0
    # Alert behavior depends on whether rules matched (e.g., dormancy spike on first txn)
    if data["matched_rules_count"] > 0:
        assert data["alert_raised"] is True
        assert data["alert_id"] is not None
    else:
        assert data["alert_raised"] is False
        assert data["alert_id"] is None
    assert "correlation_id" in data
    assert len(data["evaluation_results"]) == 8


def test_create_transaction_with_counterparty(client: TestClient, auth_token, account, all_rules_setup):
    """Test transaction creation with optional counterparty fields."""
    payload = {
        "transaction_reference": "API-TXN-002",
        "account_id": account.id,
        "amount": "8500.50",
        "currency": "INR",
        "transaction_type": TransactionType.PAYMENT.value,
        "origin_country": "IN",
        "destination_country": "GB",
        "counterparty_name": "XYZ Ltd",
        "counterparty_account": "GB789012",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post(
        "/api/v1/transactions/",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["transaction_reference"] == "API-TXN-002"


def test_create_transaction_missing_required_field(client: TestClient, auth_token, account):
    """Test transaction creation with missing required field."""
    payload = {
        "transaction_reference": "API-TXN-003",
        "account_id": account.id,
        # Missing amount
        "currency": "INR",
        "transaction_type": TransactionType.DEPOSIT.value,
        "origin_country": "IN",
        "destination_country": "IN",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post(
        "/api/v1/transactions/",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 422  # Validation error


def test_create_transaction_account_not_found(client: TestClient, auth_token):
    """Test transaction creation with non-existent account."""
    payload = {
        "transaction_reference": "API-TXN-004",
        "account_id": 99999,  # non-existent
        "amount": "5000.00",
        "currency": "INR",
        "transaction_type": TransactionType.WITHDRAWAL.value,
        "origin_country": "IN",
        "destination_country": "IN",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post(
        "/api/v1/transactions/",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404
    assert "Account not found" in response.json()["detail"]


def test_create_transaction_unauthorized(client: TestClient, account):
    """Test transaction creation without authentication."""
    payload = {
        "transaction_reference": "API-TXN-005",
        "account_id": account.id,
        "amount": "3000.00",
        "currency": "INR",
        "transaction_type": TransactionType.TRANSFER.value,
        "origin_country": "IN",
        "destination_country": "SG",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post(
        "/api/v1/transactions/",
        json=payload
    )
    
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_get_transaction_detail_success(client: TestClient, auth_token, account, all_rules_setup):
    """Test successful transaction detail retrieval via API."""
    # First create a transaction
    create_payload = {
        "transaction_reference": "API-TXN-006",
        "account_id": account.id,
        "amount": "12000.75",
        "currency": "INR",
        "transaction_type": TransactionType.TRANSFER.value,
        "origin_country": "IN",
        "destination_country": "AE",
        "counterparty_name": "Foreign Entity",
        "counterparty_account": "AE456789",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    create_response = client.post(
        "/api/v1/transactions/",
        json=create_payload,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert create_response.status_code == 201
    transaction_id = create_response.json()["id"]
    
    # Now retrieve it
    get_response = client.get(
        f"/api/v1/transactions/{transaction_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert get_response.status_code == 200
    data = get_response.json()
    
    assert data["id"] == transaction_id
    assert data["transaction_reference"] == "API-TXN-006"
    assert data["account_id"] == account.id
    assert data["amount"] == "12000.75"
    assert data["currency"] == "INR"
    assert data["transaction_type"] == TransactionType.TRANSFER.value
    assert data["origin_country"] == "IN"
    assert data["destination_country"] == "AE"
    assert data["counterparty_name"] == "Foreign Entity"
    assert data["counterparty_account"] == "AE456789"
    assert data["matched_rules_count"] >= 0
    # Alert behavior depends on whether rules matched (e.g., dormancy spike on first txn)
    if data["matched_rules_count"] > 0:
        assert data["alert_raised"] is True
        assert data["alert_id"] is not None
    else:
        assert data["alert_raised"] is False
        assert data["alert_id"] is None
    assert "correlation_id" in data
    assert len(data["evaluation_results"]) == 8


def test_get_transaction_detail_not_found(client: TestClient, auth_token):
    """Test transaction detail retrieval for non-existent transaction."""
    response = client.get(
        "/api/v1/transactions/99999",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 404
    assert "Transaction not found" in response.json()["detail"]


def test_get_transaction_detail_unauthorized(client: TestClient):
    """Test transaction detail retrieval without authentication."""
    response = client.get("/api/v1/transactions/1")
    
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]


def test_transaction_preserves_exact_amount(client: TestClient, auth_token, account, all_rules_setup):
    """Test that API preserves exact decimal amounts."""
    payload = {
        "transaction_reference": "API-TXN-007",
        "account_id": account.id,
        "amount": "9999.99",
        "currency": "INR",
        "transaction_type": TransactionType.PAYMENT.value,
        "origin_country": "IN",
        "destination_country": "IN",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post(
        "/api/v1/transactions/",
        json=payload,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify exact preservation
    assert data["amount"] == "9999.99"
    assert data["currency"] == "INR"
