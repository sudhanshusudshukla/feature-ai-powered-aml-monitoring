"""
End-to-end integration tests covering complete AML workflow journeys.

These tests verify that the entire system works together correctly,
from transaction ingestion through rule evaluation, alert generation,
case management, and audit trail verification.
"""
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json


def create_test_setup(db_session: Session):
    """Helper to create test environment with customer, account, risk profile, and country risk."""
    from app.customer.models import Customer, Account, CustomerRiskProfile
    from app.risk.models import CountryRisk
    from app.security.models import User
    from app.common.enums import UserRole
    import bcrypt
    
    # Create country risk reference data
    country_us = CountryRisk(
        country_code="US",
        country_name="United States",
        is_high_risk=False,
        risk_rating="LOW",
        version=1
    )
    country_ru = CountryRisk(
        country_code="RU",
        country_name="Russia",
        is_high_risk=True,
        risk_rating="VERY_HIGH",
        version=1
    )
    country_cn = CountryRisk(
        country_code="CN",
        country_name="China",
        is_high_risk=True,
        risk_rating="HIGH",
        version=1
    )
    db_session.add_all([country_us, country_ru, country_cn])
    db_session.commit()
    
    # Create customer
    customer = Customer(
        customer_number="CUST-E2E-001",
        full_name="End-to-End Test Customer",
        residency_country="US",
        pep_status=False,
        sanctioned_status=False,
        synthetic_source="test"
    )
    db_session.add(customer)
    db_session.flush()
    
    # Create customer risk profile
    risk_profile = CustomerRiskProfile(
        customer_id=customer.id,
        risk_level="MEDIUM",
        base_score=50,
        last_reviewed_at=datetime.utcnow(),
        reviewed_by=None  # nullable field
    )
    db_session.add(risk_profile)
    db_session.commit()
    db_session.refresh(customer)
    
    # Create account
    account = Account(
        account_number="ACC-E2E-001",
        customer_id=customer.id,
        status="ACTIVE",
        opened_at=datetime.utcnow() - timedelta(days=365),
        current_balance=100000.00,
        currency="USD"
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    
    # Create users for case management workflow
    password_hash = bcrypt.hashpw("Test-pass-1".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    analyst = User(
        username="e2e.analyst@example.com",
        password_hash=password_hash,
        full_name="E2E Test Analyst",
        role=UserRole.AML_ANALYST.value,
        permissions_json="{}",
        is_active=True,
    )
    db_session.add(analyst)
    
    officer = User(
        username="e2e.officer@example.com",
        password_hash=password_hash,
        full_name="E2E Test Officer",
        role=UserRole.AML_OFFICER.value,
        permissions_json="{}",
        is_active=True,
    )
    db_session.add(officer)
    
    db_session.commit()
    db_session.refresh(analyst)
    db_session.refresh(officer)
    
    return {
        "customer": customer,
        "account": account,
        "risk_profile": risk_profile,
        "analyst": analyst,
        "officer": officer,
    }


class TestTransactionToAlertJourney:
    """Journey 1: Transaction receipt → screening → alert generation → audit trail verification."""
    
    def test_high_value_transaction_creates_alert_with_audit_trail(
        self, auth_client: TestClient, db_session: Session, all_rules_setup
    ):
        """
        End-to-end test of complete transaction ingestion workflow:
        1. Submit high-value transaction (triggers AML-001)
        2. Verify transaction persisted with correct evaluation results
        3. Verify alert created with correct risk score and priority
        4. Verify audit trail shows transaction ingestion, rule evaluation, and alert generation
        """
        test_setup = create_test_setup(db_session)
        account = test_setup["account"]
        
        # Step 1: Submit high-value transaction
        transaction_payload = {
            "transaction_reference": "TXN-E2E-001",
            "account_id": str(account.id),
            "amount": "150000.00",
            "currency": "USD",
            "transaction_type": "TRANSFER",
            "origin_country": "US",
            "destination_country": "RU",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        response = auth_client.post("/api/v1/transactions", json=transaction_payload)
        assert response.status_code == 201, f"Transaction ingestion failed: {response.text}"
        
        transaction_data = response.json()
        transaction_id = transaction_data["id"]
        
        # Step 2: Verify transaction persisted with evaluation results
        assert transaction_data["transaction_reference"] == "TXN-E2E-001"
        assert transaction_data["amount"] == "150000.00"
        assert transaction_data["matched_rules_count"] >= 1
        assert transaction_data["alert_raised"] is True
        assert transaction_data["alert_id"] is not None
        
        # Verify rule evaluation results
        assert len(transaction_data["evaluation_results"]) == 8
        matched_rules = [
            result for result in transaction_data["evaluation_results"]
            if result["outcome"] == "MATCH"
        ]
        assert len(matched_rules) >= 1, "Expected at least one rule match for high-value transaction"
        
        # Verify AML-001 (High Value Transaction) matched
        aml001_result = next(
            (r for r in transaction_data["evaluation_results"] if r["rule_code"] == "AML-001"),
            None
        )
        assert aml001_result is not None, "AML-001 should be evaluated"
        assert aml001_result["outcome"] == "MATCH", "AML-001 should match for $150k transaction"
        
        # Step 3: Verify alert created
        alert_id = transaction_data["alert_id"]
        alert_response = auth_client.get(f"/api/v1/alerts/{alert_id}")
        assert alert_response.status_code == 200
        
        alert_data = alert_response.json()
        assert alert_data["transaction_id"] == transaction_id
        assert alert_data["status"] == "NEW"
        assert alert_data["priority"] in ["MEDIUM", "HIGH", "CRITICAL"]
        assert alert_data["risk_score"] > 0
        
        # Step 4: Verify audit trail
        # Query audit events by correlation ID
        correlation_id = transaction_data.get("correlation_id")
        assert correlation_id is not None, "Correlation ID should be present"
        
        audit_response = auth_client.get(
            f"/api/v1/audit?correlation_id={correlation_id}&page=1&page_size=50"
        )
        assert audit_response.status_code == 200
        
        audit_data = audit_response.json()
        assert audit_data["total"] >= 3, "Expected at least 3 audit events (ingestion + rules + alert)"
        
        audit_items = audit_data["items"]
        
        # Verify TRANSACTION_INGESTED event
        ingestion_event = next(
            (e for e in audit_items if e["action"] == "TRANSACTION_INGESTED"),
            None
        )
        assert ingestion_event is not None
        assert ingestion_event["entity_type"] == "transaction"
        assert ingestion_event["entity_id"] == transaction_id
        
        # Verify RULE_EVALUATED events (should have 8, one per rule)
        rule_events = [e for e in audit_items if e["action"] == "RULE_EVALUATED"]
        assert len(rule_events) == 8, "Expected 8 rule evaluation events"
        
        # Verify ALERT_GENERATED event
        alert_event = next(
            (e for e in audit_items if e["action"] == "ALERT_GENERATED"),
            None
        )
        assert alert_event is not None
        assert alert_event["entity_type"] == "alert"
        assert alert_event["entity_id"] == alert_id
    
    def test_no_match_transaction_no_alert(
        self, auth_client: TestClient, db_session: Session, all_rules_setup
    ):
        """
        Verify that a low-value, normal transaction does not create an alert
        but still evaluates all rules and creates audit trail.
        """
        test_setup = create_test_setup(db_session)
        account = test_setup["account"]
        
        # Submit low-value transaction that should not trigger any rules
        transaction_payload = {
            "transaction_reference": "TXN-E2E-002",
            "account_id": str(account.id),
            "amount": "100.00",
            "currency": "USD",
            "transaction_type": "DEPOSIT",
            "origin_country": "US",
            "destination_country": "US",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        response = auth_client.post("/api/v1/transactions", json=transaction_payload)
        assert response.status_code == 201
        
        transaction_data = response.json()
        
        # Verify no alert raised
        assert transaction_data["alert_raised"] is False
        assert transaction_data["alert_id"] is None
        assert transaction_data["matched_rules_count"] == 0
        
        # Verify all rules still evaluated
        assert len(transaction_data["evaluation_results"]) == 8
        
        # Verify all outcomes are PASS
        for result in transaction_data["evaluation_results"]:
            assert result["outcome"] == "PASS"


class TestCaseDecisionJourney:
    """Journey 2: Case creation from alert → investigation → decision → audit trail verification."""
    
    def test_complete_case_workflow_with_separation_of_duties(
        self, client: TestClient, db_session: Session, all_rules_setup
    ):
        """
        End-to-end test of complete case management workflow:
        1. Analyst logs in and creates case from alert
        2. Analyst adds note to case
        3. Analyst requests information
        4. System records information response
        5. Officer logs in and makes decision (different user for separation of duties)
        6. Verify audit trail shows complete workflow
        """
        test_setup = create_test_setup(db_session)
        account = test_setup["account"]
        analyst = test_setup["analyst"]
        officer = test_setup["officer"]
        
        # Analyst login
        analyst_login = client.post(
            "/api/v1/auth/login",
            json={"email": "e2e.analyst@example.com", "password": "Test-pass-1"}
        )
        assert analyst_login.status_code == 200
        analyst_token = analyst_login.json()["access_token"]
        analyst_client = TestClient(client.app)
        analyst_client.headers["Authorization"] = f"Bearer {analyst_token}"
        
        # Step 1: Create transaction and alert (as analyst)
        transaction_payload = {
            "transaction_reference": "TXN-E2E-003",
            "account_id": str(account.id),
            "amount": "200000.00",
            "currency": "USD",
            "transaction_type": "TRANSFER",
            "origin_country": "US",
            "destination_country": "CN",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        txn_response = analyst_client.post("/api/v1/transactions", json=transaction_payload)
        assert txn_response.status_code == 201
        
        transaction_data = txn_response.json()
        assert transaction_data["alert_raised"] is True
        alert_id = transaction_data["alert_id"]
        
        # Step 2: Create case from alert
        case_payload = {
            "title": "Investigation of High Value Cross-Border Transaction",
            "alert_ids": [alert_id]
        }
        
        case_response = analyst_client.post("/api/v1/cases", json=case_payload)
        assert case_response.status_code == 201, f"Case creation failed: {case_response.text}"
        
        case_data = case_response.json()
        case_id = case_data["id"]
        assert case_data["state"] == "OPEN"
        assert case_data["created_by_user_id"] == analyst.id
        
        # Step 3: Add note to case
        note_payload = {
            "note_text": "Initial review completed. High-value transaction to high-risk country requires investigation."
        }
        
        note_response = analyst_client.post(f"/api/v1/cases/{case_id}/notes", json=note_payload)
        assert note_response.status_code == 201, f"Note creation failed: {note_response.text}"
        
        # Step 4: Request information
        info_request_payload = {
            "requested_what": "Customer business purpose documentation",
            "reason": "Need to verify legitimate business purpose for large transfer",
            "due_date": (datetime.utcnow() + timedelta(days=5)).isoformat() + "Z"
        }
        
        info_response = analyst_client.post(
            f"/api/v1/cases/{case_id}/request-info",
            json=info_request_payload
        )
        assert info_response.status_code == 201, f"Information request failed: {info_response.text}"
        
        info_data = info_response.json()
        info_request_id = info_data["id"]
        
        # Step 5: Record information response
        response_payload = {
            "response_text": "Customer provided invoice and contract documentation showing legitimate business transaction."
        }
        
        respond_response = analyst_client.post(
            f"/api/v1/cases/{case_id}/information-requests/{info_request_id}/respond",
            json=response_payload
        )
        assert respond_response.status_code == 201, f"Response recording failed: {respond_response.text}"
        
        # Manually transition case to PENDING_DECISION state (workaround for lack of transition API)
        from app.case_management.models import AMLCase
        from app.common.enums import CaseState
        case_record = db_session.query(AMLCase).filter(AMLCase.id == case_id).first()
        case_record.state = CaseState.PENDING_DECISION.value
        db_session.commit()
        
        # Step 6: Officer login (different user for separation of duties)
        officer_login = client.post(
            "/api/v1/auth/login",
            json={"email": "e2e.officer@example.com", "password": "Test-pass-1"}
        )
        assert officer_login.status_code == 200
        officer_token = officer_login.json()["access_token"]
        officer_client = TestClient(client.app)
        officer_client.headers["Authorization"] = f"Bearer {officer_token}"
        
        # Step 7: Officer makes decision
        # First, get current case to get expected_version
        case_detail_response = officer_client.get(f"/api/v1/cases/{case_id}")
        assert case_detail_response.status_code == 200
        current_version = case_detail_response.json()["version"]
        
        decision_payload = {
            "decision": "APPROVE",
            "reason": "Transaction verified as legitimate business purpose",
            "comments": "Documentation reviewed and confirmed. No AML risk detected.",
            "expected_version": current_version
        }
        
        decision_response = officer_client.post(
            f"/api/v1/cases/{case_id}/decision",
            json=decision_payload
        )
        assert decision_response.status_code == 200, f"Decision failed: {decision_response.text}"
        
        decision_data = decision_response.json()
        assert decision_data["state"] == "APPROVED"
        
        # Step 8: Verify complete audit trail
        # Get all audit events for this case
        audit_response = analyst_client.get(
            f"/api/v1/audit?entity_type=case&entity_id={case_id}&page=1&page_size=50"
        )
        assert audit_response.status_code == 200
        
        audit_data = audit_response.json()
        audit_items = audit_data["items"]
        
        # Verify key events exist
        assert any(e["action"] == "CASE_CREATED" for e in audit_items), "CASE_CREATED event missing"
        assert any(e["action"] == "CASE_NOTE_ADDED" for e in audit_items), "CASE_NOTE_ADDED event missing"
        assert any(e["action"] == "INFORMATION_REQUESTED" for e in audit_items), "INFORMATION_REQUESTED event missing"
        assert any(e["action"] == "INFORMATION_RESPONSE_RECORDED" for e in audit_items), "INFORMATION_RESPONSE_RECORDED event missing"
        assert any(e["action"] == "CASE_DECISION" for e in audit_items), "CASE_DECISION event missing"
        
        # Verify decision was made by officer, not analyst (separation of duties)
        decision_event = next(e for e in audit_items if e["action"] == "CASE_DECISION")
        assert decision_event["actor_user_id"] == officer.id
        assert decision_event["actor_user_id"] != str(analyst.id)
    
    def test_separation_of_duties_enforcement(
        self, client: TestClient, db_session: Session, all_rules_setup
    ):
        """
        Verify that case creator cannot make decision on their own case.
        """
        test_setup = create_test_setup(db_session)
        account = test_setup["account"]
        analyst = test_setup["analyst"]
        
        # Analyst login
        analyst_login = client.post(
            "/api/v1/auth/login",
            json={"email": "e2e.analyst@example.com", "password": "Test-pass-1"}
        )
        assert analyst_login.status_code == 200
        analyst_token = analyst_login.json()["access_token"]
        analyst_client = TestClient(client.app)
        analyst_client.headers["Authorization"] = f"Bearer {analyst_token}"
        
        # Create transaction and alert
        transaction_payload = {
            "transaction_reference": "TXN-E2E-004",
            "account_id": str(account.id),
            "amount": "180000.00",
            "currency": "USD",
            "transaction_type": "TRANSFER",
            "origin_country": "US",
            "destination_country": "RU",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        txn_response = analyst_client.post("/api/v1/transactions", json=transaction_payload)
        assert txn_response.status_code == 201
        alert_id = txn_response.json()["alert_id"]
        
        # Create case
        case_payload = {
            "title": "Separation of Duties Test Case",
            "alert_ids": [alert_id]
        }
        
        case_response = analyst_client.post("/api/v1/cases", json=case_payload)
        assert case_response.status_code == 201
        case_id = case_response.json()["id"]
        
        # Try to make decision as same user (should fail)
        case_detail = analyst_client.get(f"/api/v1/cases/{case_id}")
        current_version = case_detail.json()["version"]
        
        decision_payload = {
            "decision": "APPROVE",
            "reason": "Self approval attempt",
            "comments": "This should fail",
            "expected_version": current_version
        }
        
        decision_response = analyst_client.post(
            f"/api/v1/cases/{case_id}/decision",
            json=decision_payload
        )
        
        # Should get 403 Forbidden due to separation of duties
        assert decision_response.status_code == 403, "Expected 403 for creator attempting to decide own case"
        response_data = decision_response.json()
        error_detail = response_data.get("detail", "").lower()
        assert "creator" in error_detail and "conflict" in error_detail
