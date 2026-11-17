"""Shared test fixtures for the AML backend test suite."""
import os
import tempfile
from pathlib import Path

# 1. Configuration BEFORE anything imports the app
_BACKEND = Path(__file__).resolve().parents[1]
for _seed in ("dev.env", ".env.example"):
    if (_BACKEND / _seed).is_file():
        for _line in (_BACKEND / _seed).read_text().splitlines():
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _value = _line.removeprefix("export ").split("=", 1)
                os.environ.setdefault(_key.strip(), _value.strip().strip("\"'"))
        break

_DB_FILE = Path(tempfile.mkdtemp()) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE.as_posix()}"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base, get_db
from app.main import app as fastapi_app

# Import all models to ensure they are registered
import app.security.models  # noqa: F401
import app.customer.models  # noqa: F401
import app.risk.models  # noqa: F401
import app.transaction.models  # noqa: F401
import app.rules.models  # noqa: F401
import app.alert.models  # noqa: F401
import app.case_management.models  # noqa: F401
import app.investigation.models  # noqa: F401
import app.audit.models  # noqa: F401

engine = create_engine(os.environ["DATABASE_URL"], connect_args={"check_same_thread": False})
TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(autouse=True)
def _fresh_schema():
    """Create fresh schema for each test."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session() -> Session:
    """Provide a database session for tests."""
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """Provide a test client with database override."""
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(fastapi_app) as test_client:
        yield test_client
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user with officer role."""
    import bcrypt
    from app.security.models import User
    from app.common.enums import UserRole
    
    password = "Officer-pass-1"
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    user = User(
        username="officer@example.com",
        password_hash=password_hash,
        full_name="Test Officer",
        role=UserRole.AML_OFFICER.value,
        permissions_json="{}",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_client(client, test_user):
    """Provide an authenticated test client."""
    # Login through the real login endpoint
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "officer@example.com", "password": "Officer-pass-1"}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    
    token = response.json().get("access_token")
    if token:
        client.headers["Authorization"] = f"Bearer {token}"
    
    return client


@pytest.fixture
def all_rules_setup(db_session):
    """Setup all 8 AML rules for testing."""
    import json
    from datetime import datetime
    from app.rules.models import DetectionRule, RuleVersion
    from app.common.enums import RuleSeverity
    
    rules_data = [
        ("AML-001", "High Value Transaction", {"threshold": 100000}),
        ("AML-002", "Transaction Velocity (Count)", {"threshold_7d_count": 10}),
        ("AML-003", "Transaction Velocity (Amount)", {"threshold_24h_total": 500000}),
        ("AML-004", "High Risk Geography", {}),
        ("AML-005", "Sanctioned or PEP Customer", {}),
        ("AML-006", "Structuring Pattern", {"count_threshold_30m": 5, "amount_below_threshold": 50000}),
        ("AML-007", "Dormancy Spike", {"spike_multiplier": 5.0}),
        ("AML-008", "Round Amount Pattern", {"min_round_amount": 10000}),
    ]
    
    for rule_code, name, params in rules_data:
        rule = DetectionRule(
            rule_code=rule_code,
            name=name,
            severity=RuleSeverity.MEDIUM.value,
            description="Test rule",
            is_active=True,
            version=1
        )
        db_session.add(rule)
        db_session.flush()
        
        rule_version = RuleVersion(
            rule_id=rule.id,
            version_number=1,
            parameters_json=json.dumps(params),
            effective_from=datetime.utcnow()
        )
        db_session.add(rule_version)
    
    db_session.commit()
    return True
