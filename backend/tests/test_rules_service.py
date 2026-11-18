"""Tests for rules service and evaluators."""
import json
from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.common.enums import (
    AccountStatus,
    RiskLevel,
    RuleOutcome,
    RuleSeverity,
    TransactionType,
)
from app.customer.models import Account, Customer, CustomerRiskProfile
from app.customer.schemas import HistoricalMetrics, ScreeningContext
from app.rules.models import DetectionRule, RuleVersion
from app.rules.service import RulesService
from app.transaction.models import Transaction


@pytest.fixture
def test_account(db_session):
    """Create a test account with customer and risk profile."""
    customer = Customer(
        customer_number="CUST-RULE-TEST",
        full_name="Rule Test Customer",
        residency_country="IN",
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
        account_number="ACC-RULE-TEST",
        customer_id=customer.id,
        status=AccountStatus.ACTIVE.value,
        opened_at=datetime.utcnow(),
        current_balance=Decimal("100000.00"),
        currency="INR",
        version=1
    )
    db_session.add(account)
    db_session.flush()
    return account


@pytest.fixture
def all_rules_setup(db_session):
    """Setup all 8 AML rules for testing."""
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


def test_high_value_transaction_match(db_session, test_account, all_rules_setup):
    """Test AML-001 high value transaction detection - match case."""
    
    # Setup transaction and context
    transaction = Transaction(
        transaction_reference="TX-HIGH-001",
        account_id=test_account.id,
        amount=Decimal("150000.00"),
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-001"
    )
    db_session.add(transaction)
    db_session.flush()
    
    context = ScreeningContext(
        account_id=test_account.id,
        account_number="ACC-001",
        account_status=AccountStatus.ACTIVE.value,
        customer_id=1,
        customer_number="CUST-001",
        customer_full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        risk_level=RiskLevel.LOW.value,
        risk_base_score=20,
        historical_metrics=HistoricalMetrics(
            rolling_24h_total=Decimal("0"),
            rolling_7d_count=0,
            rolling_30m_count=0,
            rolling_30m_total=Decimal("0"),
            rolling_90d_average=Decimal("0"),
            cross_border_count=0,
            high_risk_country_flag=False,
            prior_alert_count=0
        ),
        correlation_id="test-001"
    )
    
    # Evaluate
    service = RulesService(db_session)
    result = service.evaluate_all(transaction, context)
    
    # Assert - verify AML-001 matched
    assert result.any_match is True
    aml001_result = next(r for r in result.results if r.rule_code == "AML-001")
    assert aml001_result.outcome == RuleOutcome.MATCH.value
    assert aml001_result.score == 30


def test_high_value_transaction_pass(db_session, test_account, all_rules_setup):
    """Test AML-001 high value transaction detection - pass case."""
    transaction = Transaction(
        transaction_reference="TX-LOW-001",
        account_id=test_account.id,
        amount=Decimal("50000.00"),
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-002"
    )
    db_session.add(transaction)
    db_session.flush()
    
    context = ScreeningContext(
        account_id=test_account.id,
        account_number="ACC-001",
        account_status=AccountStatus.ACTIVE.value,
        customer_id=1,
        customer_number="CUST-001",
        customer_full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        risk_level=RiskLevel.LOW.value,
        risk_base_score=20,
        historical_metrics=HistoricalMetrics(
            rolling_24h_total=Decimal("0"),
            rolling_7d_count=0,
            rolling_30m_count=0,
            rolling_30m_total=Decimal("0"),
            rolling_90d_average=Decimal("0"),
            cross_border_count=0,
            high_risk_country_flag=False,
            prior_alert_count=0
        ),
        correlation_id="test-002"
    )
    
    service = RulesService(db_session)
    result = service.evaluate_all(transaction, context)
    
    # Verify AML-001 passed
    aml001_result = next(r for r in result.results if r.rule_code == "AML-001")
    assert aml001_result.outcome == RuleOutcome.PASS.value
    assert aml001_result.score == 0


def test_sanctioned_or_pep_match(db_session, test_account, all_rules_setup):
    """Test AML-005 sanctioned/PEP detection - match case."""
    transaction = Transaction(
        transaction_reference="TX-PEP-001",
        account_id=test_account.id,
        amount=Decimal("50000.00"),
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-003"
    )
    db_session.add(transaction)
    db_session.flush()
    
    context = ScreeningContext(
        account_id=test_account.id,
        account_number="ACC-001",
        account_status=AccountStatus.ACTIVE.value,
        customer_id=1,
        customer_number="CUST-001",
        customer_full_name="Test PEP",
        residency_country="IN",
        pep_status=True,  # PEP flagged
        sanctioned_status=False,
        risk_level=RiskLevel.HIGH.value,
        risk_base_score=75,
        historical_metrics=HistoricalMetrics(
            rolling_24h_total=Decimal("0"),
            rolling_7d_count=0,
            rolling_30m_count=0,
            rolling_30m_total=Decimal("0"),
            rolling_90d_average=Decimal("0"),
            cross_border_count=0,
            high_risk_country_flag=False,
            prior_alert_count=0
        ),
        correlation_id="test-003"
    )
    
    service = RulesService(db_session)
    result = service.evaluate_all(transaction, context)
    
    assert result.any_match is True
    aml005_result = next(r for r in result.results if r.rule_code == "AML-005")
    assert aml005_result.outcome == RuleOutcome.MATCH.value
    assert aml005_result.severity == RuleSeverity.CRITICAL.value
    assert aml005_result.score == 40


def test_velocity_count_match(db_session, test_account, all_rules_setup):
    """Test AML-002 velocity count - match case."""
    transaction = Transaction(
        transaction_reference="TX-VEL-001",
        account_id=test_account.id,
        amount=Decimal("10000.00"),
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-004"
    )
    db_session.add(transaction)
    db_session.flush()
    
    context = ScreeningContext(
        account_id=test_account.id,
        account_number="ACC-001",
        account_status=AccountStatus.ACTIVE.value,
        customer_id=1,
        customer_number="CUST-001",
        customer_full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        risk_level=RiskLevel.LOW.value,
        risk_base_score=20,
        historical_metrics=HistoricalMetrics(
            rolling_24h_total=Decimal("50000"),
            rolling_7d_count=12,  # Above threshold
            rolling_30m_count=0,
            rolling_30m_total=Decimal("0"),
            rolling_90d_average=Decimal("5000"),
            cross_border_count=2,
            high_risk_country_flag=False,
            prior_alert_count=0
        ),
        correlation_id="test-004"
    )
    
    service = RulesService(db_session)
    result = service.evaluate_all(transaction, context)
    
    aml002_result = next(r for r in result.results if r.rule_code == "AML-002")
    assert aml002_result.outcome == RuleOutcome.MATCH.value
    assert aml002_result.score == 20


def test_structuring_pattern_match(db_session, test_account, all_rules_setup):
    """Test AML-006 structuring pattern - match case."""
    transaction = Transaction(
        transaction_reference="TX-STRUCT-001",
        account_id=test_account.id,
        amount=Decimal("45000.00"),  # Below threshold
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-005"
    )
    db_session.add(transaction)
    db_session.flush()
    
    context = ScreeningContext(
        account_id=test_account.id,
        account_number="ACC-001",
        account_status=AccountStatus.ACTIVE.value,
        customer_id=1,
        customer_number="CUST-001",
        customer_full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        risk_level=RiskLevel.LOW.value,
        risk_base_score=20,
        historical_metrics=HistoricalMetrics(
            rolling_24h_total=Decimal("200000"),
            rolling_7d_count=8,
            rolling_30m_count=5,  # At threshold
            rolling_30m_total=Decimal("225000"),
            rolling_90d_average=Decimal("5000"),
            cross_border_count=0,
            high_risk_country_flag=False,
            prior_alert_count=0
        ),
        correlation_id="test-005"
    )
    
    service = RulesService(db_session)
    result = service.evaluate_all(transaction, context)
    
    aml006_result = next(r for r in result.results if r.rule_code == "AML-006")
    assert aml006_result.outcome == RuleOutcome.MATCH.value
    assert aml006_result.score == 35


def test_all_eight_rules_evaluated(db_session, test_account):
    """Test that all eight rules are evaluated."""
    # Setup all 8 rules
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
    
    transaction = Transaction(
        transaction_reference="TX-ALL-001",
        account_id=test_account.id,
        amount=Decimal("50000.00"),
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-006"
    )
    db_session.add(transaction)
    db_session.flush()
    
    context = ScreeningContext(
        account_id=test_account.id,
        account_number="ACC-001",
        account_status=AccountStatus.ACTIVE.value,
        customer_id=1,
        customer_number="CUST-001",
        customer_full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
        sanctioned_status=False,
        risk_level=RiskLevel.LOW.value,
        risk_base_score=20,
        historical_metrics=HistoricalMetrics(
            rolling_24h_total=Decimal("0"),
            rolling_7d_count=0,
            rolling_30m_count=0,
            rolling_30m_total=Decimal("0"),
            rolling_90d_average=Decimal("0"),
            cross_border_count=0,
            high_risk_country_flag=False,
            prior_alert_count=0
        ),
        correlation_id="test-006"
    )
    
    service = RulesService(db_session)
    result = service.evaluate_all(transaction, context)
    
    # Assert exactly 8 results
    assert len(result.results) == 8
    
    # Assert all expected rule codes present
    rule_codes = {r.rule_code for r in result.results}
    expected_codes = {"AML-001", "AML-002", "AML-003", "AML-004", "AML-005", "AML-006", "AML-007", "AML-008"}
    assert rule_codes == expected_codes
