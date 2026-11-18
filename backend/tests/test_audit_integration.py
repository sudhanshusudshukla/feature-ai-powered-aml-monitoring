"""Integration tests for audit service: transaction-alert-audit workflow and API endpoints."""
import json
from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.audit.models import AuditEvent
from app.common.enums import (
    TransactionType,
    AccountStatus,
    RiskLevel,
    RuleSeverity,
)
from app.customer.models import Customer, CustomerRiskProfile, Account
from app.rules.models import DetectionRule, RuleVersion


@pytest.fixture
def sample_customer_with_account(db_session: Session):
    """Create a complete customer with risk profile and account."""
    customer = Customer(
        customer_number="CUST-AUDIT-001",
        full_name="Audit Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="TEST",
        version=1
    )
    db_session.add(customer)
    db_session.flush()
    
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level=RiskLevel.LOW.value,
        base_score=20,
        last_reviewed_at=datetime.utcnow(),
        version=1
    )
    db_session.add(risk_profile)
    
    account = Account(
        account_number="ACC-AUDIT-001",
        customer_id=customer.id,
        status=AccountStatus.ACTIVE.value,
        opened_at=datetime.utcnow(),
        current_balance=Decimal("200000.00"),
        currency="USD",
        version=1
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


def test_transaction_ingestion_creates_audit_events(
    auth_client: TestClient,
    db_session: Session,
    sample_customer_with_account,
    all_rules_setup
):
    """Test that transaction ingestion creates TRANSACTION_INGESTED audit event."""
    # Ingest transaction
    payload = {
        "transaction_reference": "TXN-AUDIT-001",
        "account_id": sample_customer_with_account.id,
        "amount": "150000.00",
        "currency": "USD",
        "transaction_type": "TRANSFER",
        "origin_country": "US",
        "destination_country": "GB",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = auth_client.post("/api/v1/transactions/", json=payload)
    assert response.status_code == 201
    
    transaction_data = response.json()
    transaction_id = transaction_data["id"]
    
    # Check that TRANSACTION_INGESTED audit event was created
    audit_events = db_session.query(AuditEvent).filter(
        AuditEvent.action == "TRANSACTION_INGESTED",
        AuditEvent.entity_type == "transaction",
        AuditEvent.entity_id == transaction_id
    ).all()
    
    assert len(audit_events) == 1
    event = audit_events[0]
    assert event.actor_username == "system"
    assert event.actor_role == "system"
    
    details = json.loads(event.details_json)
    assert details["transaction_reference"] == "TXN-AUDIT-001"
    assert details["amount"] == "150000.00"


def test_rule_evaluation_creates_audit_events(
    auth_client: TestClient,
    db_session: Session,
    sample_customer_with_account,
    all_rules_setup
):
    """Test that rule evaluation creates RULE_EVALUATED audit events."""
    # Ingest transaction that triggers high value rule
    payload = {
        "transaction_reference": "TXN-HIGH-VALUE",
        "account_id": sample_customer_with_account.id,
        "amount": "150000.00",
        "currency": "USD",
        "transaction_type": "TRANSFER",
        "origin_country": "US",
        "destination_country": "GB",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = auth_client.post("/api/v1/transactions/", json=payload)
    assert response.status_code == 201
    
    transaction_data = response.json()
    transaction_id = transaction_data["id"]
    
    # Check that RULE_EVALUATED audit events were created (one per rule)
    audit_events = db_session.query(AuditEvent).filter(
        AuditEvent.action == "RULE_EVALUATED",
        AuditEvent.entity_type == "transaction",
        AuditEvent.entity_id == transaction_id
    ).all()
    
    # Should have 8 rule evaluation events (one for each rule)
    assert len(audit_events) == 8
    
    # Verify structure of one event
    event = audit_events[0]
    details = json.loads(event.details_json)
    assert "rule_code" in details
    assert "rule_name" in details
    assert "outcome" in details
    assert "severity" in details


def test_alert_generation_creates_audit_event(
    auth_client: TestClient,
    db_session: Session,
    sample_customer_with_account,
    all_rules_setup
):
    """Test that alert generation creates ALERT_GENERATED audit event."""
    # Ingest transaction that triggers alert (high value)
    payload = {
        "transaction_reference": "TXN-ALERT-GEN",
        "account_id": sample_customer_with_account.id,
        "amount": "150000.00",
        "currency": "USD",
        "transaction_type": "TRANSFER",
        "origin_country": "US",
        "destination_country": "GB",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = auth_client.post("/api/v1/transactions/", json=payload)
    assert response.status_code == 201
    
    transaction_data = response.json()
    
    # Verify alert was raised
    assert transaction_data["alert_raised"] is True
    alert_id = transaction_data["alert_id"]
    
    # Check that ALERT_GENERATED audit event was created
    audit_events = db_session.query(AuditEvent).filter(
        AuditEvent.action == "ALERT_GENERATED",
        AuditEvent.entity_type == "alert",
        AuditEvent.entity_id == alert_id
    ).all()
    
    assert len(audit_events) == 1
    event = audit_events[0]
    
    details = json.loads(event.details_json)
    assert details["transaction_id"] == transaction_data["id"]
    assert "alert_number" in details
    assert "risk_score" in details
    assert "priority" in details


def test_audit_events_share_correlation_id(
    auth_client: TestClient,
    db_session: Session,
    sample_customer_with_account,
    all_rules_setup
):
    """Test that all audit events for a transaction share the same correlation ID."""
    # Ingest transaction
    payload = {
        "transaction_reference": "TXN-CORR-TEST",
        "account_id": sample_customer_with_account.id,
        "amount": "150000.00",
        "currency": "USD",
        "transaction_type": "TRANSFER",
        "origin_country": "US",
        "destination_country": "GB",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = auth_client.post("/api/v1/transactions/", json=payload)
    assert response.status_code == 201
    
    transaction_data = response.json()
    correlation_id = transaction_data["correlation_id"]
    
    # Get all audit events for this correlation ID
    audit_events = db_session.query(AuditEvent).filter(
        AuditEvent.correlation_id == correlation_id
    ).all()
    
    # Should have transaction + 8 rules + alert = 10 events
    assert len(audit_events) >= 10
    
    # All should have the same correlation ID
    for event in audit_events:
        assert event.correlation_id == correlation_id


def test_failed_transaction_no_orphaned_audit(
    auth_client: TestClient,
    db_session: Session
):
    """Test that if transaction creation fails, no orphaned audit events are created."""
    # Try to ingest transaction with non-existent account
    payload = {
        "transaction_reference": "TXN-FAIL",
        "account_id": 999999,  # Non-existent
        "amount": "50000.00",
        "currency": "USD",
        "transaction_type": "TRANSFER",
        "origin_country": "US",
        "destination_country": "GB",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = auth_client.post("/api/v1/transactions/", json=payload)
    assert response.status_code == 404
    
    # Verify no audit events were created
    audit_count = db_session.query(AuditEvent).filter(
        AuditEvent.details_json.contains("TXN-FAIL")
    ).count()
    
    assert audit_count == 0


def test_audit_api_retrieval_by_entity(
    auth_client: TestClient,
    db_session: Session,
    sample_customer_with_account,
    all_rules_setup
):
    """Test audit API endpoint filters by entity type and ID."""
    # Create transaction to generate audit events
    payload = {
        "transaction_reference": "TXN-API-TEST",
        "account_id": sample_customer_with_account.id,
        "amount": "150000.00",
        "currency": "USD",
        "transaction_type": "TRANSFER",
        "origin_country": "US",
        "destination_country": "GB",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = auth_client.post("/api/v1/transactions/", json=payload)
    assert response.status_code == 201
    transaction_data = response.json()
    transaction_id = transaction_data["id"]
    
    # Query audit events via API
    response = auth_client.get(
        "/api/v1/audit",
        params={"entity_type": "transaction", "entity_id": transaction_id}
    )
    
    assert response.status_code == 200
    audit_data = response.json()
    
    assert audit_data["total"] >= 1
    assert len(audit_data["items"]) >= 1
    
    # Verify all items match the filter
    for item in audit_data["items"]:
        assert item["entity_type"] == "transaction"
        assert item["entity_id"] == transaction_id


def test_audit_api_retrieval_by_correlation_id(
    auth_client: TestClient,
    db_session: Session,
    sample_customer_with_account,
    all_rules_setup
):
    """Test audit API endpoint filters by correlation ID."""
    # Create transaction
    payload = {
        "transaction_reference": "TXN-CORR-API",
        "account_id": sample_customer_with_account.id,
        "amount": "150000.00",
        "currency": "USD",
        "transaction_type": "TRANSFER",
        "origin_country": "US",
        "destination_country": "GB",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = auth_client.post("/api/v1/transactions/", json=payload)
    assert response.status_code == 201
    transaction_data = response.json()
    correlation_id = transaction_data["correlation_id"]
    
    # Query by correlation ID
    response = auth_client.get(
        "/api/v1/audit",
        params={"correlation_id": correlation_id}
    )
    
    assert response.status_code == 200
    audit_data = response.json()
    
    # Should retrieve all events for this workflow
    assert audit_data["total"] >= 10  # transaction + 8 rules + alert
    
    for item in audit_data["items"]:
        assert item["correlation_id"] == correlation_id


def test_audit_api_requires_authentication(client: TestClient):
    """Test that audit API requires authentication."""
    response = client.get("/api/v1/audit")
    
    assert response.status_code == 401


def test_audit_api_pagination(
    auth_client: TestClient,
    db_session: Session,
    sample_customer_with_account,
    all_rules_setup
):
    """Test audit API pagination works correctly."""
    # Create transaction to generate multiple audit events
    payload = {
        "transaction_reference": "TXN-PAGINATION",
        "account_id": sample_customer_with_account.id,
        "amount": "150000.00",
        "currency": "USD",
        "transaction_type": "TRANSFER",
        "origin_country": "US",
        "destination_country": "GB",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = auth_client.post("/api/v1/transactions/", json=payload)
    assert response.status_code == 201
    
    # Get first page
    response = auth_client.get("/api/v1/audit", params={"page": 1, "page_size": 5})
    assert response.status_code == 200
    
    page1_data = response.json()
    assert page1_data["page"] == 1
    assert page1_data["page_size"] == 5
    assert len(page1_data["items"]) <= 5
    
    # Get second page if there are more items
    if page1_data["total"] > 5:
        response = auth_client.get("/api/v1/audit", params={"page": 2, "page_size": 5})
        assert response.status_code == 200
        
        page2_data = response.json()
        assert page2_data["page"] == 2
        
        # Ensure different items on different pages
        page1_ids = {item["id"] for item in page1_data["items"]}
        page2_ids = {item["id"] for item in page2_data["items"]}
        assert page1_ids.isdisjoint(page2_ids)


def test_audit_events_not_editable_via_api(auth_client: TestClient):
    """Test that audit events cannot be edited or deleted via API."""
    # Audit router should only have GET endpoint for list, no detail/update/delete
    # Attempting these should return 404 (no such route) or 405 (method not allowed)
    
    # These endpoints don't exist, so 404 is acceptable
    response = auth_client.put("/api/v1/audit/1", json={})
    assert response.status_code in (404, 405)
    
    response = auth_client.patch("/api/v1/audit/1", json={})
    assert response.status_code in (404, 405)
    
    response = auth_client.delete("/api/v1/audit/1")
    assert response.status_code in (404, 405)
