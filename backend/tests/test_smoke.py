"""Smoke tests to verify basic system setup."""
import pytest
from sqlalchemy.orm import Session
from app.security.models import User
from app.customer.models import Customer, Account
from app.risk.models import CountryRisk
from datetime import datetime


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_database_connection(db_session: Session):
    """Test database connectivity by creating and querying a user."""
    # Create a user
    user = User(
        username="test_user",
        full_name="Test User",
        role="AML_ANALYST",
        is_active=True,
        password_hash="dummy_hash",
        permissions_json='["test.read"]',
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    db_session.commit()
    
    # Query the user
    retrieved = db_session.query(User).filter_by(username="test_user").first()
    assert retrieved is not None
    assert retrieved.full_name == "Test User"
    assert retrieved.role == "AML_ANALYST"


def test_foreign_key_relationship(db_session: Session):
    """Test foreign key relationships by creating customer and account."""
    # Create customer
    customer = Customer(
        customer_number="CUST001",
        full_name="Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(customer)
    db_session.commit()
    
    # Create account linked to customer
    account = Account(
        account_number="ACC001",
        customer_id=customer.id,
        status="ACTIVE",
        opened_at=datetime.utcnow(),
        current_balance=1000.00,
        currency="USD",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(account)
    db_session.commit()
    
    # Verify relationship
    retrieved_account = db_session.query(Account).filter_by(account_number="ACC001").first()
    assert retrieved_account is not None
    assert retrieved_account.customer_id == customer.id


def test_country_risk_insert(db_session: Session):
    """Test country risk reference data insertion."""
    country = CountryRisk(
        country_code="US",
        country_name="United States",
        is_high_risk=False,
        risk_rating="LOW",
        version=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(country)
    db_session.commit()
    
    retrieved = db_session.query(CountryRisk).filter_by(country_code="US").first()
    assert retrieved is not None
    assert retrieved.country_name == "United States"
    assert retrieved.is_high_risk is False
