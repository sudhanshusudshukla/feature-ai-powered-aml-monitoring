"""Unit tests for case management service."""
import uuid
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from app.alert.models import Alert
from app.case_management.models import AMLCase
from app.case_management.service import CaseManagementService
from app.case_management.state_machine import CaseStateMachine
from app.common.enums import (
    AccountStatus,
    AlertPriority,
    AlertStatus,
    CaseState,
    RiskLevel,
    TransactionType,
    UserRole,
)
from app.common.errors import (
    AuthorizationError,
    DomainValidationError,
    InvalidStateTransitionError,
    NotFoundError,
)
from app.customer.models import Account, Customer, CustomerRiskProfile
from app.security.models import User
from app.transaction.models import Transaction


def test_create_case_from_single_alert(db_session: Session):
    """Test creating a case from a single alert."""
    # Setup: create user, customer, account, transaction, alert
    user = User(
        username="analyst",
        full_name="Test Analyst",
        role=UserRole.AML_ANALYST.value,
        is_active=True,
        password_hash="hashed",
        permissions_json="{}"
    )
    db_session.add(user)
    
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
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-corr-id"
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
    
    # Act: create case
    service = CaseManagementService(db_session)
    result = service.create_case(
        title="Suspicious high-value transfer",
        alert_ids=[alert.id],
        actor_user=user
    )
    
    # Assert
    assert result.case_number.startswith("CASE-")
    assert result.title == "Suspicious high-value transfer"
    assert result.customer_id == customer.id
    assert result.state == CaseState.OPEN.value
    assert result.priority == AlertPriority.HIGH.value
    assert result.created_by_user_id == user.id
    assert len(result.linked_alerts) == 1
    assert result.linked_alerts[0].id == alert.id


def test_create_case_from_multiple_alerts_uses_highest_priority(db_session: Session):
    """Test that case priority is highest of linked alerts."""
    # Setup
    user = User(
        username="analyst",
        full_name="Test Analyst",
        role=UserRole.AML_ANALYST.value,
        is_active=True,
        password_hash="hashed",
        permissions_json="{}"
    )
    db_session.add(user)
    
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
    
    transaction1 = Transaction(
        transaction_reference="TXN001",
        account_id=account.id,
        amount="5000.00",
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="US",
        destination_country="IN",
        transaction_timestamp=datetime.utcnow(), correlation_id="test-corr-id"
    )
    db_session.add(transaction1)
    db_session.flush()
    
    transaction2 = Transaction(
        transaction_reference="TXN002",
        account_id=account.id,
        amount="15000.00",
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="US",
        destination_country="IN",
        transaction_timestamp=datetime.utcnow(), correlation_id="test-corr-id"
    )
    db_session.add(transaction2)
    db_session.flush()
    
    alert1 = Alert(
        alert_number="ALT-000001",
        transaction_id=transaction1.id,
        risk_score=60,
        priority=AlertPriority.MEDIUM.value,
        status=AlertStatus.NEW.value,
        priority_rationale="Medium risk"
    )
    db_session.add(alert1)
    
    alert2 = Alert(
        alert_number="ALT-000002",
        transaction_id=transaction2.id,
        risk_score=85,
        priority=AlertPriority.CRITICAL.value,
        status=AlertStatus.NEW.value,
        priority_rationale="Critical risk"
    )
    db_session.add(alert2)
    db_session.commit()
    
    # Act
    service = CaseManagementService(db_session)
    result = service.create_case(
        title="Multi-alert case",
        alert_ids=[alert1.id, alert2.id],
        actor_user=user
    )
    
    # Assert: case priority should be CRITICAL (highest)
    assert result.priority == AlertPriority.CRITICAL.value
    assert len(result.linked_alerts) == 2


def test_create_case_fails_if_alert_already_linked(db_session: Session):
    """Test that creating case fails if alert already linked to another case."""
    # Setup
    user = User(
        username="analyst",
        full_name="Test Analyst",
        role=UserRole.AML_ANALYST.value,
        is_active=True,
        password_hash="hashed",
        permissions_json="{}"
    )
    db_session.add(user)
    
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
    service = CaseManagementService(db_session)
    service.create_case(
        title="First case",
        alert_ids=[alert.id],
        actor_user=user
    )
    
    # Act: attempt to create second case with same alert
    with pytest.raises(DomainValidationError) as exc_info:
        service.create_case(
            title="Second case",
            alert_ids=[alert.id],
            actor_user=user
        )
    
    assert "already linked" in str(exc_info.value).lower()


def test_create_case_fails_if_alert_not_found(db_session: Session):
    """Test that creating case fails if alert doesn't exist."""
    user = User(
        username="analyst",
        full_name="Test Analyst",
        role=UserRole.AML_ANALYST.value,
        is_active=True,
        password_hash="hashed",
        permissions_json="{}"
    )
    db_session.add(user)
    db_session.commit()
    
    service = CaseManagementService(db_session)
    
    with pytest.raises(NotFoundError) as exc_info:
        service.create_case(
            title="Invalid case",
            alert_ids=[99999],
            actor_user=user
        )
    
    assert "not found" in str(exc_info.value).lower()


def test_get_case_detail_includes_permitted_actions(db_session: Session):
    """Test that case detail includes permitted actions for user."""
    # Setup: create case
    analyst = User(
        username="analyst",
        full_name="Test Analyst",
        role=UserRole.AML_ANALYST.value,
        is_active=True,
        password_hash="hashed",
        permissions_json="{}"
    )
    db_session.add(analyst)
    
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
        created_by_user_id=analyst.id
    )
    db_session.add(case)
    db_session.commit()
    
    # Act
    service = CaseManagementService(db_session)
    result = service.get_case_detail(case.id, analyst)
    
    # Assert: analyst should be able to START_INVESTIGATION
    assert "START_INVESTIGATION" in result.permitted_actions


def test_creator_cannot_decide_own_case(db_session: Session):
    """Test separation of duties: creator cannot make decision."""
    # Setup: create case as analyst, then try to decide as same user with officer role
    creator = User(
        username="officer1",
        full_name="Test Officer",
        role=UserRole.AML_OFFICER.value,
        is_active=True,
        password_hash="hashed",
        permissions_json="{}"
    )
    db_session.add(creator)
    
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
    
    # Act: creator tries to decide
    service = CaseManagementService(db_session)
    
    with pytest.raises(AuthorizationError) as exc_info:
        service.record_decision(
            case_id=case.id,
            decision="APPROVE",
            expected_version=1,
            actor_user=creator
        )
    
    assert "creator cannot" in str(exc_info.value).lower()


def test_different_officer_can_decide_case(db_session: Session):
    """Test that a different officer can decide case (not creator)."""
    # Setup
    creator = User(
        username="officer1",
        full_name="Creator Officer",
        role=UserRole.AML_OFFICER.value,
        is_active=True,
        password_hash="hashed",
        permissions_json="{}"
    )
    db_session.add(creator)
    
    decider = User(
        username="officer2",
        full_name="Decider Officer",
        role=UserRole.AML_OFFICER.value,
        is_active=True,
        password_hash="hashed",
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
    
    # Act: different officer decides
    service = CaseManagementService(db_session)
    result = service.record_decision(
        case_id=case.id,
        decision="APPROVE",
        expected_version=1,
        actor_user=decider,
        reason="Reviewed and approved"
    )
    
    # Assert
    assert result.state == CaseState.APPROVED.value
    assert len(result.decisions) == 1
    assert result.decisions[0].decided_by_user_id == decider.id


def test_invalid_state_transition_raises_error(db_session: Session):
    """Test that invalid state transitions are rejected."""
    creator_user = User(
        username="creator",
        full_name="Test Creator",
        role=UserRole.AML_ANALYST.value,
        is_active=True,
        password_hash="hashed",
        permissions_json="{}"
    )
    db_session.add(creator_user)
    
    officer_user = User(
        username="officer",
        full_name="Test Officer",
        role=UserRole.AML_OFFICER.value,
        is_active=True,
        password_hash="hashed",
        permissions_json="{}"
    )
    db_session.add(officer_user)
    
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
    
    # Case in OPEN state created by creator_user
    case = AMLCase(
        case_number="CASE-000001",
        title="Test case",
        customer_id=customer.id,
        state=CaseState.OPEN.value,
        priority=AlertPriority.HIGH.value,
        created_by_user_id=creator_user.id
    )
    db_session.add(case)
    db_session.commit()
    
    # Act: try invalid transition (APPROVE from OPEN) with different user
    service = CaseManagementService(db_session)
    
    with pytest.raises(InvalidStateTransitionError):
        service.record_decision(
            case_id=case.id,
            decision="APPROVE",
            expected_version=1,
            actor_user=officer_user
        )


def test_state_machine_validates_transitions():
    """Test state machine transition validation."""
    sm = CaseStateMachine()
    
    # Valid transition
    next_state = sm.validate_transition(CaseState.OPEN.value, "START_INVESTIGATION")
    assert next_state == CaseState.UNDER_INVESTIGATION.value
    
    # Invalid transition
    with pytest.raises(InvalidStateTransitionError):
        sm.validate_transition(CaseState.OPEN.value, "APPROVE")


def test_state_machine_computes_analyst_permissions():
    """Test that state machine computes correct analyst permissions."""
    sm = CaseStateMachine()
    
    actions = sm.permitted_actions(
        current_state=CaseState.OPEN.value,
        actor_role=UserRole.AML_ANALYST.value,
        is_creator=False
    )
    
    assert "START_INVESTIGATION" in actions
    # Analysts cannot approve/reject
    assert "APPROVE" not in actions
    assert "REJECT" not in actions


def test_state_machine_enforces_creator_decider_separation():
    """Test that creator-decider separation is enforced in permissions."""
    sm = CaseStateMachine()
    
    # Non-creator officer can approve
    actions_non_creator = sm.permitted_actions(
        current_state=CaseState.PENDING_DECISION.value,
        actor_role=UserRole.AML_OFFICER.value,
        is_creator=False
    )
    assert "APPROVE" in actions_non_creator
    assert "REJECT" in actions_non_creator
    
    # Creator officer cannot approve/reject
    actions_creator = sm.permitted_actions(
        current_state=CaseState.PENDING_DECISION.value,
        actor_role=UserRole.AML_OFFICER.value,
        is_creator=True
    )
    assert "APPROVE" not in actions_creator
    assert "REJECT" not in actions_creator
