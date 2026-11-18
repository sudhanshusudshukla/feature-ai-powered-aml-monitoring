"""Unit tests for investigation service."""
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.case_management.models import AMLCase
from app.customer.models import Account, Customer, CustomerRiskProfile
from app.investigation.models import InformationRequest
from app.investigation.service import InvestigationService
from app.security.models import User
from app.common.enums import CaseState, InformationRequestStatus, RiskLevel, UserRole
from app.common.errors import DomainValidationError, NotFoundError


def test_add_note_success(db_session: Session):
    """Test adding a note to a case."""
    # Setup
    customer = Customer(
        customer_number="CUST-001",
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
    
    user = User(
        username="analyst",
        full_name="Test Analyst",
        role=UserRole.AML_ANALYST.value,
        is_active=True,
        password_hash="hashed",
        permissions_json="{}"
    )
    db_session.add(user)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-001",
        title="Test Case",
        customer_id=customer.id,
        state=CaseState.OPEN.value,
        priority="MEDIUM",
        created_by_user_id=user.id,
        version=1
    )
    db_session.add(case)
    db_session.commit()
    
    # Execute
    service = InvestigationService(db_session)
    result = service.add_note(
        case_id=case.id,
        note_text="Investigation started",
        actor_user=user
    )
    
    # Verify
    assert result.case_id == case.id
    assert result.note_text == "Investigation started"
    assert result.created_by_user_id == user.id
    assert result.created_at is not None


def test_request_information_success(db_session: Session):
    """Test creating an information request."""
    # Setup
    customer = Customer(
        customer_number="CUST-002",
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
    db_session.commit()
    
    user = User(username="officer", full_name="Test User", role=UserRole.AML_OFFICER.value, is_active=True, password_hash="hashed", permissions_json="{}")
    db_session.add(user)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-002",
        title="Test Case",
        customer_id=customer.id,
        state=CaseState.UNDER_INVESTIGATION.value,
        priority="HIGH",
        created_by_user_id=user.id,
        version=1
    )
    db_session.add(case)
    db_session.commit()
    
    # Execute
    service = InvestigationService(db_session)
    due_date = datetime.utcnow() + timedelta(days=7)
    result = service.request_information(
        case_id=case.id,
        requested_what="Account statements for last 90 days",
        reason="Need to verify transaction patterns",
        due_date=due_date,
        actor_user=user
    )
    
    # Verify
    assert result.case_id == case.id
    assert result.requested_what == "Account statements for last 90 days"
    assert result.status == InformationRequestStatus.OPEN.value
    assert result.requested_by_user_id == user.id


def test_record_response_success(db_session: Session):
    """Test recording a response to an information request."""
    # Setup
    customer = Customer(
        customer_number="CUST-003",
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
    
    user = User(username="analyst", full_name="Test User", role=UserRole.AML_ANALYST.value, is_active=True, password_hash="hashed", permissions_json="{}")
    db_session.add(user)
    db_session.commit()
    
    case = AMLCase(
        case_number="CASE-003",
        title="Test Case",
        customer_id=customer.id,
        state=CaseState.INFORMATION_REQUESTED.value,
        priority="HIGH",
        created_by_user_id=user.id,
        version=1
    )
    db_session.add(case)
    db_session.flush()
    
    request = InformationRequest(
        case_id=case.id,
        requested_what="Documents",
        reason="Verification",
        due_date=datetime.utcnow() + timedelta(days=7),
        status=InformationRequestStatus.OPEN.value,
        requested_by_user_id=user.id,
        version=1
    )
    db_session.add(request)
    db_session.commit()
    
    # Execute
    service = InvestigationService(db_session)
    result = service.record_response(
        request_id=request.id,
        response_text="Documents received and reviewed",
        actor_user=user
    )
    
    # Verify
    assert result.information_request_id == request.id
    assert result.response_text == "Documents received and reviewed"
    assert result.responded_by_user_id == user.id
    assert result.responded_at is not None
    
    # Verify request status updated
    db_session.expire_all()
    updated_request = db_session.query(InformationRequest).get(request.id)
    assert updated_request.status == InformationRequestStatus.RESPONDED.value


def test_record_response_request_not_found(db_session: Session):
    """Test recording response fails if request doesn't exist."""
    user = User(username="analyst", full_name="Test User", role=UserRole.AML_ANALYST.value, is_active=True, password_hash="hashed", permissions_json="{}")
    db_session.add(user)
    db_session.commit()
    
    service = InvestigationService(db_session)
    
    with pytest.raises(NotFoundError, match="Information request 999 not found"):
        service.record_response(
            request_id=999,
            response_text="Response",
            actor_user=user
        )


def test_record_response_request_not_open(db_session: Session):
    """Test recording response fails if request is not open."""
    # Setup
    customer = Customer(
        customer_number="CUST-004",
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
    db_session.commit()
    
    user = User(username="analyst", full_name="Test User", role=UserRole.AML_ANALYST.value, is_active=True, password_hash="hashed", permissions_json="{}")
    db_session.add(user)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-004",
        title="Test Case",
        customer_id=customer.id,
        state=CaseState.INFORMATION_REQUESTED.value,
        priority="MEDIUM",
        created_by_user_id=user.id,
        version=1
    )
    db_session.add(case)
    db_session.flush()
    
    request = InformationRequest(
        case_id=case.id,
        requested_what="Documents",
        reason="Verification",
        due_date=datetime.utcnow() + timedelta(days=7),
        status=InformationRequestStatus.CANCELLED.value,
        requested_by_user_id=user.id,
        version=1
    )
    db_session.add(request)
    db_session.commit()
    
    service = InvestigationService(db_session)
    
    with pytest.raises(DomainValidationError, match="Cannot respond to information request"):
        service.record_response(
            request_id=request.id,
            response_text="Response",
            actor_user=user
        )


def test_record_response_already_responded(db_session: Session):
    """Test recording response fails if request already has a response."""
    # Setup
    customer = Customer(
        customer_number="CUST-005",
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
    
    user = User(username="analyst", full_name="Test User", role=UserRole.AML_ANALYST.value, is_active=True, password_hash="hashed", permissions_json="{}")
    db_session.add(user)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-005",
        title="Test Case",
        customer_id=customer.id,
        state=CaseState.INFORMATION_REQUESTED.value,
        priority="MEDIUM",
        created_by_user_id=user.id,
        version=1
    )
    db_session.add(case)
    db_session.commit()
    
    # Create request and response
    service = InvestigationService(db_session)
    due_date = datetime.utcnow() + timedelta(days=7)
    request = service.request_information(
        case_id=case.id,
        requested_what="Documents",
        reason="Verification",
        due_date=due_date,
        actor_user=user
    )
    
    # Record first response
    service.record_response(
        request_id=request.id,
        response_text="First response",
        actor_user=user
    )
    
    # Try to record second response
    with pytest.raises(DomainValidationError, match="Cannot respond to information request with status RESPONDED"):
        service.record_response(
            request_id=request.id,
            response_text="Second response",
            actor_user=user
        )
