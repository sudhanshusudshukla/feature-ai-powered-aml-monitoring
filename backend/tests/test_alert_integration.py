"""Integration tests for alert API endpoints."""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.alert.models import Alert
from app.transaction.models import Transaction
from app.customer.models import Customer, CustomerRiskProfile, Account
from app.common.enums import AlertPriority, AlertStatus, TransactionType, RiskLevel, AccountStatus


@pytest.fixture
def sample_alert(db_session: Session) -> Alert:
    """Create a sample alert with complete data for testing."""
    # Create customer
    customer = Customer(
        customer_number="CUS-TEST-001",
        full_name="Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
    )
    db_session.add(customer)
    db_session.flush()
    
    # Create risk profile
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level=RiskLevel.MEDIUM,
        base_score=50,
        last_reviewed_at=datetime.utcnow(),
        reviewed_by="system",
    )
    db_session.add(risk_profile)
    
    # Create account
    account = Account(
        account_number="ACC-TEST-001",
        customer_id=customer.id,
        status=AccountStatus.ACTIVE,
        opened_at=datetime.utcnow(),
        current_balance="10000.00",
        currency="USD",
    )
    db_session.add(account)
    db_session.flush()
    
    # Create transaction
    transaction = Transaction(
        transaction_reference="TXN-TEST-001",
        account_id=account.id,
        amount="5000.00",
        currency="USD",
        transaction_type=TransactionType.TRANSFER,
        origin_country="US",
        destination_country="CA",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-corr-id",
    )
    db_session.add(transaction)
    db_session.flush()
    
    # Create alert
    alert = Alert(
        alert_number="ALT-TEST-001",
        transaction_id=transaction.id,
        risk_score=65,
        priority=AlertPriority.HIGH,
        status=AlertStatus.NEW,
        priority_rationale="Priority HIGH: final score 65. Base score 60. Customer risk adjustment +5. Geography adjustment +0. Customer is rated MEDIUM risk."
    )
    db_session.add(alert)
    db_session.commit()
    
    return alert


def test_get_alert_detail_success(client: TestClient, auth_client: TestClient, sample_alert: Alert):
    """Test successful alert detail retrieval."""
    response = auth_client.get(f"/api/v1/alerts/{sample_alert.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == sample_alert.id
    assert data["alert_number"] == "ALT-TEST-001"
    assert data["risk_score"] == 65
    assert data["priority"] == "HIGH"
    assert data["status"] == "NEW"
    assert "transaction" in data
    assert "matched_rules" in data
    assert "customer_snapshot" in data


def test_get_alert_detail_not_found(auth_client: TestClient):
    """Test alert detail with non-existent ID returns 404."""
    response = auth_client.get("/api/v1/alerts/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_alert_detail_requires_auth(client: TestClient, sample_alert: Alert):
    """Test alert detail requires authentication."""
    response = client.get(f"/api/v1/alerts/{sample_alert.id}")
    assert response.status_code == 401
