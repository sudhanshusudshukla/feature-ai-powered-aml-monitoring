"""Integration tests for GET /api/v1/transactions list endpoint."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.transaction.models import Transaction
from app.alert.models import Alert
from app.customer.models import Customer, Account
from app.common.enums import TransactionType, AccountStatus, AlertStatus, AlertPriority


@pytest.fixture
def sample_transactions_dataset(db_session: Session) -> list[Transaction]:
    """Create a diverse set of transactions for list testing."""
    # Create customer
    customer = Customer(
        customer_number="CUS-TXN-001",
        full_name="Test Customer Txns",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
    )
    db_session.add(customer)
    db_session.flush()
    
    # Create account
    account = Account(
        account_number="ACC-TXN-001",
        customer_id=customer.id,
        status=AccountStatus.ACTIVE,
        opened_at=datetime.utcnow(),
        current_balance="100000.00",
        currency="USD",
    )
    db_session.add(account)
    db_session.flush()
    
    # Create diverse transactions
    transactions = []
    now = datetime.utcnow()
    
    tx_types = [TransactionType.TRANSFER, TransactionType.DEPOSIT, TransactionType.WITHDRAWAL]
    
    for i in range(20):
        transaction = Transaction(
            transaction_reference=f"TXN-TST-{i:04d}",
            account_id=account.id,
            amount=str(500 + (i * 250)),  # Range from 500 to 5250
            currency="USD",
            transaction_type=tx_types[i % len(tx_types)],
            origin_country="US" if i % 2 == 0 else "GB",
            destination_country="CA" if i % 2 == 0 else "FR",
            transaction_timestamp=now - timedelta(hours=i),
            correlation_id=f"test-corr-txn-{i}",
        )
        db_session.add(transaction)
        db_session.flush()
        
        # Create alert for some transactions
        if i % 4 == 0:
            alert = Alert(
                alert_number=f"ALT-TXN-{i:04d}",
                transaction_id=transaction.id,
                risk_score=50 + i,
                priority=AlertPriority.MEDIUM,
                status=AlertStatus.NEW,
                priority_rationale=f"Test alert for txn {i}",
            )
            db_session.add(alert)
            transaction.alert_id = alert.id
        
        transactions.append(transaction)
    
    db_session.commit()
    return transactions


def test_list_transactions_requires_auth(client: TestClient):
    """Test that list transactions requires authentication."""
    response = client.get("/api/v1/transactions")
    assert response.status_code == 401


def test_list_transactions_success(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test successful transaction list retrieval."""
    response = auth_client.get("/api/v1/transactions")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total" in data
    
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total"] == 20
    assert len(data["items"]) == 20


def test_list_transactions_pagination(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test transaction list pagination."""
    # Page 1 with 10 items
    response = auth_client.get("/api/v1/transactions?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["page"] == 1
    assert data["total"] == 20
    
    # Page 2 with 10 items
    response = auth_client.get("/api/v1/transactions?page=2&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["page"] == 2


def test_list_transactions_filter_by_type(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test filtering transactions by type."""
    response = auth_client.get("/api/v1/transactions?transaction_type=TRANSFER")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items are transfers
    for item in data["items"]:
        assert item["transaction_type"] == "TRANSFER"


def test_list_transactions_filter_by_outcome_alert_raised(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test filtering transactions by outcome: alert_raised."""
    response = auth_client.get("/api/v1/transactions?outcome=alert_raised")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items have alerts
    for item in data["items"]:
        assert item["alert_raised"] is True
        assert item["alert_id"] is not None
    
    assert data["total"] == 5  # Every 4th transaction has an alert


def test_list_transactions_filter_by_outcome_no_alert(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test filtering transactions by outcome: no_alert."""
    response = auth_client.get("/api/v1/transactions?outcome=no_alert")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items have no alerts
    for item in data["items"]:
        assert item["alert_raised"] is False
        assert item["alert_id"] is None
    
    assert data["total"] == 15


def test_list_transactions_filter_by_amount_range(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test filtering transactions by amount range."""
    response = auth_client.get("/api/v1/transactions?amount_min=1000&amount_max=3000")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items are within range
    for item in data["items"]:
        amount = Decimal(item["amount"])
        assert Decimal("1000") <= amount <= Decimal("3000")


def test_list_transactions_filter_by_amount_min_only(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test filtering transactions by minimum amount only."""
    response = auth_client.get("/api/v1/transactions?amount_min=4000")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items are above minimum
    for item in data["items"]:
        amount = Decimal(item["amount"])
        assert amount >= Decimal("4000")


def test_list_transactions_filter_by_date_range(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test filtering transactions by date range."""
    now = datetime.utcnow()
    date_from = (now - timedelta(hours=10)).isoformat()
    date_to = now.isoformat()
    
    response = auth_client.get(f"/api/v1/transactions?date_from={date_from}&date_to={date_to}")
    assert response.status_code == 200
    data = response.json()
    
    # Should return transactions from last 10 hours (may be 10 or 11 depending on microsecond precision)
    assert data["total"] >= 10 and data["total"] <= 11


def test_list_transactions_sort_by_timestamp_desc(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test sorting transactions by timestamp descending (default)."""
    response = auth_client.get("/api/v1/transactions?sort_by=timestamp&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    
    # Check items are sorted by timestamp descending
    items = data["items"]
    for i in range(len(items) - 1):
        assert items[i]["timestamp"] >= items[i + 1]["timestamp"]


def test_list_transactions_sort_by_amount_asc(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test sorting transactions by amount ascending."""
    response = auth_client.get("/api/v1/transactions?sort_by=amount&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    
    # Check items are sorted by amount ascending
    items = data["items"]
    for i in range(len(items) - 1):
        assert Decimal(items[i]["amount"]) <= Decimal(items[i + 1]["amount"])


def test_list_transactions_multiple_filters(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test combining multiple filters."""
    response = auth_client.get("/api/v1/transactions?transaction_type=TRANSFER&outcome=alert_raised")
    assert response.status_code == 200
    data = response.json()
    
    # Check all items match both filters
    for item in data["items"]:
        assert item["transaction_type"] == "TRANSFER"
        assert item["alert_raised"] is True


def test_list_transactions_response_structure(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test the structure of transaction list items."""
    response = auth_client.get("/api/v1/transactions?page_size=1")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["items"]) == 1
    item = data["items"][0]
    
    # Check all expected fields are present
    assert "id" in item
    assert "transaction_reference" in item
    assert "account_id" in item
    assert "customer_name" in item
    assert "amount" in item
    assert "currency" in item
    assert "transaction_type" in item
    assert "origin_country" in item
    assert "destination_country" in item
    assert "timestamp" in item
    assert "matched_rules_count" in item
    assert "alert_raised" in item
    assert "alert_id" in item


def test_list_transactions_empty_results(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test filtering with no matching results."""
    response = auth_client.get("/api/v1/transactions?amount_min=100000")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_list_transactions_invalid_page(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test with invalid page number."""
    response = auth_client.get("/api/v1/transactions?page=0")
    assert response.status_code == 422  # Validation error


def test_list_transactions_invalid_page_size(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test with page size exceeding maximum."""
    response = auth_client.get("/api/v1/transactions?page_size=150")
    assert response.status_code == 422  # Exceeds max of 100


def test_list_transactions_page_beyond_results(auth_client: TestClient, sample_transactions_dataset: list[Transaction]):
    """Test requesting page beyond available results."""
    response = auth_client.get("/api/v1/transactions?page=10&page_size=20")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 20
    assert len(data["items"]) == 0  # No items on this page
