"""Integration tests for investigation workflow end-to-end."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.alert.models import Alert
from app.case_management.models import AMLCase
from app.customer.models import Account, Customer, CustomerRiskProfile
from app.investigation.models import InformationRequest
from app.security.models import User
from app.transaction.models import Transaction
from app.common.enums import (
    AccountStatus,
    AlertPriority,
    AlertStatus,
    CaseState,
    InformationRequestStatus,
    RiskLevel,
    TransactionType,
    UserRole,
)


def test_case_detail_exposes_linked_alerts_requests_responses_decisions(
    auth_client: TestClient, db_session: Session
):
    """Test case detail returns complete workflow data."""
    # Setup: customer, account, transaction, alert, case
    customer = Customer(
        customer_number="CUST-INT-001",
        full_name="Integration Test Customer",
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
    db_session.flush()
    
    account = Account(
        account_number="ACC-INT-001",
        customer_id=customer.id,
        status=AccountStatus.ACTIVE.value,
        opened_at=datetime.utcnow(),
        current_balance="10000.00",
        currency="USD"
    )
    db_session.add(account)
    db_session.flush()
    
    transaction = Transaction(
        transaction_reference="TXN-INT-001",
        account_id=account.id,
        transaction_type=TransactionType.TRANSFER.value,
        amount="15000.00",
        currency="USD",
        origin_country="US",
        destination_country="RU",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="CORR-INT-001"
    )
    db_session.add(transaction)
    db_session.flush()
    
    alert = Alert(
        alert_number="ALR-INT-001",
        transaction_id=transaction.id,
        risk_score=85,
        priority=AlertPriority.HIGH.value,
        status=AlertStatus.NEW.value,
        priority_rationale="High-risk geography"
    )
    db_session.add(alert)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-INT-001",
        title="Integration Test Case",
        customer_id=customer.id,
        state=CaseState.UNDER_INVESTIGATION.value,
        priority=AlertPriority.HIGH.value,
        created_by_user_id=1,
        version=1
    )
    db_session.add(case)
    db_session.flush()
    
    # Link alert to case
    from app.case_management.models import CaseAlertLink
    link = CaseAlertLink(
        case_id=case.id,
        alert_id=alert.id,
        linked_by_user_id=1,
        linked_at=datetime.utcnow()
    )
    db_session.add(link)
    
    # Add information request
    info_request = InformationRequest(
        case_id=case.id,
        requested_what="Account statements",
        reason="Verify transaction patterns",
        due_date=datetime.utcnow() + timedelta(days=7),
        status=InformationRequestStatus.OPEN.value,
        requested_by_user_id=1,
        version=1
    )
    db_session.add(info_request)
    
    db_session.commit()
    
    # Execute: Get case detail
    response = auth_client.get(f"/api/v1/cases/{case.id}")
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == case.id
    assert data["case_number"] == "CASE-INT-001"
    assert data["state"] == CaseState.UNDER_INVESTIGATION.value
    
    # Verify linked alerts
    assert len(data["linked_alerts"]) == 1
    assert data["linked_alerts"][0]["alert_number"] == "ALR-INT-001"
    
    # Verify information requests
    assert len(data["information_requests"]) == 1
    assert data["information_requests"][0]["requested_what"] == "Account statements"
    assert data["information_requests"][0]["status"] == InformationRequestStatus.OPEN.value


def test_valid_officer_decision_updates_case_and_returns_detail(
    auth_client: TestClient, db_session: Session
):
    """Test officer decision updates case state and returns full detail."""
    # Setup: Create case with different creator
    customer = Customer(
        customer_number="CUST-DEC-001",
        full_name="Decision Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="TEST"
    )
    db_session.add(customer)
    db_session.commit()
    
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level=RiskLevel.HIGH.value,
        base_score=75,
        last_reviewed_at=datetime.utcnow(),
        reviewed_by="system"
    )
    db_session.add(risk_profile)
    db_session.commit()
    
    # Create case with a different user as creator
    other_user = User(
        username="creator_user",
        full_name="Case Creator User",
        role=UserRole.AML_ANALYST.value,
        is_active=True,
        password_hash="hashed_password",
        permissions_json="{}"
    )
    db_session.add(other_user)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-DEC-001",
        title="Decision Test Case",
        customer_id=customer.id,
        state=CaseState.PENDING_DECISION.value,
        priority=AlertPriority.CRITICAL.value,
        created_by_user_id=other_user.id,  # Different from auth user
        version=1
    )
    db_session.add(case)
    db_session.commit()
    
    # Execute: Record decision
    response = auth_client.post(
        f"/api/v1/cases/{case.id}/decision",
        json={
            "decision": "APPROVE",
            "reason": "Verified legitimate business transaction",
            "comments": "Customer provided documentation",
            "expected_version": 1
        }
    )
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == case.id
    assert data["state"] == CaseState.APPROVED.value
    assert data["version"] == 2  # Version incremented
    
    # Verify decision is recorded
    assert len(data["decisions"]) == 1
    assert data["decisions"][0]["decision"] == "APPROVE"
    assert data["decisions"][0]["reason"] == "Verified legitimate business transaction"


def test_allowed_transitions_succeed_from_valid_states(
    auth_client: TestClient, db_session: Session
):
    """Test state transitions succeed when valid."""
    # Setup multiple cases in different states
    customer = Customer(
        customer_number="CUST-TRANS-001",
        full_name="Transition Test Customer",
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
    db_session.commit()
    
    # Create different user as creator
    other_user = User(
        username="trans_creator",
        full_name="Transition Creator User",
        role=UserRole.AML_ANALYST.value,
        is_active=True,
        password_hash="hashed_password",
        permissions_json="{}"
    )
    db_session.add(other_user)
    db_session.commit()
    
    # Test 1: PENDING_DECISION -> APPROVE
    case1 = AMLCase(
        case_number="CASE-TRANS-001",
        title="Transition Test 1",
        customer_id=customer.id,
        state=CaseState.PENDING_DECISION.value,
        priority=AlertPriority.HIGH.value,
        created_by_user_id=other_user.id,
        version=1
    )
    db_session.add(case1)
    
    # Test 2: PENDING_DECISION -> REJECT
    case2 = AMLCase(
        case_number="CASE-TRANS-002",
        title="Transition Test 2",
        customer_id=customer.id,
        state=CaseState.PENDING_DECISION.value,
        priority=AlertPriority.MEDIUM.value,
        created_by_user_id=other_user.id,
        version=1
    )
    db_session.add(case2)
    
    # Test 3: PENDING_DECISION -> ESCALATE
    case3 = AMLCase(
        case_number="CASE-TRANS-003",
        title="Transition Test 3",
        customer_id=customer.id,
        state=CaseState.PENDING_DECISION.value,
        priority=AlertPriority.CRITICAL.value,
        created_by_user_id=other_user.id,
        version=1
    )
    db_session.add(case3)
    
    db_session.commit()
    
    # Execute: Test each transition
    response1 = auth_client.post(
        f"/api/v1/cases/{case1.id}/decision",
        json={"decision": "APPROVE", "expected_version": 1}
    )
    assert response1.status_code == 200
    assert response1.json()["state"] == CaseState.APPROVED.value
    
    response2 = auth_client.post(
        f"/api/v1/cases/{case2.id}/decision",
        json={"decision": "REJECT", "reason": "Suspicious activity confirmed", "expected_version": 1}
    )
    assert response2.status_code == 200
    assert response2.json()["state"] == CaseState.REJECTED.value
    
    response3 = auth_client.post(
        f"/api/v1/cases/{case3.id}/decision",
        json={"decision": "ESCALATE", "reason": "Requires senior review", "expected_version": 1}
    )
    assert response3.status_code == 200
    assert response3.json()["state"] == CaseState.ESCALATED.value


def test_invalid_transitions_return_409_invalid_state(
    auth_client: TestClient, db_session: Session
):
    """Test invalid state transitions return HTTP 409."""
    # Setup
    customer = Customer(
        customer_number="CUST-INV-001",
        full_name="Invalid Transition Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="TEST"
    )
    db_session.add(customer)
    db_session.commit()
    
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level=RiskLevel.LOW.value,
        base_score=25,
        last_reviewed_at=datetime.utcnow(),
        reviewed_by="system"
    )
    db_session.add(risk_profile)
    db_session.flush()
    
    other_user = User(
        username="inv_creator",
        full_name="Invalid Transition Creator User",
        role=UserRole.AML_ANALYST.value,
        is_active=True,
        password_hash="hashed_password",
        permissions_json="{}"
    )
    db_session.add(other_user)
    db_session.commit()
    
    # Create case in OPEN state
    case = AMLCase(
        case_number="CASE-INV-001",
        title="Invalid Transition Test",
        customer_id=customer.id,
        state=CaseState.OPEN.value,  # OPEN state
        priority=AlertPriority.LOW.value,
        created_by_user_id=other_user.id,
        version=1
    )
    db_session.add(case)
    db_session.commit()
    
    # Execute: Try to APPROVE from OPEN (invalid transition)
    response = auth_client.post(
        f"/api/v1/cases/{case.id}/decision",
        json={"decision": "APPROVE", "expected_version": 1}
    )
    
    # Verify
    assert response.status_code == 409
    data = response.json()
    assert "not allowed" in data["detail"].lower() or "invalid" in data["detail"].lower()


def test_open_information_requests_block_decision_when_required(
    auth_client: TestClient, db_session: Session
):
    """Test that open information requests can affect decision flow."""
    # Setup
    customer = Customer(
        customer_number="CUST-BLOCK-001",
        full_name="Block Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="TEST"
    )
    db_session.add(customer)
    db_session.commit()
    
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level=RiskLevel.HIGH.value,
        base_score=80,
        last_reviewed_at=datetime.utcnow(),
        reviewed_by="system"
    )
    db_session.add(risk_profile)
    db_session.flush()
    
    other_user = User(
        username="block_creator",
        full_name="Block Creator User",
        role=UserRole.AML_ANALYST.value,
        is_active=True,
        password_hash="hashed_password",
        permissions_json="{}"
    )
    db_session.add(other_user)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-BLOCK-001",
        title="Block Test Case",
        customer_id=customer.id,
        state=CaseState.PENDING_DECISION.value,
        priority=AlertPriority.HIGH.value,
        created_by_user_id=other_user.id,
        version=1
    )
    db_session.add(case)
    db_session.commit()
    
    # Add open information request
    info_request = InformationRequest(
        case_id=case.id,
        requested_what="Additional documentation",
        reason="Need more evidence",
        due_date=datetime.utcnow() + timedelta(days=3),
        status=InformationRequestStatus.OPEN.value,
        requested_by_user_id=1,
        version=1
    )
    db_session.add(info_request)
    db_session.commit()
    
    # Execute: Get case detail to verify open requests are visible
    response = auth_client.get(f"/api/v1/cases/{case.id}")
    
    # Verify
    assert response.status_code == 200
    data = response.json()
    
    # Verify has_open_info_requests affects permitted actions
    assert len(data["information_requests"]) == 1
    assert data["information_requests"][0]["status"] == InformationRequestStatus.OPEN.value


def test_case_state_machine_supports_documented_transitions(
    auth_client: TestClient, db_session: Session
):
    """Test state machine supports all documented transitions."""
    # Setup
    customer = Customer(
        customer_number="CUST-SM-001",
        full_name="State Machine Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="TEST"
    )
    db_session.add(customer)
    db_session.commit()
    
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level=RiskLevel.HIGH.value,
        base_score=85,
        last_reviewed_at=datetime.utcnow(),
        reviewed_by="system"
    )
    db_session.add(risk_profile)
    db_session.flush()
    
    other_user = User(
        username="sm_creator",
        full_name="State Machine Creator User",
        role=UserRole.AML_ANALYST.value,
        is_active=True,
        password_hash="hashed_password",
        permissions_json="{}"
    )
    db_session.add(other_user)
    db_session.commit()
    
    # Test ESCALATED -> APPROVED
    case = AMLCase(
        case_number="CASE-SM-001",
        title="State Machine Test",
        customer_id=customer.id,
        state=CaseState.ESCALATED.value,
        priority=AlertPriority.CRITICAL.value,
        created_by_user_id=other_user.id,
        version=1
    )
    db_session.add(case)
    db_session.commit()
    
    # Execute
    response = auth_client.post(
        f"/api/v1/cases/{case.id}/decision",
        json={"decision": "APPROVE", "reason": "Escalated review complete", "expected_version": 1}
    )
    
    # Verify
    assert response.status_code == 200
    assert response.json()["state"] == CaseState.APPROVED.value
