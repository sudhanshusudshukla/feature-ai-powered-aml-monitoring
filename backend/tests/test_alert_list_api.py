"""Integration tests for GET /api/v1/alerts list endpoint."""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.alert.models import Alert
from app.transaction.models import Transaction
from app.customer.models import Customer, Account
from app.common.enums import AlertPriority, AlertStatus, TransactionType, AccountStatus


@pytest.fixture
def sample_alerts_dataset(db_session: Session) -> list[Alert]:
    """Create a diverse set of alerts for list testing."""
    # Create customer
    customer = Customer(
        customer_number="CUS-LIST-001",
        full_name="Test Customer List",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
    )
    db_session.add(customer)
    db_session.flush()
    
    # Create account
    account = Account(
        account_number="ACC-LIST-001",
        customer_id=customer.id,
        status=AccountStatus.ACTIVE,
        opened_at=datetime.utcnow(),
        current_balance="10000.00",
        currency="USD",
    )
    db_session.add(account)
    db_session.flush()
    
    # Create transactions and alerts with variety
    alerts = []
    now = datetime.utcnow()
    
    priorities = [AlertPriority.LOW, AlertPriority.MEDIUM, AlertPriority.HIGH, AlertPriority.CRITICAL]
    statuses = [AlertStatus.NEW, AlertStatus.UNDER_REVIEW, AlertStatus.CLOSED]
    
    for i in range(15):
        transaction = Transaction(
            transaction_reference=f"TXN-LIST-{i:03d}",
            account_id=account.id,
            amount=str(1000 * (i + 1)),
            currency="USD",
            transaction_type=TransactionType.TRANSFER,
            origin_country="US",
            destination_country="CA",
            transaction_timestamp=now - timedelta(days=i),
            correlation_id=f"test-corr-{i}",
        )
        db_session.add(transaction)
        db_session.flush()
        
        alert = Alert(
            alert_number=f"ALT-LIST-{i:03d}",
            transaction_id=transaction.id,
            risk_score=30 + (i * 4),
            priority=priorities[i % len(priorities)],
            status=statuses[i % len(statuses)],
            priority_rationale=f"Test alert {i}",
            created_at=now - timedelta(days=i),
            assigned_to_user_id=1 if i % 3 == 0 else None
        )
        db_session.add(alert)
        alerts.append(alert)
    
    db_session.commit()
    return alerts


def test_list_alerts_requires_auth(client: TestClient):
    """Test that list alerts requires authentication."""
    response = client.get("/api/v1/alerts")
    assert response.status_code == 401


def test_list_alerts_success(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test successful alert list retrieval with default pagination."""
    response = auth_client.get("/api/v1/alerts")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total" in data
    
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total"] == 15
    assert len(data["items"]) == 15


def test_list_alerts_pagination(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test alert list pagination."""
    # Page 1 with 5 items
    response = auth_client.get("/api/v1/alerts?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 1
    assert data["total"] == 15
    
    # Page 2 with 5 items
    response = auth_client.get("/api/v1/alerts?page=2&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 2
    
    # Page 3 with 5 items
    response = auth_client.get("/api/v1/alerts?page=3&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 3


def test_list_alerts_filter_by_status(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test filtering alerts by status."""
    response = auth_client.get("/api/v1/alerts?status=NEW")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items have NEW status
    for item in data["items"]:
        assert item["status"] == "NEW"
    
    assert data["total"] == 5  # 15 alerts, every 3rd is NEW


def test_list_alerts_filter_by_priority(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test filtering alerts by priority."""
    response = auth_client.get("/api/v1/alerts?priority=HIGH")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items have HIGH priority
    for item in data["items"]:
        assert item["priority"] == "HIGH"


def test_list_alerts_filter_by_assignee(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test filtering alerts by assignee."""
    response = auth_client.get("/api/v1/alerts?assignee=1")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items are assigned to user 1
    for item in data["items"]:
        assert item["assigned_to_user_id"] == 1
    
    assert data["total"] == 5  # Every 3rd alert is assigned to user 1


def test_list_alerts_filter_by_date_range(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test filtering alerts by date range."""
    now = datetime.utcnow()
    date_from = (now - timedelta(days=5)).isoformat()
    date_to = now.isoformat()
    
    response = auth_client.get(f"/api/v1/alerts?date_from={date_from}&date_to={date_to}")
    assert response.status_code == 200
    data = response.json()
    
    # Should return alerts from last 5 days (days 0-4 created within range)
    assert data["total"] >= 5  # At least 5 alerts


def test_list_alerts_sort_by_created_at_desc(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test sorting alerts by created_at descending (default)."""
    response = auth_client.get("/api/v1/alerts?sort_by=created_at&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    
    # Check items are sorted by created_at descending
    items = data["items"]
    for i in range(len(items) - 1):
        assert items[i]["created_at"] >= items[i + 1]["created_at"]


def test_list_alerts_sort_by_risk_score_asc(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test sorting alerts by risk_score ascending."""
    response = auth_client.get("/api/v1/alerts?sort_by=risk_score&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    
    # Check items are sorted by risk_score ascending
    items = data["items"]
    for i in range(len(items) - 1):
        assert items[i]["risk_score"] <= items[i + 1]["risk_score"]


def test_list_alerts_multiple_filters(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test combining multiple filters."""
    response = auth_client.get("/api/v1/alerts?status=NEW&priority=HIGH")
    assert response.status_code == 200
    data = response.json()
    
    # Check all items match both filters
    for item in data["items"]:
        assert item["status"] == "NEW"
        assert item["priority"] == "HIGH"


def test_list_alerts_empty_results(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test filtering with no matching results."""
    response = auth_client.get("/api/v1/alerts?status=NONEXISTENT")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_list_alerts_response_structure(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test the structure of alert list items."""
    response = auth_client.get("/api/v1/alerts?page_size=1")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["items"]) == 1
    item = data["items"][0]
    
    # Check all expected fields are present
    assert "id" in item
    assert "alert_number" in item
    assert "transaction_id" in item
    assert "risk_score" in item
    assert "priority" in item
    assert "status" in item
    assert "created_at" in item
    assert "assigned_to_user_id" in item
    assert "customer_name" in item
    assert "transaction_reference" in item
    assert "transaction_amount" in item
    assert "transaction_currency" in item


def test_list_alerts_invalid_page(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test with invalid page number."""
    response = auth_client.get("/api/v1/alerts?page=0")
    assert response.status_code == 422  # Validation error


def test_list_alerts_invalid_page_size(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test with invalid page size."""
    response = auth_client.get("/api/v1/alerts?page_size=200")
    assert response.status_code == 422  # Exceeds max of 100


def test_list_alerts_page_beyond_results(auth_client: TestClient, sample_alerts_dataset: list[Alert]):
    """Test requesting page beyond available results."""
    response = auth_client.get("/api/v1/alerts?page=100&page_size=20")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 15
    assert len(data["items"]) == 0  # No items on this page
