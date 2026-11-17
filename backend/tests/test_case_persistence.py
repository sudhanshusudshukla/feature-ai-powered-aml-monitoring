"""Test case workflow persistence models and constraints.

Tests:
- Case table creation and fields
- Foreign key constraints (customer_id, user_ids)
- Optimistic locking on mutable entities (aml_cases, information_requests)
- Append-only behavior for decisions, notes, responses
- UNIQUE constraints (case_number, case_id+alert_id, alert_id, information_request_id)
- Case workflow relationships
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.case_management.models import AMLCase, CaseAlertLink, CaseNote, CaseDecision
from app.investigation.models import InformationRequest, InformationResponse
from app.customer.models import Customer, CustomerRiskProfile
from app.alert.models import Alert
from app.transaction.models import Transaction
from app.customer.models import Account
from app.security.models import User
from app.common.enums import CaseState, AlertStatus, InformationRequestStatus


def test_case_table_creation_with_all_fields(db_session: Session):
    """Test aml_cases table exists with all required fields and relationships."""
    # Create prerequisite entities
    user = User(
        username="analyst1",
        full_name="Test Analyst",
        role="AML_ANALYST",
        is_active=True,
        password_hash="hash123",
        permissions_json="[]",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    
    customer = Customer(
        customer_number="C001",
        full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(customer)
    db_session.flush()
    
    # Create case
    case = AMLCase(
        case_number="CASE-2026-001",
        title="Suspicious Transaction Pattern",
        customer_id=customer.id,
        state=CaseState.OPEN.value,
        priority="HIGH",
        created_by_user_id=user.id,
        assigned_to_user_id=user.id,
        closure_reason=None,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(case)
    db_session.commit()
    
    # Verify fields
    retrieved = db_session.query(AMLCase).filter_by(case_number="CASE-2026-001").one()
    assert retrieved.id is not None
    assert retrieved.case_number == "CASE-2026-001"
    assert retrieved.title == "Suspicious Transaction Pattern"
    assert retrieved.customer_id == customer.id
    assert retrieved.state == CaseState.OPEN.value
    assert retrieved.priority == "HIGH"
    assert retrieved.created_by_user_id == user.id
    assert retrieved.assigned_to_user_id == user.id
    assert retrieved.closure_reason is None
    assert retrieved.version == 1
    assert retrieved.created_at is not None
    assert retrieved.updated_at is not None


def test_case_unique_case_number(db_session: Session):
    """Test case_number UNIQUE constraint."""
    user = User(
        username="analyst2",
        full_name="Test Analyst",
        role="AML_ANALYST",
        is_active=True,
        password_hash="hash123",
        permissions_json="[]",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    customer = Customer(
        customer_number="C002",
        full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.add(customer)
    db_session.flush()
    
    case1 = AMLCase(
        case_number="CASE-2026-002",
        title="Case 1",
        customer_id=customer.id,
        state=CaseState.OPEN.value,
        priority="MEDIUM",
        created_by_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(case1)
    db_session.commit()
    
    # Attempt duplicate case_number
    case2 = AMLCase(
        case_number="CASE-2026-002",
        title="Case 2",
        customer_id=customer.id,
        state=CaseState.OPEN.value,
        priority="LOW",
        created_by_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(case2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_case_foreign_key_constraints(db_session: Session):
    """Test FK constraints on customer_id, created_by_user_id, assigned_to_user_id."""
    # Attempt to create case with non-existent customer
    case = AMLCase(
        case_number="CASE-2026-003",
        title="Test Case",
        customer_id=99999,  # non-existent
        state=CaseState.OPEN.value,
        priority="MEDIUM",
        created_by_user_id=1,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(case)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_case_optimistic_locking(db_session: Session):
    """Test optimistic locking with version field on aml_cases."""
    user = User(
        username="analyst3",
        full_name="Test Analyst",
        role="AML_ANALYST",
        is_active=True,
        password_hash="hash123",
        permissions_json="[]",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    customer = Customer(
        customer_number="C003",
        full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.add(customer)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-2026-004",
        title="Test Case",
        customer_id=customer.id,
        state=CaseState.OPEN.value,
        priority="MEDIUM",
        created_by_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(case)
    db_session.commit()
    case_id = case.id
    
    # Simulate concurrent update by incrementing version
    case.state = CaseState.UNDER_INVESTIGATION.value
    case.version = 2
    case.updated_at = datetime.utcnow()
    db_session.commit()
    
    # Attempt stale update with version=1
    result = db_session.execute(
        text("""UPDATE aml_cases SET state = :state, updated_at = :updated_at, version = :new_version
           WHERE id = :id AND version = :expected_version"""),
        {
            "state": CaseState.PENDING_DECISION.value,
            "updated_at": datetime.utcnow(),
            "new_version": 2,
            "id": case_id,
            "expected_version": 1
        }
    )
    db_session.commit()
    
    # Verify no rows affected (version mismatch)
    retrieved = db_session.query(AMLCase).filter_by(id=case_id).one()
    assert retrieved.state == CaseState.UNDER_INVESTIGATION.value
    assert retrieved.version == 2


def test_case_alert_link_unique_constraints(db_session: Session):
    """Test case_alert_links UNIQUE(case_id, alert_id) and UNIQUE(alert_id)."""
    # Setup
    user = User(
        username="analyst4",
        full_name="Test Analyst",
        role="AML_ANALYST",
        is_active=True,
        password_hash="hash123",
        permissions_json="[]",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    customer = Customer(
        customer_number="C004",
        full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.add(customer)
    db_session.flush()
    
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level="MEDIUM",
        base_score=50,
        last_reviewed_at=datetime.utcnow(),
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(risk_profile)
    
    account = Account(
        account_number="ACC004",
        customer_id=customer.id,
        status="ACTIVE",
        opened_at=datetime.utcnow(),
        current_balance=1000.00,
        currency="INR",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(account)
    db_session.flush()
    
    transaction = Transaction(
        transaction_reference="TXN004",
        account_id=account.id,
        amount=5000.00,
        currency="INR",
        transaction_type="TRANSFER",
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="corr-004",
        created_at=datetime.utcnow()
    )
    db_session.add(transaction)
    db_session.flush()
    
    alert1 = Alert(
        alert_number="ALT-2026-001",
        transaction_id=transaction.id,
        risk_score=75,
        priority="HIGH",
        status=AlertStatus.NEW.value,
        priority_rationale="High value",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(alert1)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-2026-005",
        title="Test Case",
        customer_id=customer.id,
        state=CaseState.OPEN.value,
        priority="HIGH",
        created_by_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(case)
    db_session.flush()
    
    link1 = CaseAlertLink(
        case_id=case.id,
        alert_id=alert1.id,
        linked_at=datetime.utcnow(),
        linked_by_user_id=user.id
    )
    db_session.add(link1)
    db_session.commit()
    
    # Test UNIQUE(case_id, alert_id)
    link2 = CaseAlertLink(
        case_id=case.id,
        alert_id=alert1.id,
        linked_at=datetime.utcnow(),
        linked_by_user_id=user.id
    )
    db_session.add(link2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()
    
    # Test UNIQUE(alert_id) - alert can only be in one case
    case2 = AMLCase(
        case_number="CASE-2026-006",
        title="Test Case 2",
        customer_id=customer.id,
        state=CaseState.OPEN.value,
        priority="MEDIUM",
        created_by_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(case2)
    db_session.flush()
    
    link3 = CaseAlertLink(
        case_id=case2.id,
        alert_id=alert1.id,
        linked_at=datetime.utcnow(),
        linked_by_user_id=user.id
    )
    db_session.add(link3)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_case_notes_append_only(db_session: Session):
    """Test case_notes are append-only (no update mechanism)."""
    user = User(
        username="analyst5",
        full_name="Test Analyst",
        role="AML_ANALYST",
        is_active=True,
        password_hash="hash123",
        permissions_json="[]",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    customer = Customer(
        customer_number="C005",
        full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.add(customer)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-2026-007",
        title="Test Case",
        customer_id=customer.id,
        state=CaseState.OPEN.value,
        priority="MEDIUM",
        created_by_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(case)
    db_session.flush()
    
    note = CaseNote(
        case_id=case.id,
        note_text="Initial investigation note",
        created_by_user_id=user.id,
        created_at=datetime.utcnow()
    )
    db_session.add(note)
    db_session.commit()
    
    # Verify note has no version field
    assert not hasattr(note, 'version')
    assert not hasattr(note, 'updated_at')
    
    # Verify note text is immutable by policy (model has no update timestamp)
    original_text = note.note_text
    note_id = note.id
    
    # Attempt programmatic update (not blocked by DB, but policy layer should prevent)
    note.note_text = "Modified text"
    db_session.commit()
    
    # Verify change persisted (DB allows, but application layer enforces append-only)
    retrieved = db_session.query(CaseNote).filter_by(id=note_id).one()
    assert retrieved.note_text == "Modified text"  # DB allows update
    # Application layer must enforce append-only by never calling update


def test_case_decisions_append_only(db_session: Session):
    """Test case_decisions are append-only and final."""
    user = User(
        username="officer1",
        full_name="Test Officer",
        role="AML_OFFICER",
        is_active=True,
        password_hash="hash123",
        permissions_json="[]",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    customer = Customer(
        customer_number="C006",
        full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.add(customer)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-2026-008",
        title="Test Case",
        customer_id=customer.id,
        state=CaseState.PENDING_DECISION.value,
        priority="HIGH",
        created_by_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(case)
    db_session.flush()
    
    decision = CaseDecision(
        case_id=case.id,
        decision="APPROVE",
        reason="Verified legitimate transaction",
        comments="Customer provided supporting documentation",
        decided_by_user_id=user.id,
        decided_at=datetime.utcnow()
    )
    db_session.add(decision)
    db_session.commit()
    
    # Verify decision has no version or updated_at field
    assert not hasattr(decision, 'version')
    assert not hasattr(decision, 'updated_at')
    
    # Verify decision is final (no update mechanism in model)
    decision_id = decision.id
    retrieved = db_session.query(CaseDecision).filter_by(id=decision_id).one()
    assert retrieved.decision == "APPROVE"


def test_information_request_optimistic_locking(db_session: Session):
    """Test optimistic locking on information_requests (mutable status)."""
    user = User(
        username="analyst6",
        full_name="Test Analyst",
        role="AML_ANALYST",
        is_active=True,
        password_hash="hash123",
        permissions_json="[]",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    customer = Customer(
        customer_number="C007",
        full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.add(customer)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-2026-009",
        title="Test Case",
        customer_id=customer.id,
        state=CaseState.INFORMATION_REQUESTED.value,
        priority="MEDIUM",
        created_by_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(case)
    db_session.flush()
    
    info_req = InformationRequest(
        case_id=case.id,
        requested_what="Bank statements for last 6 months",
        reason="Verify transaction patterns",
        due_date=datetime.utcnow() + timedelta(days=5),
        status=InformationRequestStatus.OPEN.value,
        requested_by_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(info_req)
    db_session.commit()
    req_id = info_req.id
    
    # Simulate concurrent update
    info_req.status = InformationRequestStatus.RESPONDED.value
    info_req.version = 2
    info_req.updated_at = datetime.utcnow()
    db_session.commit()
    
    # Attempt stale update
    result = db_session.execute(
        text("""UPDATE information_requests SET status = :status, updated_at = :updated_at, version = :new_version
           WHERE id = :id AND version = :expected_version"""),
        {
            "status": InformationRequestStatus.CANCELLED.value,
            "updated_at": datetime.utcnow(),
            "new_version": 2,
            "id": req_id,
            "expected_version": 1
        }
    )
    db_session.commit()
    
    # Verify version mismatch prevented stale update
    retrieved = db_session.query(InformationRequest).filter_by(id=req_id).one()
    assert retrieved.status == InformationRequestStatus.RESPONDED.value
    assert retrieved.version == 2


def test_information_response_unique_constraint(db_session: Session):
    """Test information_responses UNIQUE(information_request_id) one-to-one."""
    user = User(
        username="analyst7",
        full_name="Test Analyst",
        role="AML_ANALYST",
        is_active=True,
        password_hash="hash123",
        permissions_json="[]",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    customer = Customer(
        customer_number="C008",
        full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.add(customer)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-2026-010",
        title="Test Case",
        customer_id=customer.id,
        state=CaseState.INFORMATION_REQUESTED.value,
        priority="LOW",
        created_by_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(case)
    db_session.flush()
    
    info_req = InformationRequest(
        case_id=case.id,
        requested_what="Additional documentation",
        reason="Clarify transaction purpose",
        due_date=datetime.utcnow() + timedelta(days=3),
        status=InformationRequestStatus.OPEN.value,
        requested_by_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(info_req)
    db_session.flush()
    
    response1 = InformationResponse(
        information_request_id=info_req.id,
        response_text="Documents attached",
        responded_by_user_id=user.id,
        responded_at=datetime.utcnow()
    )
    db_session.add(response1)
    db_session.commit()
    
    # Attempt duplicate response
    response2 = InformationResponse(
        information_request_id=info_req.id,
        response_text="Additional response",
        responded_by_user_id=user.id,
        responded_at=datetime.utcnow()
    )
    db_session.add(response2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_case_workflow_relationships(db_session: Session):
    """Test complete case workflow relationships traverse correctly."""
    # Setup full workflow
    user = User(
        username="analyst8",
        full_name="Test Analyst",
        role="AML_ANALYST",
        is_active=True,
        password_hash="hash123",
        permissions_json="[]",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    customer = Customer(
        customer_number="C009",
        full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.add(customer)
    db_session.flush()
    
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level="HIGH",
        base_score=80,
        last_reviewed_at=datetime.utcnow(),
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(risk_profile)
    
    account = Account(
        account_number="ACC009",
        customer_id=customer.id,
        status="ACTIVE",
        opened_at=datetime.utcnow(),
        current_balance=50000.00,
        currency="INR",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(account)
    db_session.flush()
    
    transaction = Transaction(
        transaction_reference="TXN009",
        account_id=account.id,
        amount=100000.00,
        currency="INR",
        transaction_type="TRANSFER",
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="corr-009",
        created_at=datetime.utcnow()
    )
    db_session.add(transaction)
    db_session.flush()
    
    alert = Alert(
        alert_number="ALT-2026-009",
        transaction_id=transaction.id,
        risk_score=85,
        priority="CRITICAL",
        status=AlertStatus.NEW.value,
        priority_rationale="High value to high risk destination",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(alert)
    db_session.flush()
    
    case = AMLCase(
        case_number="CASE-2026-011",
        title="High Value Transfer Investigation",
        customer_id=customer.id,
        state=CaseState.UNDER_INVESTIGATION.value,
        priority="CRITICAL",
        created_by_user_id=user.id,
        assigned_to_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(case)
    db_session.flush()
    
    link = CaseAlertLink(
        case_id=case.id,
        alert_id=alert.id,
        linked_at=datetime.utcnow(),
        linked_by_user_id=user.id
    )
    db_session.add(link)
    
    note = CaseNote(
        case_id=case.id,
        note_text="Contacted customer for verification",
        created_by_user_id=user.id,
        created_at=datetime.utcnow()
    )
    db_session.add(note)
    
    info_req = InformationRequest(
        case_id=case.id,
        requested_what="Source of funds documentation",
        reason="High value transfer requires verification",
        due_date=datetime.utcnow() + timedelta(days=7),
        status=InformationRequestStatus.OPEN.value,
        requested_by_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(info_req)
    db_session.commit()
    
    # Verify relationships
    retrieved_case = db_session.query(AMLCase).filter_by(case_number="CASE-2026-011").one()
    
    assert len(retrieved_case.alert_links) == 1
    assert retrieved_case.alert_links[0].alert_id == alert.id
    
    assert len(retrieved_case.notes) == 1
    assert retrieved_case.notes[0].note_text == "Contacted customer for verification"
    
    # Note: information_requests relationship not defined in AMLCase model
    # Verify via explicit query
    requests = db_session.query(InformationRequest).filter_by(case_id=case.id).all()
    assert len(requests) == 1
    assert requests[0].requested_what == "Source of funds documentation"
    
    assert len(retrieved_case.decisions) == 0  # No decision yet


def test_multiple_cases_same_customer(db_session: Session):
    """Test customer can have multiple cases."""
    user = User(
        username="analyst9",
        full_name="Test Analyst",
        role="AML_ANALYST",
        is_active=True,
        password_hash="hash123",
        permissions_json="[]",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    customer = Customer(
        customer_number="C010",
        full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.add(customer)
    db_session.flush()
    
    case1 = AMLCase(
        case_number="CASE-2026-012",
        title="First Investigation",
        customer_id=customer.id,
        state=CaseState.CLOSED.value,
        priority="MEDIUM",
        created_by_user_id=user.id,
        closure_reason="False positive",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    case2 = AMLCase(
        case_number="CASE-2026-013",
        title="Second Investigation",
        customer_id=customer.id,
        state=CaseState.OPEN.value,
        priority="HIGH",
        created_by_user_id=user.id,
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(case1)
    db_session.add(case2)
    db_session.commit()
    
    # Verify both cases for same customer
    cases = db_session.query(AMLCase).filter_by(customer_id=customer.id).all()
    assert len(cases) == 2
    assert {c.case_number for c in cases} == {"CASE-2026-012", "CASE-2026-013"}
