"""
Seed script to populate database with default users and reference data.
Idempotent - can be run multiple times safely.
"""
import json
from datetime import datetime, timedelta
from decimal import Decimal

import bcrypt
from sqlalchemy.orm import Session

from app.alert.models import Alert
from app.audit.models import AuditEvent
from app.common.enums import (
    AccountStatus,
    AlertPriority,
    AlertStatus,
    CountryRiskRating,
    RiskLevel,
    RuleSeverity,
    UserRole,
)
from app.customer.models import Account, Customer, CustomerRiskProfile
from app.database import get_db
from app.risk.models import CountryRisk
from app.rules.models import DetectionRule, RuleVersion
from app.security.models import User
from app.transaction.models import Transaction


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def seed_users(db: Session):
    """Seed default users for each role."""
    default_users = [
        {
            "username": "analyst@example.com",
            "password": "Analyst-pass-1",
            "full_name": "Ana Fernandes",
            "role": UserRole.AML_ANALYST,
            "permissions_json": "{}",
        },
        {
            "username": "officer@example.com",
            "password": "Officer-pass-1",
            "full_name": "Omar Khan",
            "role": UserRole.AML_OFFICER,
            "permissions_json": "{}",
        },
        {
            "username": "manager@example.com",
            "password": "Manager-pass-1",
            "full_name": "Maria Silva",
            "role": UserRole.AML_MANAGER,
            "permissions_json": "{}",
        },
        {
            "username": "admin@example.com",
            "password": "Admin-pass-1",
            "full_name": "Admin User",
            "role": UserRole.ADMINISTRATOR,
            "permissions_json": "{}",
        },
        {
            "username": "auditor@example.com",
            "password": "Auditor-pass-1",
            "full_name": "Audit User",
            "role": UserRole.AUDITOR,
            "permissions_json": "{}",
        },
    ]
    
    for user_data in default_users:
        existing = db.query(User).filter(User.username == user_data["username"]).first()
        if existing:
            print(f"User {user_data['username']} already exists, skipping")
            continue
        
        role_value = user_data["role"].value if hasattr(user_data["role"], 'value') else str(user_data["role"])
        user = User(
            username=user_data["username"],
            password_hash=hash_password(user_data["password"]),
            full_name=user_data["full_name"],
            role=role_value,
            permissions_json=user_data["permissions_json"],
            is_active=True,
        )
        db.add(user)
        print(f"Created user: {user_data['username']} ({user_data['full_name']})")
    
    db.commit()


def seed_detection_rules(db: Session):
    """Seed the eight AML detection rules."""
    rules_data = [
        {
            "rule_code": "AML-001",
            "name": "High Value Transaction",
            "severity": RuleSeverity.HIGH,
            "description": "Detects transactions with exceptionally high amounts",
            "params": {"threshold": 100000}
        },
        {
            "rule_code": "AML-002",
            "name": "Transaction Velocity (Count)",
            "severity": RuleSeverity.MEDIUM,
            "description": "Detects unusual transaction frequency patterns",
            "params": {"threshold_7d_count": 10}
        },
        {
            "rule_code": "AML-003",
            "name": "Transaction Velocity (Amount)",
            "severity": RuleSeverity.HIGH,
            "description": "Detects unusual transaction volume in short time windows",
            "params": {"threshold_24h_total": 500000}
        },
        {
            "rule_code": "AML-004",
            "name": "High Risk Geography",
            "severity": RuleSeverity.MEDIUM,
            "description": "Detects transactions involving high-risk countries",
            "params": {}
        },
        {
            "rule_code": "AML-005",
            "name": "Sanctioned or PEP Customer",
            "severity": RuleSeverity.CRITICAL,
            "description": "Detects transactions from politically exposed persons or sanctioned entities",
            "params": {}
        },
        {
            "rule_code": "AML-006",
            "name": "Structuring Pattern",
            "severity": RuleSeverity.HIGH,
            "description": "Detects potential structuring behavior to evade reporting thresholds",
            "params": {"count_threshold_30m": 5, "amount_below_threshold": 50000}
        },
        {
            "rule_code": "AML-007",
            "name": "Dormancy Spike",
            "severity": RuleSeverity.MEDIUM,
            "description": "Detects sudden activity after dormancy periods",
            "params": {"spike_multiplier": 5.0}
        },
        {
            "rule_code": "AML-008",
            "name": "Round Amount Pattern",
            "severity": RuleSeverity.LOW,
            "description": "Detects suspicious round-number transaction amounts",
            "params": {"min_round_amount": 10000}
        },
    ]
    
    for rule_data in rules_data:
        existing = db.query(DetectionRule).filter(
            DetectionRule.rule_code == rule_data["rule_code"]
        ).first()
        
        if existing:
            print(f"Rule {rule_data['rule_code']} already exists, skipping")
            continue
        
        severity_value = rule_data["severity"].value if hasattr(rule_data["severity"], 'value') else str(rule_data["severity"])
        
        rule = DetectionRule(
            rule_code=rule_data["rule_code"],
            name=rule_data["name"],
            severity=severity_value,
            description=rule_data["description"],
            is_active=True,
            version=1
        )
        db.add(rule)
        db.flush()
        
        # Create version 1 for each rule
        rule_version = RuleVersion(
            rule_id=rule.id,
            version_number=1,
            parameters_json=json.dumps(rule_data["params"]),
            effective_from=datetime.utcnow(),
            changed_by=None,
            change_reason="Initial rule version"
        )
        db.add(rule_version)
        print(f"Created rule: {rule_data['rule_code']} - {rule_data['name']}")
    
    db.commit()


def seed_country_risk(db: Session):
    """Seed country risk reference data."""
    countries = [
        {"code": "IN", "name": "India", "is_high_risk": False, "rating": CountryRiskRating.LOW},
        {"code": "US", "name": "United States", "is_high_risk": False, "rating": CountryRiskRating.LOW},
        {"code": "GB", "name": "United Kingdom", "is_high_risk": False, "rating": CountryRiskRating.LOW},
        {"code": "SG", "name": "Singapore", "is_high_risk": False, "rating": CountryRiskRating.LOW},
        {"code": "AE", "name": "United Arab Emirates", "is_high_risk": False, "rating": CountryRiskRating.MEDIUM},
        {"code": "CH", "name": "Switzerland", "is_high_risk": False, "rating": CountryRiskRating.LOW},
        {"code": "KP", "name": "North Korea", "is_high_risk": True, "rating": CountryRiskRating.VERY_HIGH},
        {"code": "IR", "name": "Iran", "is_high_risk": True, "rating": CountryRiskRating.VERY_HIGH},
    ]
    
    for country_data in countries:
        existing = db.query(CountryRisk).filter(
            CountryRisk.country_code == country_data["code"]
        ).first()
        
        if existing:
            print(f"Country {country_data['code']} already exists, skipping")
            continue
        
        rating_value = country_data["rating"].value if hasattr(country_data["rating"], 'value') else str(country_data["rating"])
        
        country = CountryRisk(
            country_code=country_data["code"],
            country_name=country_data["name"],
            is_high_risk=country_data["is_high_risk"],
            risk_rating=rating_value,
            version=1
        )
        db.add(country)
        print(f"Created country: {country_data['code']} - {country_data['name']}")
    
    db.commit()


def seed_customers_and_accounts(db: Session):
    """Seed sample customers and accounts."""
    customers_data = [
        {
            "customer_number": "CUST-001",
            "full_name": "Rajesh Kumar",
            "residency_country": "IN",
            "pep_status": False,
            "sanctioned_status": False,
            "risk_level": RiskLevel.LOW,
            "base_score": 20,
            "account_number": "ACC-001-001",
            "balance": Decimal("150000.00")
        },
        {
            "customer_number": "CUST-002",
            "full_name": "Sarah Johnson",
            "residency_country": "US",
            "pep_status": False,
            "sanctioned_status": False,
            "risk_level": RiskLevel.MEDIUM,
            "base_score": 45,
            "account_number": "ACC-002-001",
            "balance": Decimal("500000.00")
        },
        {
            "customer_number": "CUST-003",
            "full_name": "Ahmed Hassan",
            "residency_country": "AE",
            "pep_status": True,
            "sanctioned_status": False,
            "risk_level": RiskLevel.HIGH,
            "base_score": 75,
            "account_number": "ACC-003-001",
            "balance": Decimal("2500000.00")
        },
        {
            "customer_number": "CUST-004",
            "full_name": "Maria Garcia",
            "residency_country": "US",
            "pep_status": False,
            "sanctioned_status": False,
            "risk_level": RiskLevel.LOW,
            "base_score": 15,
            "account_number": "ACC-004-001",
            "balance": Decimal("75000.00")
        },
    ]
    
    for customer_data in customers_data:
        existing = db.query(Customer).filter(
            Customer.customer_number == customer_data["customer_number"]
        ).first()
        
        if existing:
            print(f"Customer {customer_data['customer_number']} already exists, skipping")
            continue
        
        # Create customer
        customer = Customer(
            customer_number=customer_data["customer_number"],
            full_name=customer_data["full_name"],
            residency_country=customer_data["residency_country"],
            pep_status=customer_data["pep_status"],
            sanctioned_status=customer_data["sanctioned_status"],
            synthetic_source="SEED_DATA",
            version=1
        )
        db.add(customer)
        db.flush()
        
        # Create risk profile
        risk_level_value = customer_data["risk_level"].value if hasattr(customer_data["risk_level"], 'value') else str(customer_data["risk_level"])
        risk_profile = CustomerRiskProfile(
            customer_id=customer.id,
            risk_level=risk_level_value,
            base_score=customer_data["base_score"],
            last_reviewed_at=datetime.utcnow(),
            reviewed_by=None,
            version=1
        )
        db.add(risk_profile)
        
        # Create account
        account = Account(
            account_number=customer_data["account_number"],
            customer_id=customer.id,
            status=AccountStatus.ACTIVE.value,
            opened_at=datetime.utcnow() - timedelta(days=365),
            current_balance=customer_data["balance"],
            currency="INR",
            version=1
        )
        db.add(account)
        
        print(f"Created customer: {customer_data['customer_number']} - {customer_data['full_name']}")
    
    db.commit()


def seed_sample_transactions(db: Session):
    """Seed sample transactions for demonstration."""
    from app.transaction.models import Transaction
    from decimal import Decimal
    
    # Check if transactions already exist
    existing_count = db.query(Transaction).count()
    if existing_count > 0:
        print(f"{existing_count} transactions already exist, skipping")
        return
    
    # Get accounts
    accounts = db.query(Account).limit(3).all()
    if not accounts:
        print("No accounts found, skipping sample transactions")
        return
    
    # Create 3 sample transactions
    for idx, account in enumerate(accounts, start=1):
        transaction = Transaction(
            transaction_reference=f"TXN-{idx:06d}",
            account_id=account.id,
            amount=Decimal("15000.00") if idx == 1 else Decimal("5000.00"),
            currency="USD",
            transaction_type="TRANSFER",
            origin_country="US",
            destination_country="AE" if idx == 1 else "GB",
            transaction_timestamp=datetime.utcnow(),
            correlation_id=f"seed-txn-{idx}",
            created_at=datetime.utcnow()
        )
        db.add(transaction)
        print(f"Created sample transaction: {transaction.transaction_reference}")
    
    db.commit()


def seed_rule_evaluation_results(db: Session):
    """Seed rule evaluation results for sample transactions."""
    from app.rules.models import RuleEvaluationResult, DetectionRule
    
    # Get first 3 transactions (seed data) and rules
    transactions = db.query(Transaction).order_by(Transaction.id).limit(3).all()
    rules = db.query(DetectionRule).all()
    
    if not transactions or not rules:
        print("No transactions or rules found, skipping rule evaluation results")
        return
    
    # Seed evaluation results for each transaction
    # Transaction 1: Matches AML-001 (High Value), AML-004 (High Risk Geography)
    if len(transactions) >= 1:
        transaction1 = transactions[0]
        rule_001 = next((r for r in rules if r.rule_code == "AML-001"), None)
        rule_004 = next((r for r in rules if r.rule_code == "AML-004"), None)
        
        if rule_001:
            existing = db.query(RuleEvaluationResult).filter(
                RuleEvaluationResult.transaction_id == transaction1.id,
                RuleEvaluationResult.rule_id == rule_001.id
            ).first()
            if not existing:
                eval_result = RuleEvaluationResult(
                    transaction_id=transaction1.id,
                    rule_id=rule_001.id,
                    rule_code=rule_001.rule_code,
                    rule_version=1,
                    result="MATCH",
                    severity=rule_001.severity,
                    score=25,
                    explanation=f"Transaction amount ${transaction1.amount} exceeds the high-value threshold of $100,000",
                    evidence_snapshot=json.dumps({
                        "amount": str(transaction1.amount),
                        "threshold": 100000,
                        "currency": transaction1.currency
                    }),
                    created_at=transaction1.created_at
                )
                db.add(eval_result)
                print(f"Created rule evaluation result: {transaction1.transaction_reference} x {rule_001.rule_code}")
            else:
                print(f"Rule evaluation result for {transaction1.transaction_reference} x {rule_001.rule_code} already exists, skipping")
        
        if rule_004:
            existing = db.query(RuleEvaluationResult).filter(
                RuleEvaluationResult.transaction_id == transaction1.id,
                RuleEvaluationResult.rule_id == rule_004.id
            ).first()
            if not existing:
                eval_result = RuleEvaluationResult(
                    transaction_id=transaction1.id,
                    rule_id=rule_004.id,
                    rule_code=rule_004.rule_code,
                    rule_version=1,
                    result="MATCH",
                    severity=rule_004.severity,
                    score=15,
                    explanation=f"Transaction involves high-risk geography: destination country {transaction1.destination_country}",
                    evidence_snapshot=json.dumps({
                        "origin_country": transaction1.origin_country,
                        "destination_country": transaction1.destination_country,
                        "risk_rating": "MEDIUM"
                    }),
                    created_at=transaction1.created_at
                )
                db.add(eval_result)
                print(f"Created rule evaluation result: {transaction1.transaction_reference} x {rule_004.rule_code}")
            else:
                print(f"Rule evaluation result for {transaction1.transaction_reference} x {rule_004.rule_code} already exists, skipping")
    
    # Transaction 2: Matches AML-008 (Round Amount)
    if len(transactions) >= 2:
        transaction2 = transactions[1]
        rule_008 = next((r for r in rules if r.rule_code == "AML-008"), None)
        
        if rule_008:
            existing = db.query(RuleEvaluationResult).filter(
                RuleEvaluationResult.transaction_id == transaction2.id,
                RuleEvaluationResult.rule_id == rule_008.id
            ).first()
            if not existing:
                eval_result = RuleEvaluationResult(
                    transaction_id=transaction2.id,
                    rule_id=rule_008.id,
                    rule_code=rule_008.rule_code,
                    rule_version=1,
                    result="MATCH",
                    severity=rule_008.severity,
                    score=10,
                    explanation=f"Transaction amount ${transaction2.amount} is a suspicious round number",
                    evidence_snapshot=json.dumps({
                        "amount": str(transaction2.amount),
                        "is_round": True
                    }),
                    created_at=transaction2.created_at
                )
                db.add(eval_result)
                print(f"Created rule evaluation result: {transaction2.transaction_reference} x {rule_008.rule_code}")
            else:
                print(f"Rule evaluation result for {transaction2.transaction_reference} x {rule_008.rule_code} already exists, skipping")
    
    # Transaction 3: Matches AML-002 (Transaction Velocity), AML-004 (High Risk Geography)
    if len(transactions) >= 3:
        transaction3 = transactions[2]
        rule_002 = next((r for r in rules if r.rule_code == "AML-002"), None)
        rule_004 = next((r for r in rules if r.rule_code == "AML-004"), None)
        
        if rule_002:
            existing = db.query(RuleEvaluationResult).filter(
                RuleEvaluationResult.transaction_id == transaction3.id,
                RuleEvaluationResult.rule_id == rule_002.id
            ).first()
            if not existing:
                eval_result = RuleEvaluationResult(
                    transaction_id=transaction3.id,
                    rule_id=rule_002.id,
                    rule_code=rule_002.rule_code,
                    rule_version=1,
                    result="MATCH",
                    severity=rule_002.severity,
                    score=20,
                    explanation="Account shows unusual transaction frequency pattern in the last 7 days",
                    evidence_snapshot=json.dumps({
                        "transaction_count_7d": 12,
                        "threshold": 10,
                        "average_baseline": 3
                    }),
                    created_at=transaction3.created_at
                )
                db.add(eval_result)
                print(f"Created rule evaluation result: {transaction3.transaction_reference} x {rule_002.rule_code}")
            else:
                print(f"Rule evaluation result for {transaction3.transaction_reference} x {rule_002.rule_code} already exists, skipping")
        
        if rule_004:
            existing = db.query(RuleEvaluationResult).filter(
                RuleEvaluationResult.transaction_id == transaction3.id,
                RuleEvaluationResult.rule_id == rule_004.id
            ).first()
            if not existing:
                eval_result = RuleEvaluationResult(
                    transaction_id=transaction3.id,
                    rule_id=rule_004.id,
                    rule_code=rule_004.rule_code,
                    rule_version=1,
                    result="MATCH",
                    severity=rule_004.severity,
                    score=15,
                    explanation=f"Transaction destination {transaction3.destination_country} is flagged as medium risk",
                    evidence_snapshot=json.dumps({
                        "origin_country": transaction3.origin_country,
                        "destination_country": transaction3.destination_country,
                        "risk_rating": "MEDIUM"
                    }),
                    created_at=transaction3.created_at
                )
                db.add(eval_result)
                print(f"Created rule evaluation result: {transaction3.transaction_reference} x {rule_004.rule_code}")
            else:
                print(f"Rule evaluation result for {transaction3.transaction_reference} x {rule_004.rule_code} already exists, skipping")
    
    db.commit()


def seed_sample_alerts(db: Session):
    """Seed sample alerts linked to sample transactions."""
    # First check if we have sample transactions from previous ingestion
    sample_transactions = db.query(Transaction).limit(3).all()
    
    if not sample_transactions:
        print("No transactions found, skipping sample alerts")
        return
    
    for idx, transaction in enumerate(sample_transactions, start=1):
        # Check if alert already exists for this transaction
        existing = db.query(Alert).filter(Alert.transaction_id == transaction.id).first()
        if existing:
            print(f"Alert for transaction {transaction.id} already exists, skipping")
            continue
        
        # Create sample alert
        alert = Alert(
            alert_number=f"ALT-{idx:06d}",
            transaction_id=transaction.id,
            risk_score=65 + (idx * 5),
            priority=AlertPriority.HIGH.value,
            status=AlertStatus.NEW.value,
            assigned_to_user_id=None,
            priority_rationale=f"Sample alert {idx} for demonstration purposes",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=1
        )
        db.add(alert)
        print(f"Created sample alert: {alert.alert_number}")
    
    db.commit()


def seed_cases(db: Session):
    """Seed sample cases for demonstration."""
    from app.case_management.models import AMLCase, CaseAlertLink, CaseNote
    from app.investigation.models import InformationRequest
    from datetime import timedelta
    
    # Reset terminal-state cases back to PENDING_DECISION for testing
    terminal_cases = db.query(AMLCase).filter(
        AMLCase.case_number.in_(['CASE-000001', 'CASE-000002']),
        AMLCase.state.in_(['APPROVED', 'REJECTED', 'CLOSED'])
    ).all()
    
    for case in terminal_cases:
        case.state = 'PENDING_DECISION'
        print(f"Reset {case.case_number} state to PENDING_DECISION")
    
    if terminal_cases:
        db.commit()
    
    # Get users and alerts
    analyst = db.query(User).filter_by(username="analyst@example.com").first()
    officer = db.query(User).filter_by(username="officer@example.com").first()
    alerts = db.query(Alert).limit(3).all()
    
    if not analyst or not officer or len(alerts) < 2:
        print("Missing required data for case seeding, skipping")
        return
    
    # Check if cases already exist
    case1 = db.query(AMLCase).filter_by(case_number="CASE-000001").first()
    case2 = db.query(AMLCase).filter_by(case_number="CASE-000002").first()
    
    if not case1:
        # Create case 1: PENDING_DECISION (ready for officer decision)
        case1 = AMLCase(
            case_number="CASE-000001",
            title="Suspicious high-value transfer investigation",
            customer_id=alerts[0].transaction.account.customer_id,
            state="PENDING_DECISION",
            priority=alerts[0].priority,
            created_by_user_id=analyst.id,
            assigned_to_user_id=officer.id,
            version=1
        )
        db.add(case1)
        db.flush()
        
        # Link first alert to case1
        link1 = CaseAlertLink(
            case_id=case1.id,
            alert_id=alerts[0].id,
            linked_at=datetime.utcnow(),
            linked_by_user_id=analyst.id
        )
        db.add(link1)
        
        # Add a note to case1
        note1 = CaseNote(
            case_id=case1.id,
            note_text="Investigation completed. Ready for decision.",
            created_by_user_id=analyst.id
        )
        db.add(note1)
        print(f"Created case: {case1.case_number}")
    
    # Add a closed information request to case1 (already responded, won't block decisions)
    # Check if it already exists
    existing_req1 = db.query(InformationRequest).filter_by(case_id=case1.id).first()
    if not existing_req1:
        info_req1 = InformationRequest(
            case_id=case1.id,
            requested_what="Customer identification documents",
            reason="Verification required per compliance policy",
            due_date=datetime.utcnow() - timedelta(days=2),
            status="RESPONDED",
            requested_by_user_id=officer.id,
            version=1
        )
        db.add(info_req1)
        print(f"Created responded information request for case {case1.case_number}")
    
    if not case2:
        # Create case 2: PENDING_DECISION with an open information request (to test blocking)
        case2 = AMLCase(
            case_number="CASE-000002",
            title="Multiple small transactions to high-risk jurisdiction",
            customer_id=alerts[1].transaction.account.customer_id,
            state="PENDING_DECISION",
            priority=alerts[1].priority,
            created_by_user_id=analyst.id,
            assigned_to_user_id=officer.id,
            version=1
        )
        db.add(case2)
        db.flush()
        
        # Link second alert to case2
        link2 = CaseAlertLink(
            case_id=case2.id,
            alert_id=alerts[1].id,
            linked_at=datetime.utcnow(),
            linked_by_user_id=analyst.id
        )
        db.add(link2)
        
        # Add a note to case2
        note2 = CaseNote(
            case_id=case2.id,
            note_text="Reviewing transaction pattern. Additional info requested.",
            created_by_user_id=analyst.id
        )
        db.add(note2)
        print(f"Created case: {case2.case_number}")
    
    # Add a closed information request to case2 (already responded, won't block decisions)
    # Check if it already exists
    existing_req2 = db.query(InformationRequest).filter_by(case_id=case2.id).first()
    if not existing_req2:
        info_req2 = InformationRequest(
            case_id=case2.id,
            requested_what="Bank statements for the last 3 months",
            reason="Need to verify transaction history",
            due_date=datetime.utcnow() + timedelta(days=3),
            status="RESPONDED",
            requested_by_user_id=officer.id,
            version=1
        )
        db.add(info_req2)
        print(f"Created responded information request for case {case2.case_number}")
    
    db.commit()
    print("Sample cases seeding completed")


def seed_audit_events(db: Session):
    """Seed sample audit events for demonstration."""
    # Only seed if we have transactions and alerts
    sample_transactions = db.query(Transaction).limit(3).all()
    sample_alerts = db.query(Alert).limit(3).all()
    
    if not sample_transactions:
        print("No transactions found, skipping audit events")
        return
    
    # Check if audit events already exist
    existing_count = db.query(AuditEvent).count()
    if existing_count > 0:
        print(f"{existing_count} audit events already exist, skipping")
        return
    
    # Create sample audit events for transactions
    for transaction in sample_transactions:
        # Transaction ingested event
        audit_event = AuditEvent(
            timestamp=transaction.created_at,
            actor_user_id=None,
            actor_username="system",
            actor_role="system",
            action="TRANSACTION_INGESTED",
            entity_type="transaction",
            entity_id=transaction.id,
            correlation_id=transaction.correlation_id,
            details_json=json.dumps({
                "transaction_reference": transaction.transaction_reference,
                "account_id": transaction.account_id,
                "amount": str(transaction.amount),
                "currency": transaction.currency,
                "transaction_type": transaction.transaction_type
            })
        )
        db.add(audit_event)
    
    # Create sample audit events for alerts
    for alert in sample_alerts:
        audit_event = AuditEvent(
            timestamp=alert.created_at,
            actor_user_id=None,
            actor_username="system",
            actor_role="system",
            action="ALERT_GENERATED",
            entity_type="alert",
            entity_id=alert.id,
            correlation_id=f"correlation-{alert.id}",
            details_json=json.dumps({
                "alert_number": alert.alert_number,
                "transaction_id": alert.transaction_id,
                "risk_score": alert.risk_score,
                "priority": alert.priority
            })
        )
        db.add(audit_event)
    
    db.commit()
    print(f"Created {len(sample_transactions) + len(sample_alerts)} sample audit events")


def main():
    """Main seed function."""
    print("Starting database seed...")
    
    db = next(get_db())
    
    try:
        print("\n=== Seeding Users ===")
        seed_users(db)
        
        print("\n=== Seeding Detection Rules ===")
        seed_detection_rules(db)
        
        print("\n=== Seeding Country Risk ===")
        seed_country_risk(db)
        
        print("\n=== Seeding Customers and Accounts ===")
        seed_customers_and_accounts(db)
        
        print("\n=== Seeding Sample Transactions ===")
        seed_sample_transactions(db)
        
        print("\n=== Seeding Rule Evaluation Results ===")
        seed_rule_evaluation_results(db)
        
        print("\n=== Seeding Sample Alerts ===")
        seed_sample_alerts(db)
        
        print("\n=== Seeding Sample Cases ===")
        seed_cases(db)
        
        print("\n=== Seeding Audit Events ===")
        seed_audit_events(db)
        
        print("\n✓ Database seeding completed successfully")
        print("\nDefault credentials:")
        print("  analyst@example.com / Analyst-pass-1")
        print("  officer@example.com / Officer-pass-1")
        print("  manager@example.com / Manager-pass-1")
        print("  admin@example.com / Admin-pass-1")
        print("  auditor@example.com / Auditor-pass-1")
        print("\nSample data:")
        print("  4 customers with accounts (CUST-001 through CUST-004)")
        print("  8 AML detection rules (AML-001 through AML-008)")
        print("  8 country risk entries")
        
    finally:
        db.close()


if __name__ == "__main__":
    main()
