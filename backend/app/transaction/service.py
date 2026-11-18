"""Transaction service for ingestion orchestration."""
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.alert.service import AlertService
from app.audit.service import AuditService
from app.common.errors import NotFoundError
from app.customer.repository import AccountRepository
from app.rules.service import RulesService
from app.transaction.models import Transaction
from app.transaction.repository import TransactionRepository
from app.transaction.schemas import (
    RuleEvaluationItem,
    TransactionDetailResponse,
    TransactionIngestRequest,
    TransactionIngestResponse,
)


class TransactionService:
    """Service for transaction ingestion and detail retrieval."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = TransactionRepository(db)
        self.account_repository = AccountRepository(db)
        self.rules_service = RulesService(db)
        self.alert_service = AlertService(db)
        self.audit_service = AuditService(db)
    
    def ingest_transaction(
        self,
        dto: TransactionIngestRequest,
        correlation_id: str
    ) -> TransactionIngestResponse:
        """
        Ingest a new transaction.
        
        Steps:
        - Load account screening context (validates account exists)
        - Persist transaction
        - Write TRANSACTION_INGESTED audit event
        - Evaluate all 8 rules
        - Write RULE_EVALUATED audit events
        - Create alert if any rules match
        - Write ALERT_GENERATED audit event if alert created
        - Commit all changes atomically
        - Return created response
        """
        # Load screening context (validates account exists and loads customer/risk data)
        screening_context = self.account_repository.get_screening_context(
            account_id=dto.account_id,
            correlation_id=correlation_id
        )
        
        # Create transaction entity
        transaction = Transaction(
            transaction_reference=dto.transaction_reference,
            account_id=dto.account_id,
            amount=dto.amount,
            currency=dto.currency,
            transaction_type=dto.transaction_type,
            origin_country=dto.origin_country,
            destination_country=dto.destination_country,
            counterparty_name=dto.counterparty_name,
            counterparty_account=dto.counterparty_account,
            transaction_timestamp=dto.timestamp,
            correlation_id=correlation_id,
            created_at=datetime.utcnow()
        )
        
        # Persist transaction
        persisted = self.repository.create(transaction)
        self.db.flush()
        
        # Record TRANSACTION_INGESTED audit event
        self.audit_service.record_event(
            action="TRANSACTION_INGESTED",
            entity_type="transaction",
            entity_id=persisted.id,
            correlation_id=correlation_id,
            details={
                "transaction_reference": persisted.transaction_reference,
                "account_id": persisted.account_id,
                "amount": str(persisted.amount),
                "currency": persisted.currency,
                "transaction_type": persisted.transaction_type,
                "origin_country": persisted.origin_country,
                "destination_country": persisted.destination_country
            }
        )
        
        # Evaluate all 8 rules
        evaluation_batch = self.rules_service.evaluate_all(persisted, screening_context)
        
        # Record RULE_EVALUATED audit event for each rule
        for draft in evaluation_batch.results:
            self.audit_service.record_event(
                action="RULE_EVALUATED",
                entity_type="transaction",
                entity_id=persisted.id,
                correlation_id=correlation_id,
                details={
                    "rule_code": draft.rule_code,
                    "rule_name": draft.rule_name,
                    "rule_version": draft.rule_version,
                    "outcome": draft.outcome,
                    "severity": draft.severity,
                    "score": draft.score,
                    "explanation": draft.explanation
                }
            )
        
        # Create alert if any matches
        alert = None
        if evaluation_batch.any_match:
            alert = self.alert_service.create_alert_for_matches(
                persisted,
                evaluation_batch.results,
                screening_context,
                correlation_id
            )
            
            # Record ALERT_GENERATED audit event
            self.audit_service.record_event(
                action="ALERT_GENERATED",
                entity_type="alert",
                entity_id=alert.id,
                correlation_id=correlation_id,
                details={
                    "alert_number": alert.alert_number,
                    "transaction_id": persisted.id,
                    "risk_score": alert.risk_score,
                    "priority": alert.priority,
                    "matched_rules_count": evaluation_batch.matched_rules_count
                }
            )
        
        # Commit all changes atomically
        self.db.commit()
        
        # Convert evaluation results to response items
        evaluation_items = [
            RuleEvaluationItem(
                rule_code=draft.rule_code,
                rule_name=draft.rule_name,
                rule_version=draft.rule_version,
                outcome=draft.outcome,
                severity=draft.severity,
                score=draft.score,
                explanation=draft.explanation,
                evidence_snapshot=draft.evidence_snapshot
            )
            for draft in evaluation_batch.results
        ]
        
        return TransactionIngestResponse(
            id=persisted.id,
            transaction_reference=persisted.transaction_reference,
            account_id=persisted.account_id,
            amount=str(persisted.amount),
            currency=persisted.currency,
            transaction_type=persisted.transaction_type,
            origin_country=persisted.origin_country,
            destination_country=persisted.destination_country,
            timestamp=persisted.transaction_timestamp,
            matched_rules_count=evaluation_batch.matched_rules_count,
            alert_raised=alert is not None,
            alert_id=alert.id if alert else None,
            correlation_id=persisted.correlation_id,
            evaluation_results=evaluation_items
        )
    
    def get_transaction_detail(self, transaction_id: int) -> TransactionDetailResponse:
        """
        Retrieve transaction detail.
        Returns full transaction with evaluation results.
        """
        transaction = self.repository.get_by_id(transaction_id)
        if not transaction:
            raise NotFoundError("Transaction not found")
        
        # Load evaluation results from database
        evaluation_items = []
        matched_count = 0
        
        for result in transaction.evaluation_results:
            evaluation_items.append(
                RuleEvaluationItem(
                    rule_code=result.rule_code,
                    rule_name=result.rule.name,
                    rule_version=result.rule_version,
                    outcome=result.result,
                    severity=result.severity,
                    score=result.score,
                    explanation=result.explanation,
                    evidence_snapshot=json.loads(result.evidence_snapshot)
                )
            )
            if result.result == "MATCH":
                matched_count += 1
        
        # Check if alert exists
        alert = None
        if transaction.alert:
            alert = transaction.alert
        
        return TransactionDetailResponse(
            id=transaction.id,
            transaction_reference=transaction.transaction_reference,
            account_id=transaction.account_id,
            amount=str(transaction.amount),
            currency=transaction.currency,
            transaction_type=transaction.transaction_type,
            origin_country=transaction.origin_country,
            destination_country=transaction.destination_country,
            counterparty_name=transaction.counterparty_name,
            counterparty_account=transaction.counterparty_account,
            timestamp=transaction.transaction_timestamp,
            matched_rules_count=matched_count,
            alert_raised=alert is not None,
            alert_id=alert.id if alert else None,
            evaluation_results=evaluation_items,
            correlation_id=transaction.correlation_id
        )
