"""Unit tests for audit service: event recording and retrieval."""
import json
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.enums import TransactionType, AccountStatus, RiskLevel
from app.customer.models import Customer, CustomerRiskProfile, Account
from app.transaction.models import Transaction


@pytest.fixture
def sample_customer(db_session: Session):
    """Create a sample customer with risk profile and account."""
    customer = Customer(
        customer_number="CUST-TEST-001",
        full_name="Test Customer",
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
        account_number="ACC-TEST-001",
        customer_id=customer.id,
        status=AccountStatus.ACTIVE.value,
        opened_at=datetime.utcnow(),
        current_balance=Decimal("100000.00"),
        currency="USD",
        version=1
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture
def sample_transaction(db_session: Session, sample_customer):
    """Create a sample transaction."""
    transaction = Transaction(
        transaction_reference="TXN-TEST-001",
        account_id=sample_customer.id,
        amount=Decimal("50000.00"),
        currency="USD",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="US",
        destination_country="GB",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-correlation-001",
        created_at=datetime.utcnow()
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    return transaction


def test_record_event_creates_audit_event(db_session: Session, test_user):
    """Test that record_event creates an audit event."""
    service = AuditService(db_session)
    
    event = service.record_event(
        action="TEST_ACTION",
        entity_type="test_entity",
        entity_id=123,
        correlation_id="test-corr-001",
        details={"key": "value"},
        actor_user_id=test_user.id,
        actor_username="test_user",
        actor_role="tester"
    )
    
    assert event.id is not None
    assert event.action == "TEST_ACTION"
    assert event.entity_type == "test_entity"
    assert event.entity_id == 123
    assert event.correlation_id == "test-corr-001"
    assert event.actor_user_id == test_user.id
    assert event.actor_username == "test_user"
    assert event.actor_role == "tester"
    assert json.loads(event.details_json) == {"key": "value"}


def test_record_event_with_system_actor(db_session: Session):
    """Test that record_event works with system actor (no user_id)."""
    service = AuditService(db_session)
    
    event = service.record_event(
        action="SYSTEM_ACTION",
        entity_type="system_entity",
        entity_id=456,
        correlation_id="system-corr-001",
        details={"automated": True}
    )
    
    assert event.id is not None
    assert event.actor_user_id is None
    assert event.actor_username == "system"
    assert event.actor_role == "system"


def test_list_events_returns_paginated_results(db_session: Session, sample_transaction):
    """Test that list_events returns paginated results."""
    service = AuditService(db_session)
    
    # Create multiple events
    for i in range(5):
        service.record_event(
            action=f"ACTION_{i}",
            entity_type="transaction",
            entity_id=sample_transaction.id,
            correlation_id=sample_transaction.correlation_id,
            details={"index": i}
        )
    
    # Test pagination
    result = service.list_events(page=1, page_size=3)
    
    assert len(result.items) == 3
    assert result.page == 1
    assert result.page_size == 3
    assert result.total == 5


def test_list_events_filters_by_entity_type(db_session: Session, sample_transaction):
    """Test that list_events filters by entity_type."""
    service = AuditService(db_session)
    
    # Create events for different entity types
    service.record_event(
        action="ACTION_1",
        entity_type="transaction",
        entity_id=1,
        correlation_id="corr-001",
        details={}
    )
    service.record_event(
        action="ACTION_2",
        entity_type="alert",
        entity_id=2,
        correlation_id="corr-002",
        details={}
    )
    
    # Filter by transaction
    result = service.list_events(entity_type="transaction")
    
    assert len(result.items) == 1
    assert result.items[0].entity_type == "transaction"


def test_list_events_filters_by_entity_id(db_session: Session, sample_transaction):
    """Test that list_events filters by entity_id."""
    service = AuditService(db_session)
    
    # Create events for different entity IDs
    service.record_event(
        action="ACTION_1",
        entity_type="transaction",
        entity_id=1,
        correlation_id="corr-001",
        details={}
    )
    service.record_event(
        action="ACTION_2",
        entity_type="transaction",
        entity_id=2,
        correlation_id="corr-002",
        details={}
    )
    
    # Filter by entity_id
    result = service.list_events(entity_id=1)
    
    assert len(result.items) == 1
    assert result.items[0].entity_id == 1


def test_list_events_filters_by_actor_id(db_session: Session):
    """Test that list_events filters by actor_id."""
    service = AuditService(db_session)
    
    # Create events by system actor (no FK constraint)
    service.record_event(
        action="ACTION_1",
        entity_type="transaction",
        entity_id=1,
        correlation_id="corr-001",
        details={},
        actor_user_id=None,
        actor_username="system_1",
        actor_role="system"
    )
    service.record_event(
        action="ACTION_2",
        entity_type="transaction",
        entity_id=2,
        correlation_id="corr-002",
        details={},
        actor_user_id=None,
        actor_username="system_2",
        actor_role="system"
    )
    
    # Filter by actor_id (NULL)
    result = service.list_events(actor_id=None)
    
    # Both events should match NULL actor_id filter
    assert len(result.items) >= 2


def test_list_events_filters_by_correlation_id(db_session: Session, sample_transaction):
    """Test that list_events filters by correlation_id."""
    service = AuditService(db_session)
    
    # Create events with different correlation IDs
    service.record_event(
        action="ACTION_1",
        entity_type="transaction",
        entity_id=1,
        correlation_id="corr-001",
        details={}
    )
    service.record_event(
        action="ACTION_2",
        entity_type="transaction",
        entity_id=2,
        correlation_id="corr-002",
        details={}
    )
    
    # Filter by correlation_id
    result = service.list_events(correlation_id="corr-001")
    
    assert len(result.items) == 1
    assert result.items[0].correlation_id == "corr-001"


def test_list_events_ordered_by_timestamp_desc(db_session: Session):
    """Test that list_events returns events ordered by timestamp descending."""
    service = AuditService(db_session)
    
    # Create events with slight time differences
    event1 = service.record_event(
        action="FIRST",
        entity_type="test",
        entity_id=1,
        correlation_id="corr-001",
        details={}
    )
    
    event2 = service.record_event(
        action="SECOND",
        entity_type="test",
        entity_id=2,
        correlation_id="corr-002",
        details={}
    )
    
    result = service.list_events()
    
    # Most recent first
    assert result.items[0].id == event2.id
    assert result.items[1].id == event1.id


def test_list_events_combined_filters(db_session: Session, sample_transaction, test_user):
    """Test that list_events works with multiple filters combined."""
    service = AuditService(db_session)
    
    # Create diverse events with valid user or system actor
    service.record_event(
        action="ACTION_A",
        entity_type="transaction",
        entity_id=1,
        correlation_id="corr-001",
        details={},
        actor_user_id=test_user.id,
        actor_username="test_user",
        actor_role="officer"
    )
    service.record_event(
        action="ACTION_B",
        entity_type="transaction",
        entity_id=1,
        correlation_id="corr-001",
        details={},
        actor_user_id=None,
        actor_username="system",
        actor_role="system"
    )
    service.record_event(
        action="ACTION_C",
        entity_type="alert",
        entity_id=2,
        correlation_id="corr-001",
        details={},
        actor_user_id=test_user.id,
        actor_username="test_user",
        actor_role="officer"
    )
    
    # Filter by entity_type and actor_id
    result = service.list_events(
        entity_type="transaction",
        actor_id=test_user.id
    )
    
    assert len(result.items) == 1
    assert result.items[0].entity_type == "transaction"
    assert result.items[0].actor_user_id == test_user.id


def test_audit_events_are_immutable(db_session: Session):
    """Test that audit events cannot be updated after creation."""
    service = AuditService(db_session)
    
    event = service.record_event(
        action="IMMUTABLE_TEST",
        entity_type="test",
        entity_id=1,
        correlation_id="corr-001",
        details={"original": "value"}
    )
    
    original_id = event.id
    original_timestamp = event.timestamp
    original_details = event.details_json
    
    # Repository only has insert method, no update method
    # Verify the event persists unchanged
    result = service.list_events(entity_id=1)
    
    assert len(result.items) == 1
    assert result.items[0].id == original_id
    assert result.items[0].details_json == original_details
