"""Unit tests for TransactionService."""
from datetime import datetime
from decimal import Decimal
import pytest
from sqlalchemy.orm import Session
from app.transaction.service import TransactionService
from app.transaction.schemas import TransactionIngestRequest
from app.customer.models import Customer, Account, CustomerRiskProfile
from app.common.enums import TransactionType, AccountStatus
from app.common.errors import NotFoundError


@pytest.fixture
def customer(db_session: Session):
    """Create a test customer."""
    customer = Customer(
        customer_number="CUST001",
        full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test"
    )
    db_session.add(customer)
    db_session.flush()
    
    # Add risk profile (required for screening context)
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level="LOW",
        base_score=25,
        last_reviewed_at=datetime.utcnow()
    )
    db_session.add(risk_profile)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def account(db_session: Session, customer):
    """Create a test account."""
    account = Account(
        account_number="ACC001",
        customer_id=customer.id,
        status=AccountStatus.ACTIVE.value,
        opened_at=datetime.utcnow(),
        current_balance=Decimal("10000.00"),
        currency="INR"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


def test_ingest_transaction_success(db_session: Session, account, all_rules_setup):
    """Test successful transaction ingestion."""
    service = TransactionService(db_session)
    
    request = TransactionIngestRequest(
        transaction_reference="TXN001",
        account_id=account.id,
        amount=Decimal("5000.00"),
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="IN",
        destination_country="US",
        timestamp=datetime.utcnow()
    )
    
    response = service.ingest_transaction(request, "test-correlation-id")
    
    assert response.id > 0
    assert response.transaction_reference == "TXN001"
    assert response.account_id == account.id
    assert response.amount == "5000.00"
    assert response.currency == "INR"
    assert response.transaction_type == TransactionType.TRANSFER.value
    assert response.origin_country == "IN"
    assert response.destination_country == "US"
    assert response.matched_rules_count >= 0  # May have dormancy spike match
    assert response.correlation_id == "test-correlation-id"
    assert len(response.evaluation_results) == 8  # All 8 rules evaluated


def test_ingest_transaction_with_optional_fields(db_session: Session, account, all_rules_setup):
    """Test transaction ingestion with optional counterparty fields."""
    service = TransactionService(db_session)
    
    request = TransactionIngestRequest(
        transaction_reference="TXN002",
        account_id=account.id,
        amount=Decimal("2500.00"),
        currency="INR",
        transaction_type=TransactionType.PAYMENT.value,
        origin_country="IN",
        destination_country="GB",
        counterparty_name="ABC Corp",
        counterparty_account="GB123456",
        timestamp=datetime.utcnow()
    )
    
    response = service.ingest_transaction(request, "test-correlation-id-2")
    
    assert response.id > 0
    assert response.transaction_reference == "TXN002"


def test_ingest_transaction_account_not_found(db_session: Session):
    """Test transaction ingestion with non-existent account."""
    service = TransactionService(db_session)
    
    request = TransactionIngestRequest(
        transaction_reference="TXN003",
        account_id=99999,  # non-existent
        amount=Decimal("1000.00"),
        currency="INR",
        transaction_type=TransactionType.DEPOSIT.value,
        origin_country="IN",
        destination_country="IN",
        timestamp=datetime.utcnow()
    )
    
    with pytest.raises(NotFoundError, match="Account not found"):
        service.ingest_transaction(request, "test-correlation-id-3")


def test_get_transaction_detail_success(db_session: Session, account, all_rules_setup):
    """Test successful transaction detail retrieval."""
    service = TransactionService(db_session)
    
    # First create a transaction
    request = TransactionIngestRequest(
        transaction_reference="TXN004",
        account_id=account.id,
        amount=Decimal("7500.50"),
        currency="INR",
        transaction_type=TransactionType.WITHDRAWAL.value,
        origin_country="IN",
        destination_country="IN",
        counterparty_name="Self",
        counterparty_account="ACC002",
        timestamp=datetime.utcnow()
    )
    
    ingest_response = service.ingest_transaction(request, "test-correlation-id-4")
    
    # Now retrieve it
    detail_response = service.get_transaction_detail(ingest_response.id)
    
    assert detail_response.id == ingest_response.id
    assert detail_response.transaction_reference == "TXN004"
    assert detail_response.account_id == account.id
    assert detail_response.amount == "7500.50"
    assert detail_response.currency == "INR"
    assert detail_response.transaction_type == TransactionType.WITHDRAWAL.value
    assert detail_response.origin_country == "IN"
    assert detail_response.destination_country == "IN"
    assert detail_response.counterparty_name == "Self"
    assert detail_response.counterparty_account == "ACC002"
    assert detail_response.matched_rules_count >= 0  # May have matches
    assert detail_response.correlation_id == "test-correlation-id-4"
    assert len(detail_response.evaluation_results) == 8  # All 8 rules evaluated


def test_get_transaction_detail_not_found(db_session: Session):
    """Test transaction detail retrieval for non-existent transaction."""
    service = TransactionService(db_session)
    
    with pytest.raises(NotFoundError, match="Transaction not found"):
        service.get_transaction_detail(99999)


def test_transaction_preserves_original_values(db_session: Session, account, all_rules_setup):
    """Test that transaction intake preserves original values without conversion."""
    service = TransactionService(db_session)
    
    original_timestamp = datetime(2024, 1, 15, 10, 30, 45)
    
    request = TransactionIngestRequest(
        transaction_reference="TXN005",
        account_id=account.id,
        amount=Decimal("12345.67"),
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="IN",
        destination_country="AE",
        timestamp=original_timestamp
    )
    
    response = service.ingest_transaction(request, "test-correlation-id-5")
    
    # Verify exact preservation
    assert response.amount == "12345.67"
    assert response.currency == "INR"
    assert response.timestamp == original_timestamp
    assert response.origin_country == "IN"
    assert response.destination_country == "AE"
