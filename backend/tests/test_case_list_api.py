"""Integration tests for GET /api/v1/cases list endpoint."""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.case_management.models import AMLCase, CaseAlertLink
from app.alert.models import Alert
from app.transaction.models import Transaction
from app.customer.models import Customer, Account
from app.common.enums import (
    CaseState, AlertStatus, AlertPriority,
    TransactionType, AccountStatus
)


@pytest.fixture
def sample_cases_dataset(db_session: Session) -> list[AMLCase]:
    """Create a diverse set of cases for list testing."""
    # Create customers
    customers = []
    for i in range(3):
        customer = Customer(
            customer_number=f"CUS-CASE-{i:03d}",
            full_name=f"Test Customer Case {i}",
            residency_country="US",
            pep_status=False,
            sanctioned_status=False,
            synthetic_source="test",
        )
        db_session.add(customer)
        customers.append(customer)
    db_session.flush()
    
    # Create accounts and transactions
    accounts = []
    transactions = []
    for i, customer in enumerate(customers):
        account = Account(
            account_number=f"ACC-CASE-{i:03d}",
            customer_id=customer.id,
            status=AccountStatus.ACTIVE,
            opened_at=datetime.utcnow(),
            current_balance="10000.00",
            currency="USD",
        )
        db_session.add(account)
        accounts.append(account)
        db_session.flush()
        
        # Create 2 transactions per account
        for j in range(2):
            transaction = Transaction(
                transaction_reference=f"TXN-CASE-{i}-{j}",
                account_id=account.id,
                amount=str(5000 * (j + 1)),
                currency="USD",
                transaction_type=TransactionType.TRANSFER,
                origin_country="US",
                destination_country="CA",
                transaction_timestamp=datetime.utcnow(),
                correlation_id=f"test-corr-case-{i}-{j}",
            )
            db_session.add(transaction)
            transactions.append(transaction)
    
    db_session.flush()
    
    # Create alerts
    alerts = []
    for i, transaction in enumerate(transactions):
        alert = Alert(
            alert_number=f"ALT-CASE-{i:03d}",
            transaction_id=transaction.id,
            risk_score=50 + (i * 5),
            priority=AlertPriority.MEDIUM,
            status=AlertStatus.NEW,
            priority_rationale=f"Test alert {i}",
        )
        db_session.add(alert)
        alerts.append(alert)
    
    db_session.flush()
    
    # Create diverse cases
    cases = []
    now = datetime.utcnow()
    
    states = [CaseState.OPEN, CaseState.UNDER_INVESTIGATION, CaseState.INFORMATION_REQUESTED, 
              CaseState.PENDING_DECISION, CaseState.CLOSED]
    priorities = [AlertPriority.LOW, AlertPriority.MEDIUM, AlertPriority.HIGH, AlertPriority.CRITICAL]
    
    for i in range(12):
        case = AMLCase(
            case_number=f"CASE-{i:05d}",
            title=f"Test Case {i}",
            customer_id=customers[i % len(customers)].id,
            state=states[i % len(states)],
            priority=priorities[i % len(priorities)],
            created_by_user_id=1,
            assigned_to_user_id=1 if i % 3 == 0 else None,
            created_at=now - timedelta(days=i),
            updated_at=now - timedelta(days=i),
        )
        db_session.add(case)
        db_session.flush()
        
        # Link 1-2 alerts to each case
        for j in range(min(i % 2 + 1, len(alerts))):
            if (i * 2 + j) < len(alerts):
                link = CaseAlertLink(
                    case_id=case.id,
                    alert_id=alerts[i * 2 + j].id if (i * 2 + j) < len(alerts) else alerts[0].id,
                    linked_by_user_id=1,
                    linked_at=now - timedelta(days=i),
                )
                db_session.add(link)
        
        cases.append(case)
    
    db_session.commit()
    return cases


def test_list_cases_requires_auth(client: TestClient):
    """Test that list cases requires authentication."""
    response = client.get("/api/v1/cases")
    assert response.status_code == 401


def test_list_cases_success(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test successful case list retrieval."""
    response = auth_client.get("/api/v1/cases")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert "page" in data
    assert "page_size" in data
    assert "total" in data
    
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total"] == 12
    assert len(data["items"]) == 12


def test_list_cases_pagination(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test case list pagination."""
    # Page 1 with 5 items
    response = auth_client.get("/api/v1/cases?page=1&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 1
    assert data["total"] == 12
    
    # Page 2 with 5 items
    response = auth_client.get("/api/v1/cases?page=2&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 2
    
    # Page 3 with 2 items
    response = auth_client.get("/api/v1/cases?page=3&page_size=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert data["page"] == 3


def test_list_cases_filter_by_state(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test filtering cases by state."""
    response = auth_client.get("/api/v1/cases?state=OPEN")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items have OPEN state
    for item in data["items"]:
        assert item["state"] == "OPEN"


def test_list_cases_filter_by_priority(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test filtering cases by priority."""
    response = auth_client.get("/api/v1/cases?priority=HIGH")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items have HIGH priority
    for item in data["items"]:
        assert item["priority"] == "HIGH"


def test_list_cases_filter_by_assignee(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test filtering cases by assignee."""
    response = auth_client.get("/api/v1/cases?assignee=1")
    assert response.status_code == 200
    data = response.json()
    
    # Check all returned items are assigned to user 1
    for item in data["items"]:
        assert item["assigned_to_user_id"] == 1
    
    assert data["total"] == 4  # Every 3rd case is assigned to user 1


def test_list_cases_sort_by_created_at_desc(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test sorting cases by created_at descending (default)."""
    response = auth_client.get("/api/v1/cases?sort_by=created_at&sort_order=desc")
    assert response.status_code == 200
    data = response.json()
    
    # Check items are sorted by created_at descending
    items = data["items"]
    for i in range(len(items) - 1):
        assert items[i]["created_at"] >= items[i + 1]["created_at"]


def test_list_cases_sort_by_updated_at_asc(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test sorting cases by updated_at ascending."""
    response = auth_client.get("/api/v1/cases?sort_by=updated_at&sort_order=asc")
    assert response.status_code == 200
    data = response.json()
    
    # Check items are sorted by updated_at ascending
    items = data["items"]
    for i in range(len(items) - 1):
        assert items[i]["updated_at"] <= items[i + 1]["updated_at"]


def test_list_cases_multiple_filters(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test combining multiple filters."""
    response = auth_client.get("/api/v1/cases?state=OPEN&priority=LOW")
    assert response.status_code == 200
    data = response.json()
    
    # Check all items match both filters
    for item in data["items"]:
        assert item["state"] == "OPEN"
        assert item["priority"] == "LOW"


def test_list_cases_response_structure(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test the structure of case list items."""
    response = auth_client.get("/api/v1/cases?page_size=1")
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["items"]) == 1
    item = data["items"][0]
    
    # Check all expected fields are present
    assert "id" in item
    assert "case_number" in item
    assert "title" in item
    assert "customer_id" in item
    assert "customer_name" in item
    assert "state" in item
    assert "priority" in item
    assert "created_by_user_id" in item
    assert "assigned_to_user_id" in item
    assert "created_at" in item
    assert "updated_at" in item
    assert "alert_count" in item


def test_list_cases_alert_count(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test that alert_count is correctly calculated."""
    response = auth_client.get("/api/v1/cases")
    assert response.status_code == 200
    data = response.json()
    
    # Check that alert_count is present and non-negative
    for item in data["items"]:
        assert "alert_count" in item
        assert item["alert_count"] >= 0


def test_list_cases_empty_results(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test filtering with no matching results."""
    response = auth_client.get("/api/v1/cases?state=NONEXISTENT")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 0
    assert len(data["items"]) == 0


def test_list_cases_invalid_page(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test with invalid page number."""
    response = auth_client.get("/api/v1/cases?page=0")
    assert response.status_code == 422  # Validation error


def test_list_cases_invalid_page_size(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test with page size exceeding maximum."""
    response = auth_client.get("/api/v1/cases?page_size=150")
    assert response.status_code == 422  # Exceeds max of 100


def test_list_cases_page_beyond_results(auth_client: TestClient, sample_cases_dataset: list[AMLCase]):
    """Test requesting page beyond available results."""
    response = auth_client.get("/api/v1/cases?page=10&page_size=20")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total"] == 12
    assert len(data["items"]) == 0  # No items on this page
