"""Unit tests for customer service and account context retrieval."""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.customer.models import Customer, CustomerRiskProfile, Account
from app.customer.service import CustomerService
from app.customer.repository import AccountRepository
from app.transaction.models import Transaction
from app.alert.models import Alert
from app.common.errors import NotFoundError


def test_get_customer_success(db_session):
    """Test retrieving an existing customer."""
    # Create customer with risk profile
    customer = Customer(
        customer_number="CUST001",
        full_name="John Doe",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test"
    )
    db_session.add(customer)
    db_session.flush()
    
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level="LOW",
        base_score=25,
        last_reviewed_at=datetime.utcnow()
    )
    db_session.add(risk_profile)
    db_session.commit()
    
    # Retrieve customer
    service = CustomerService(db_session)
    result = service.get_customer(customer.id)
    
    assert result.id == customer.id
    assert result.customer_number == "CUST001"
    assert result.full_name == "John Doe"
    assert result.pep_status is False
    assert result.sanctioned_status is False


def test_get_customer_not_found(db_session):
    """Test retrieving non-existent customer raises NotFoundError."""
    service = CustomerService(db_session)
    
    with pytest.raises(NotFoundError, match="Customer not found"):
        service.get_customer(99999)


def test_get_account_success(db_session):
    """Test retrieving an existing account."""
    # Create customer
    customer = Customer(
        customer_number="CUST001",
        full_name="John Doe",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test"
    )
    db_session.add(customer)
    db_session.flush()
    
    # Create account
    account = Account(
        account_number="ACC001",
        customer_id=customer.id,
        status="ACTIVE",
        opened_at=datetime.utcnow(),
        current_balance=Decimal("50000.00"),
        currency="INR"
    )
    db_session.add(account)
    db_session.commit()
    
    # Retrieve account
    service = CustomerService(db_session)
    result = service.get_account(account.id)
    
    assert result.id == account.id
    assert result.account_number == "ACC001"
    assert result.customer_id == customer.id
    assert result.status == "ACTIVE"
    assert result.current_balance == "50000.00"


def test_get_account_not_found(db_session):
    """Test retrieving non-existent account raises NotFoundError."""
    service = CustomerService(db_session)
    
    with pytest.raises(NotFoundError, match="Account not found"):
        service.get_account(99999)


def test_get_screening_context_success(db_session):
    """Test retrieving complete screening context with all data."""
    # Create customer with risk profile
    customer = Customer(
        customer_number="CUST001",
        full_name="Jane Smith",
        residency_country="IN",
        pep_status=True,
        sanctioned_status=False,
        synthetic_source="test"
    )
    db_session.add(customer)
    db_session.flush()
    
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level="HIGH",
        base_score=75,
        last_reviewed_at=datetime.utcnow()
    )
    db_session.add(risk_profile)
    db_session.flush()
    
    # Create account
    account = Account(
        account_number="ACC001",
        customer_id=customer.id,
        status="ACTIVE",
        opened_at=datetime.utcnow(),
        current_balance=Decimal("100000.00"),
        currency="INR"
    )
    db_session.add(account)
    db_session.commit()
    
    # Retrieve screening context
    service = CustomerService(db_session)
    context = service.get_screening_context(account.id, "test-correlation-id")
    
    # Verify account fields
    assert context.account_id == account.id
    assert context.account_number == "ACC001"
    assert context.account_status == "ACTIVE"
    
    # Verify customer fields
    assert context.customer_id == customer.id
    assert context.customer_number == "CUST001"
    assert context.customer_full_name == "Jane Smith"
    assert context.residency_country == "IN"
    assert context.pep_status is True
    assert context.sanctioned_status is False
    
    # Verify risk profile fields
    assert context.risk_level == "HIGH"
    assert context.risk_base_score == 75
    
    # Verify correlation ID
    assert context.correlation_id == "test-correlation-id"
    
    # Verify historical metrics exist
    assert context.historical_metrics is not None
    assert context.historical_metrics.rolling_24h_total == Decimal("0")
    assert context.historical_metrics.rolling_7d_count == 0


def test_get_screening_context_account_not_found(db_session):
    """Test screening context retrieval fails cleanly when account missing."""
    repository = AccountRepository(db_session)
    
    with pytest.raises(NotFoundError, match="Account not found"):
        repository.get_screening_context(99999, "test-correlation-id")


def test_get_screening_context_missing_risk_profile(db_session):
    """Test screening context retrieval fails when risk profile missing."""
    # Create customer WITHOUT risk profile
    customer = Customer(
        customer_number="CUST001",
        full_name="John Doe",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test"
    )
    db_session.add(customer)
    db_session.flush()
    
    # Create account
    account = Account(
        account_number="ACC001",
        customer_id=customer.id,
        status="ACTIVE",
        opened_at=datetime.utcnow(),
        current_balance=Decimal("50000.00"),
        currency="INR"
    )
    db_session.add(account)
    db_session.commit()
    
    repository = AccountRepository(db_session)
    
    with pytest.raises(NotFoundError, match="Risk profile not found"):
        repository.get_screening_context(account.id, "test-correlation-id")


def test_transaction_window_metrics_empty_history(db_session):
    """Test historical metrics calculation with no prior transactions."""
    # Create customer and account
    customer = Customer(
        customer_number="CUST001",
        full_name="John Doe",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test"
    )
    db_session.add(customer)
    db_session.flush()
    
    account = Account(
        account_number="ACC001",
        customer_id=customer.id,
        status="ACTIVE",
        opened_at=datetime.utcnow(),
        current_balance=Decimal("50000.00"),
        currency="INR"
    )
    db_session.add(account)
    db_session.commit()
    
    # Calculate metrics with no transactions
    repository = AccountRepository(db_session)
    metrics = repository.get_transaction_window_metrics(
        account_id=account.id,
        customer_id=customer.id,
        as_of=datetime.utcnow()
    )
    
    assert metrics.rolling_24h_total == Decimal("0")
    assert metrics.rolling_7d_count == 0
    assert metrics.rolling_30m_count == 0
    assert metrics.rolling_30m_total == Decimal("0")
    assert metrics.rolling_90d_average == Decimal("0")
    assert metrics.cross_border_count == 0
    assert metrics.high_risk_country_flag is False
    assert metrics.prior_alert_count == 0


def test_transaction_window_metrics_with_history(db_session):
    """Test historical metrics calculation with transaction history."""
    now = datetime.utcnow()
    
    # Create customer and account
    customer = Customer(
        customer_number="CUST001",
        full_name="John Doe",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test"
    )
    db_session.add(customer)
    db_session.flush()
    
    account = Account(
        account_number="ACC001",
        customer_id=customer.id,
        status="ACTIVE",
        opened_at=datetime.utcnow(),
        current_balance=Decimal("50000.00"),
        currency="INR"
    )
    db_session.add(account)
    db_session.flush()
    
    # Create transactions in different time windows
    # Transaction 1: 12 hours ago (in 24h window)
    tx1 = Transaction(
        transaction_reference="TXN001",
        account_id=account.id,
        amount=Decimal("10000.00"),
        currency="INR",
        transaction_type="TRANSFER",
        origin_country="US",
        destination_country="IN",
        transaction_timestamp=now - timedelta(hours=12),
        correlation_id="corr-001"
    )
    db_session.add(tx1)
    
    # Transaction 2: 3 days ago (in 7d window)
    tx2 = Transaction(
        transaction_reference="TXN002",
        account_id=account.id,
        amount=Decimal("5000.00"),
        currency="INR",
        transaction_type="TRANSFER",
        origin_country="US",
        destination_country="US",
        transaction_timestamp=now - timedelta(days=3),
        correlation_id="corr-002"
    )
    db_session.add(tx2)
    
    # Transaction 3: 15 minutes ago (in 30m window)
    tx3 = Transaction(
        transaction_reference="TXN003",
        account_id=account.id,
        amount=Decimal("2000.00"),
        currency="INR",
        transaction_type="DEPOSIT",
        origin_country="IN",
        destination_country="IN",
        transaction_timestamp=now - timedelta(minutes=15),
        correlation_id="corr-003"
    )
    db_session.add(tx3)
    
    # Transaction 4: 45 days ago (in 90d window)
    tx4 = Transaction(
        transaction_reference="TXN004",
        account_id=account.id,
        amount=Decimal("8000.00"),
        currency="INR",
        transaction_type="WITHDRAWAL",
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=now - timedelta(days=45),
        correlation_id="corr-004"
    )
    db_session.add(tx4)
    
    db_session.commit()
    
    # Calculate metrics
    repository = AccountRepository(db_session)
    metrics = repository.get_transaction_window_metrics(
        account_id=account.id,
        customer_id=customer.id,
        as_of=now
    )
    
    # Verify 24h window: tx1 + tx3 = 12000
    assert metrics.rolling_24h_total == Decimal("12000.00")
    
    # Verify 7d window: tx1 + tx2 + tx3 = 3 transactions
    assert metrics.rolling_7d_count == 3
    
    # Verify 30m window: tx3 only
    assert metrics.rolling_30m_count == 1
    assert metrics.rolling_30m_total == Decimal("2000.00")
    
    # Verify 90d average: all 4 transactions average = (10000 + 5000 + 2000 + 8000) / 4 = 6250
    assert metrics.rolling_90d_average == Decimal("6250.00")
    
    # Verify cross-border: tx1 (US->IN) and tx4 (IN->US) = 2
    assert metrics.cross_border_count == 2
    
    # Verify no alerts yet
    assert metrics.prior_alert_count == 0


def test_transaction_window_metrics_with_alerts(db_session):
    """Test historical metrics include prior alert count."""
    now = datetime.utcnow()
    
    # Create customer and account
    customer = Customer(
        customer_number="CUST001",
        full_name="John Doe",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test"
    )
    db_session.add(customer)
    db_session.flush()
    
    account = Account(
        account_number="ACC001",
        customer_id=customer.id,
        status="ACTIVE",
        opened_at=datetime.utcnow(),
        current_balance=Decimal("50000.00"),
        currency="INR"
    )
    db_session.add(account)
    db_session.flush()
    
    # Create transactions with alerts
    tx1 = Transaction(
        transaction_reference="TXN001",
        account_id=account.id,
        amount=Decimal("10000.00"),
        currency="INR",
        transaction_type="TRANSFER",
        origin_country="US",
        destination_country="IN",
        transaction_timestamp=now - timedelta(hours=12),
        correlation_id="corr-001"
    )
    db_session.add(tx1)
    db_session.flush()
    
    alert1 = Alert(
        alert_number="ALT001",
        transaction_id=tx1.id,
        risk_score=75,
        priority="HIGH",
        status="NEW",
        priority_rationale="High value transaction"
    )
    db_session.add(alert1)
    
    tx2 = Transaction(
        transaction_reference="TXN002",
        account_id=account.id,
        amount=Decimal("15000.00"),
        currency="INR",
        transaction_type="TRANSFER",
        origin_country="US",
        destination_country="IN",
        transaction_timestamp=now - timedelta(days=2),
        correlation_id="corr-002"
    )
    db_session.add(tx2)
    db_session.flush()
    
    alert2 = Alert(
        alert_number="ALT002",
        transaction_id=tx2.id,
        risk_score=80,
        priority="CRITICAL",
        status="ASSIGNED",
        priority_rationale="Very high value transaction"
    )
    db_session.add(alert2)
    
    db_session.commit()
    
    # Calculate metrics
    repository = AccountRepository(db_session)
    metrics = repository.get_transaction_window_metrics(
        account_id=account.id,
        customer_id=customer.id,
        as_of=now
    )
    
    # Verify prior alert count
    assert metrics.prior_alert_count == 2
