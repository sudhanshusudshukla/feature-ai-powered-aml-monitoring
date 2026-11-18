"""Tests for alert service and risk scoring."""
from datetime import datetime
from decimal import Decimal

import pytest

from app.alert.service import AlertService
from app.common.enums import (
    AccountStatus,
    AlertPriority,
    RiskLevel,
    RuleOutcome,
    RuleSeverity,
    TransactionType,
)
from app.customer.models import Account, Customer, CustomerRiskProfile
from app.customer.schemas import HistoricalMetrics, ScreeningContext
from app.rules.schemas import RuleEvaluationDraft
from app.transaction.models import Transaction


@pytest.fixture
def test_account(db_session):
    """Create a test account with customer and risk profile."""
    customer = Customer(
        customer_number="CUST-ALERT-TEST",
        full_name="Alert Test Customer",
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
        account_number="ACC-ALERT-TEST",
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


def test_alert_created_for_matches(db_session, test_account):
    """Test alert is created when rules match."""
    transaction = Transaction(
        transaction_reference="TX-ALERT-001",
        account_id=test_account.id,
        amount=Decimal("150000.00"),
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-alert-001"
    )
    db_session.add(transaction)
    db_session.flush()
    
    evaluations = [
        RuleEvaluationDraft(
            rule_code="AML-001",
            rule_name="High Value Transaction",
            rule_version=1,
            outcome=RuleOutcome.MATCH.value,
            severity=RuleSeverity.HIGH.value,
            score=30,
            explanation="High value detected",
            evidence_snapshot={"amount": "150000"}
        ),
        RuleEvaluationDraft(
            rule_code="AML-002",
            rule_name="Velocity Count",
            rule_version=1,
            outcome=RuleOutcome.PASS.value,
            severity=RuleSeverity.LOW.value,
            score=0,
            explanation="Normal velocity",
            evidence_snapshot={}
        ),
    ]
    
    context = ScreeningContext(
        account_id=test_account.id,
        account_number=test_account.account_number,
        account_status=AccountStatus.ACTIVE.value,
        customer_id=test_account.customer_id,
        customer_number="CUST-ALERT-TEST",
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
        correlation_id="test-alert-001"
    )
    
    service = AlertService(db_session)
    alert = service.create_alert_for_matches(transaction, evaluations, context, "test-alert-001")
    
    assert alert is not None
    assert alert.transaction_id == transaction.id
    assert alert.risk_score == 30  # Base score only
    assert alert.priority == AlertPriority.LOW.value  # 30 is below 35
    assert alert.alert_number.startswith("ALT-")


def test_no_alert_for_zero_matches(db_session, test_account):
    """Test no alert created when no rules match."""
    transaction = Transaction(
        transaction_reference="TX-ALERT-002",
        account_id=test_account.id,
        amount=Decimal("10000.00"),
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-alert-002"
    )
    db_session.add(transaction)
    db_session.flush()
    
    evaluations = [
        RuleEvaluationDraft(
            rule_code="AML-001",
            rule_name="High Value Transaction",
            rule_version=1,
            outcome=RuleOutcome.PASS.value,
            severity=RuleSeverity.LOW.value,
            score=0,
            explanation="Normal value",
            evidence_snapshot={}
        ),
        RuleEvaluationDraft(
            rule_code="AML-002",
            rule_name="Velocity Count",
            rule_version=1,
            outcome=RuleOutcome.PASS.value,
            severity=RuleSeverity.LOW.value,
            score=0,
            explanation="Normal velocity",
            evidence_snapshot={}
        ),
    ]
    
    context = ScreeningContext(
        account_id=test_account.id,
        account_number=test_account.account_number,
        account_status=AccountStatus.ACTIVE.value,
        customer_id=test_account.customer_id,
        customer_number="CUST-ALERT-TEST",
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
        correlation_id="test-alert-002"
    )
    
    service = AlertService(db_session)
    alert = service.create_alert_for_matches(transaction, evaluations, context, "test-alert-002")
    
    assert alert is None


def test_risk_score_aggregates_multiple_matches(db_session, test_account):
    """Test risk score sums multiple matched rules."""
    transaction = Transaction(
        transaction_reference="TX-ALERT-003",
        account_id=test_account.id,
        amount=Decimal("150000.00"),
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-alert-003"
    )
    db_session.add(transaction)
    db_session.flush()
    
    evaluations = [
        RuleEvaluationDraft(
            rule_code="AML-001",
            rule_name="High Value Transaction",
            rule_version=1,
            outcome=RuleOutcome.MATCH.value,
            severity=RuleSeverity.HIGH.value,
            score=30,
            explanation="High value",
            evidence_snapshot={}
        ),
        RuleEvaluationDraft(
            rule_code="AML-003",
            rule_name="Velocity Amount",
            rule_version=1,
            outcome=RuleOutcome.MATCH.value,
            severity=RuleSeverity.HIGH.value,
            score=25,
            explanation="High velocity",
            evidence_snapshot={}
        ),
        RuleEvaluationDraft(
            rule_code="AML-006",
            rule_name="Structuring",
            rule_version=1,
            outcome=RuleOutcome.MATCH.value,
            severity=RuleSeverity.HIGH.value,
            score=35,
            explanation="Structuring pattern",
            evidence_snapshot={}
        ),
    ]
    
    context = ScreeningContext(
        account_id=test_account.id,
        account_number=test_account.account_number,
        account_status=AccountStatus.ACTIVE.value,
        customer_id=test_account.customer_id,
        customer_number="CUST-ALERT-TEST",
        customer_full_name="Test Customer",
        residency_country="IN",
        pep_status=False,
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
            high_risk_country_flag=True,
            prior_alert_count=0
        ),
        correlation_id="test-alert-003"
    )
    
    service = AlertService(db_session)
    alert = service.create_alert_for_matches(transaction, evaluations, context, "test-alert-003")
    
    # Base: 30 + 25 + 35 = 90
    # Customer risk (HIGH): +10
    # Geography (high risk): +10
    # Total: 110, bounded to 100
    assert alert.risk_score == 100
    assert alert.priority == AlertPriority.CRITICAL.value  # >= 80


def test_pep_priority_floor_enforcement(db_session, test_account):
    """Test PEP status raises priority to at least HIGH."""
    transaction = Transaction(
        transaction_reference="TX-ALERT-004",
        account_id=test_account.id,
        amount=Decimal("60000.00"),
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-alert-004"
    )
    db_session.add(transaction)
    db_session.flush()
    
    evaluations = [
        RuleEvaluationDraft(
            rule_code="AML-005",
            rule_name="PEP Customer",
            rule_version=1,
            outcome=RuleOutcome.MATCH.value,
            severity=RuleSeverity.CRITICAL.value,
            score=40,
            explanation="PEP detected",
            evidence_snapshot={}
        ),
    ]
    
    context = ScreeningContext(
        account_id=test_account.id,
        account_number=test_account.account_number,
        account_status=AccountStatus.ACTIVE.value,
        customer_id=test_account.customer_id,
        customer_number="CUST-ALERT-TEST",
        customer_full_name="Test PEP",
        residency_country="IN",
        pep_status=True,  # PEP customer
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
        correlation_id="test-alert-004"
    )
    
    service = AlertService(db_session)
    alert = service.create_alert_for_matches(transaction, evaluations, context, "test-alert-004")
    
    # Score: 40, would normally be MEDIUM
    # But PEP raises to HIGH
    assert alert.risk_score == 40
    assert alert.priority == AlertPriority.HIGH.value
    assert "PEP/sanctioned" in alert.priority_rationale


def test_priority_bands(db_session, test_account):
    """Test exact priority band calculations."""
    transaction = Transaction(
        transaction_reference="TX-ALERT-005",
        account_id=test_account.id,
        amount=Decimal("10000.00"),
        currency="INR",
        transaction_type=TransactionType.TRANSFER.value,
        origin_country="IN",
        destination_country="US",
        transaction_timestamp=datetime.utcnow(),
        correlation_id="test-alert-005"
    )
    db_session.add(transaction)
    db_session.flush()
    
    context = ScreeningContext(
        account_id=test_account.id,
        account_number=test_account.account_number,
        account_status=AccountStatus.ACTIVE.value,
        customer_id=test_account.customer_id,
        customer_number="CUST-ALERT-TEST",
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
        correlation_id="test-alert-005"
    )
    
    service = AlertService(db_session)
    
    # Test LOW: < 35
    eval_low = [RuleEvaluationDraft(
        rule_code="AML-001", rule_name="Test", rule_version=1,
        outcome=RuleOutcome.MATCH.value, severity=RuleSeverity.LOW.value,
        score=30, explanation="", evidence_snapshot={}
    )]
    result_low = service.compute_risk_score(eval_low, context)
    assert result_low.final_score == 30
    assert result_low.priority == AlertPriority.LOW.value
    
    # Test MEDIUM: 35-59
    eval_medium = [RuleEvaluationDraft(
        rule_code="AML-001", rule_name="Test", rule_version=1,
        outcome=RuleOutcome.MATCH.value, severity=RuleSeverity.MEDIUM.value,
        score=50, explanation="", evidence_snapshot={}
    )]
    result_medium = service.compute_risk_score(eval_medium, context)
    assert result_medium.final_score == 50
    assert result_medium.priority == AlertPriority.MEDIUM.value
    
    # Test HIGH: 60-79
    eval_high = [RuleEvaluationDraft(
        rule_code="AML-001", rule_name="Test", rule_version=1,
        outcome=RuleOutcome.MATCH.value, severity=RuleSeverity.HIGH.value,
        score=70, explanation="", evidence_snapshot={}
    )]
    result_high = service.compute_risk_score(eval_high, context)
    assert result_high.final_score == 70
    assert result_high.priority == AlertPriority.HIGH.value
    
    # Test CRITICAL: >= 80
    eval_critical = [RuleEvaluationDraft(
        rule_code="AML-001", rule_name="Test", rule_version=1,
        outcome=RuleOutcome.MATCH.value, severity=RuleSeverity.CRITICAL.value,
        score=85, explanation="", evidence_snapshot={}
    )]
    result_critical = service.compute_risk_score(eval_critical, context)
    assert result_critical.final_score == 85
    assert result_critical.priority == AlertPriority.CRITICAL.value
