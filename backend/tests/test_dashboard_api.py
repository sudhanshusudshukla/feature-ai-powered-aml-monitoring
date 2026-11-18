"""Integration tests for GET /api/v1/dashboard/summary endpoint."""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.alert.models import Alert
from app.case_management.models import AMLCase
from app.transaction.models import Transaction
from app.rules.models import DetectionRule, RuleVersion
from app.customer.models import Customer, Account
from app.common.enums import (
    AlertPriority, AlertStatus, CaseState,
    TransactionType, AccountStatus, RuleSeverity
)
import json


@pytest.fixture
def sample_dashboard_data(db_session: Session):
    """Create comprehensive data for dashboard testing."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Create customer and account
    customer = Customer(
        customer_number="CUS-DASH-001",
        full_name="Dashboard Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
    )
    db_session.add(customer)
    db_session.flush()
    
    account = Account(
        account_number="ACC-DASH-001",
        customer_id=customer.id,
        status=AccountStatus.ACTIVE,
        opened_at=now,
        current_balance="100000.00",
        currency="USD",
    )
    db_session.add(account)
    db_session.flush()
    
    # Create transactions (15 total to support 15 alerts, 5 today)
    transactions = []
    tx_types = [TransactionType.TRANSFER, TransactionType.DEPOSIT, TransactionType.WITHDRAWAL]
    for i in range(15):
        is_today = i < 5
        tx = Transaction(
            transaction_reference=f"TXN-DASH-{i:03d}",
            account_id=account.id,
            amount=str(1000 * (i + 1)),
            currency="USD",
            transaction_type=tx_types[i % len(tx_types)],
            origin_country="US",
            destination_country="CA",
            transaction_timestamp=today_start + timedelta(hours=i) if is_today else today_start - timedelta(days=i),
            correlation_id=f"dash-corr-{i}",
        )
        db_session.add(tx)
        transactions.append(tx)
    db_session.flush()
    
    # Create alerts with varied priorities and statuses
    priorities = [AlertPriority.LOW, AlertPriority.MEDIUM, AlertPriority.HIGH, AlertPriority.CRITICAL]
    statuses = [AlertStatus.NEW, AlertStatus.UNDER_REVIEW, AlertStatus.CLOSED]
    
    for i in range(15):
        alert = Alert(
            alert_number=f"ALT-DASH-{i:03d}",
            transaction_id=transactions[i].id,  # Now we have 15 transactions for 15 alerts
            risk_score=40 + (i * 3),
            priority=priorities[i % len(priorities)],
            status=statuses[i % len(statuses)],
            priority_rationale=f"Dashboard test alert {i}",
            created_at=now - timedelta(hours=i),
        )
        db_session.add(alert)
    db_session.flush()
    
    # Create cases with varied states and priorities
    case_states = [CaseState.OPEN, CaseState.UNDER_INVESTIGATION, 
                   CaseState.INFORMATION_REQUESTED, CaseState.PENDING_DECISION, CaseState.CLOSED]
    case_priorities = [AlertPriority.LOW, AlertPriority.MEDIUM, AlertPriority.HIGH]
    
    for i in range(10):
        case = AMLCase(
            case_number=f"CASE-DASH-{i:04d}",
            title=f"Dashboard Test Case {i}",
            customer_id=customer.id,
            state=case_states[i % len(case_states)],
            priority=case_priorities[i % len(case_priorities)],
            created_by_user_id=1,
            created_at=now - timedelta(days=i),
            updated_at=now - timedelta(days=i),
        )
        db_session.add(case)
    db_session.flush()
    
    # Create detection rules (mix of active and inactive)
    severities = [RuleSeverity.LOW, RuleSeverity.MEDIUM, RuleSeverity.HIGH]
    for i in range(8):
        rule = DetectionRule(
            rule_code=f"AML-DASH-{i:03d}",
            name=f"Dashboard Test Rule {i}",
            severity=severities[i % len(severities)].value,
            description=f"Test rule {i}",
            is_active=i < 6,  # 6 active, 2 inactive
            version=1,
        )
        db_session.add(rule)
        db_session.flush()
        
        version = RuleVersion(
            rule_id=rule.id,
            version_number=1,
            parameters_json=json.dumps({}),
            effective_from=now,
        )
        db_session.add(version)
    
    db_session.commit()
    return {
        "transactions_today": 5,
        "total_alerts": 15,
        "new_alerts": 5,
        "high_priority_alerts": 7,  # HIGH (4: indices 2,6,10,14) + CRITICAL (3: indices 3,7,11) = 7
        "open_cases": 8,  # Not CLOSED
        "rules_active": 6,
    }


def test_dashboard_summary_requires_auth(client: TestClient):
    """Test that dashboard summary requires authentication."""
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 401


def test_dashboard_summary_success(auth_client: TestClient, sample_dashboard_data: dict):
    """Test successful dashboard summary retrieval."""
    response = auth_client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    
    data = response.json()
    
    # Check top-level structure
    assert "kpis" in data
    assert "alerts_by_priority" in data
    assert "alerts_by_status" in data
    assert "cases_by_state" in data
    assert "transactions_by_type" in data


def test_dashboard_kpis_structure(auth_client: TestClient, sample_dashboard_data: dict):
    """Test KPI counts structure and values."""
    response = auth_client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    
    data = response.json()
    kpis = data["kpis"]
    
    # Check all KPI fields are present
    assert "total_alerts" in kpis
    assert "new_alerts" in kpis
    assert "open_cases" in kpis
    assert "high_priority_alerts" in kpis
    assert "transactions_today" in kpis
    assert "rules_active" in kpis
    
    # Validate expected values
    expected = sample_dashboard_data
    assert kpis["total_alerts"] == expected["total_alerts"]
    assert kpis["new_alerts"] == expected["new_alerts"]
    assert kpis["transactions_today"] == expected["transactions_today"]
    assert kpis["rules_active"] == expected["rules_active"]
    assert kpis["high_priority_alerts"] == expected["high_priority_alerts"]
    assert kpis["open_cases"] == expected["open_cases"]


def test_dashboard_alerts_by_priority(auth_client: TestClient, sample_dashboard_data: dict):
    """Test alerts by priority chart data."""
    response = auth_client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    
    data = response.json()
    alerts_by_priority = data["alerts_by_priority"]
    
    # Check structure
    assert isinstance(alerts_by_priority, list)
    assert len(alerts_by_priority) > 0
    
    # Check each data point has label and value
    for point in alerts_by_priority:
        assert "label" in point
        assert "value" in point
        assert isinstance(point["value"], int)
        assert point["value"] >= 0
    
    # Verify total matches KPI
    total = sum(point["value"] for point in alerts_by_priority)
    assert total == data["kpis"]["total_alerts"]


def test_dashboard_alerts_by_status(auth_client: TestClient, sample_dashboard_data: dict):
    """Test alerts by status chart data."""
    response = auth_client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    
    data = response.json()
    alerts_by_status = data["alerts_by_status"]
    
    # Check structure
    assert isinstance(alerts_by_status, list)
    assert len(alerts_by_status) > 0
    
    # Check each data point has label and value
    for point in alerts_by_status:
        assert "label" in point
        assert "value" in point
        assert isinstance(point["value"], int)
        assert point["value"] >= 0
    
    # Verify total matches KPI
    total = sum(point["value"] for point in alerts_by_status)
    assert total == data["kpis"]["total_alerts"]


def test_dashboard_cases_by_state(auth_client: TestClient, sample_dashboard_data: dict):
    """Test cases by state chart data."""
    response = auth_client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    
    data = response.json()
    cases_by_state = data["cases_by_state"]
    
    # Check structure
    assert isinstance(cases_by_state, list)
    assert len(cases_by_state) > 0
    
    # Check each data point has label and value
    for point in cases_by_state:
        assert "label" in point
        assert "value" in point
        assert isinstance(point["value"], int)
        assert point["value"] >= 0


def test_dashboard_transactions_by_type(auth_client: TestClient, sample_dashboard_data: dict):
    """Test transactions by type chart data."""
    response = auth_client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    
    data = response.json()
    transactions_by_type = data["transactions_by_type"]
    
    # Check structure
    assert isinstance(transactions_by_type, list)
    assert len(transactions_by_type) > 0
    
    # Check each data point has label and value
    for point in transactions_by_type:
        assert "label" in point
        assert "value" in point
        assert isinstance(point["value"], int)
        assert point["value"] >= 0


def test_dashboard_empty_database(auth_client: TestClient, db_session: Session):
    """Test dashboard with no data returns zeros."""
    response = auth_client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    
    data = response.json()
    kpis = data["kpis"]
    
    # All KPIs should be zero
    assert kpis["total_alerts"] == 0
    assert kpis["new_alerts"] == 0
    assert kpis["open_cases"] == 0
    assert kpis["high_priority_alerts"] == 0
    assert kpis["transactions_today"] == 0
    assert kpis["rules_active"] == 0
    
    # Charts should be empty lists
    assert data["alerts_by_priority"] == []
    assert data["alerts_by_status"] == []
    assert data["cases_by_state"] == []
    assert data["transactions_by_type"] == []


def test_dashboard_performance(auth_client: TestClient, sample_dashboard_data: dict):
    """Test dashboard endpoint responds quickly."""
    import time
    
    start = time.time()
    response = auth_client.get("/api/v1/dashboard/summary")
    elapsed = time.time() - start
    
    assert response.status_code == 200
    # Should respond in less than 2 seconds even with aggregations
    assert elapsed < 2.0
