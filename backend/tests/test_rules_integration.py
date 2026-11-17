"""Integration tests for rules evaluation with transaction ingestion."""
import json
from datetime import datetime
from decimal import Decimal

import pytest

from app.common.enums import RuleSeverity, TransactionType
from app.customer.models import Account, Customer, CustomerRiskProfile
from app.risk.models import CountryRisk
from app.rules.models import DetectionRule, RuleVersion


def test_transaction_ingestion_evaluates_all_rules(auth_client, db_session):
    """Test transaction ingestion triggers evaluation of all 8 rules."""
    # Setup customer, account, rules
    customer = Customer(
        customer_number="CUST-INT-001",
        full_name="Integration Test Customer",
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
        risk_level="LOW",
        base_score=20,
        last_reviewed_at=datetime.utcnow(),
        version=1
    )
    db_session.add(risk_profile)
    
    account = Account(
        account_number="ACC-INT-001",
        customer_id=customer.id,
        status="ACTIVE",
        opened_at=datetime.utcnow(),
        current_balance=Decimal("100000.00"),
        currency="INR",
        version=1
    )
    db_session.add(account)
    db_session.flush()
    
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
    
    # Setup country risk
    country_in = CountryRisk(
        country_code="IN",
        country_name="India",
        is_high_risk=False,
        risk_rating="LOW",
        version=1
    )
    country_us = CountryRisk(
        country_code="US",
        country_name="United States",
        is_high_risk=False,
        risk_rating="LOW",
        version=1
    )
    db_session.add(country_in)
    db_session.add(country_us)
    db_session.commit()
    
    # Ingest transaction
    payload = {
        "transaction_reference": "TX-INT-001",
        "account_id": account.id,
        "amount": "50000.00",
        "currency": "INR",
        "transaction_type": TransactionType.TRANSFER.value,
        "origin_country": "IN",
        "destination_country": "US",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = auth_client.post("/api/v1/transactions", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify 8 evaluation results returned
    assert len(data["evaluation_results"]) == 8
    
    # Verify all rule codes present
    rule_codes = {r["rule_code"] for r in data["evaluation_results"]}
    expected_codes = {"AML-001", "AML-002", "AML-003", "AML-004", "AML-005", "AML-006", "AML-007", "AML-008"}
    assert rule_codes == expected_codes
    
    # Verify each result has required fields
    for result in data["evaluation_results"]:
        assert "rule_code" in result
        assert "rule_name" in result
        assert "rule_version" in result
        assert result["rule_version"] == 1
        assert "outcome" in result
        assert result["outcome"] in ["PASS", "MATCH"]
        assert "severity" in result
        assert "score" in result
        assert "explanation" in result
        assert "evidence_snapshot" in result


def test_high_value_transaction_creates_alert(auth_client, db_session):
    """Test high-value transaction triggers match and creates alert."""
    # Setup customer and account
    customer = Customer(
        customer_number="CUST-INT-002",
        full_name="High Value Customer",
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
        risk_level="LOW",
        base_score=20,
        last_reviewed_at=datetime.utcnow(),
        version=1
    )
    db_session.add(risk_profile)
    
    account = Account(
        account_number="ACC-INT-002",
        customer_id=customer.id,
        status="ACTIVE",
        opened_at=datetime.utcnow(),
        current_balance=Decimal("500000.00"),
        currency="INR",
        version=1
    )
    db_session.add(account)
    db_session.flush()
    
    # Setup rules
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
            severity=RuleSeverity.HIGH.value,
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
    
    country_in = CountryRisk(
        country_code="IN",
        country_name="India",
        is_high_risk=False,
        risk_rating="LOW",
        version=1
    )
    country_us = CountryRisk(
        country_code="US",
        country_name="United States",
        is_high_risk=False,
        risk_rating="LOW",
        version=1
    )
    db_session.add(country_in)
    db_session.add(country_us)
    db_session.commit()
    
    # Ingest high-value transaction
    payload = {
        "transaction_reference": "TX-INT-HIGH-001",
        "account_id": account.id,
        "amount": "150000.00",  # Above threshold
        "currency": "INR",
        "transaction_type": TransactionType.TRANSFER.value,
        "origin_country": "IN",
        "destination_country": "US",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = auth_client.post("/api/v1/transactions", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify alert was raised
    assert data["matched_rules_count"] >= 1
    assert data["alert_raised"] is True
    assert data["alert_id"] is not None
    
    # Find AML-001 result
    aml001_result = next(r for r in data["evaluation_results"] if r["rule_code"] == "AML-001")
    assert aml001_result["outcome"] == "MATCH"
    assert aml001_result["score"] > 0


def test_transaction_detail_includes_evaluations(auth_client, db_session):
    """Test transaction detail endpoint returns persisted evaluations."""
    # Setup customer and account
    customer = Customer(
        customer_number="CUST-INT-003",
        full_name="Detail Test Customer",
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
        risk_level="LOW",
        base_score=20,
        last_reviewed_at=datetime.utcnow(),
        version=1
    )
    db_session.add(risk_profile)
    
    account = Account(
        account_number="ACC-INT-003",
        customer_id=customer.id,
        status="ACTIVE",
        opened_at=datetime.utcnow(),
        current_balance=Decimal("100000.00"),
        currency="INR",
        version=1
    )
    db_session.add(account)
    db_session.flush()
    
    # Setup rules
    for rule_code, name, params in [
        ("AML-001", "High Value Transaction", {"threshold": 100000}),
        ("AML-002", "Transaction Velocity (Count)", {"threshold_7d_count": 10}),
        ("AML-003", "Transaction Velocity (Amount)", {"threshold_24h_total": 500000}),
        ("AML-004", "High Risk Geography", {}),
        ("AML-005", "Sanctioned or PEP Customer", {}),
        ("AML-006", "Structuring Pattern", {"count_threshold_30m": 5, "amount_below_threshold": 50000}),
        ("AML-007", "Dormancy Spike", {"spike_multiplier": 5.0}),
        ("AML-008", "Round Amount Pattern", {"min_round_amount": 10000}),
    ]:
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
    
    country_in = CountryRisk(
        country_code="IN",
        country_name="India",
        is_high_risk=False,
        risk_rating="LOW",
        version=1
    )
    country_us = CountryRisk(
        country_code="US",
        country_name="United States",
        is_high_risk=False,
        risk_rating="LOW",
        version=1
    )
    db_session.add(country_in)
    db_session.add(country_us)
    db_session.commit()
    
    # Ingest transaction
    payload = {
        "transaction_reference": "TX-INT-DETAIL-001",
        "account_id": account.id,
        "amount": "50000.00",
        "currency": "INR",
        "transaction_type": TransactionType.TRANSFER.value,
        "origin_country": "IN",
        "destination_country": "US",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    ingest_response = auth_client.post("/api/v1/transactions", json=payload)
    assert ingest_response.status_code == 201
    transaction_id = ingest_response.json()["id"]
    
    # Retrieve transaction detail
    detail_response = auth_client.get(f"/api/v1/transactions/{transaction_id}")
    
    assert detail_response.status_code == 200
    detail_data = detail_response.json()
    
    # Verify evaluations persisted and returned
    assert len(detail_data["evaluation_results"]) == 8
    assert detail_data["matched_rules_count"] >= 0
    
    # Verify structure of returned evaluations
    for result in detail_data["evaluation_results"]:
        assert "rule_code" in result
        assert "rule_name" in result
        assert "outcome" in result
        assert "explanation" in result
