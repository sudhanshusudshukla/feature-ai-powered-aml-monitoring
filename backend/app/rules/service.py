"""Rules service for rule evaluation orchestration."""
import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.common.enums import RuleOutcome
from app.common.errors import RuleEvaluationFailureError
from app.customer.schemas import ScreeningContext
from app.rules.evaluators import (
    AMLRuleEvaluator,
    DormancySpikeEvaluator,
    HighRiskGeographyEvaluator,
    HighValueTransactionEvaluator,
    RoundAmountPatternEvaluator,
    SanctionedOrPepEvaluator,
    StructuringEvaluator,
    VelocityAmountEvaluator,
    VelocityCountEvaluator,
)
from app.rules.models import RuleEvaluationResult
from app.rules.repository import RulesRepository
from app.rules.schemas import EvaluationBatchResult, RuleEvaluationDraft
from app.transaction.models import Transaction


class RulesService:
    """Service for rule evaluation orchestration."""
    
    # Define all eight evaluators
    EVALUATORS: list[AMLRuleEvaluator] = [
        HighValueTransactionEvaluator(),
        VelocityCountEvaluator(),
        VelocityAmountEvaluator(),
        HighRiskGeographyEvaluator(),
        SanctionedOrPepEvaluator(),
        StructuringEvaluator(),
        DormancySpikeEvaluator(),
        RoundAmountPatternEvaluator(),
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = RulesRepository(db)
    
    def evaluate_all(
        self,
        transaction: Transaction,
        context: ScreeningContext
    ) -> EvaluationBatchResult:
        """
        Evaluate all eight AML rules against the transaction.
        
        Returns batch result with all evaluations.
        Raises RuleEvaluationFailureError if any evaluator fails.
        """
        # Get current rule versions
        rule_versions = self.repository.get_all_current_versions()
        
        results: list[RuleEvaluationDraft] = []
        failed_rules: list[str] = []
        
        # Evaluate each rule
        for evaluator in self.EVALUATORS:
            rule_code = evaluator.rule_code()
            
            try:
                # Get rule version
                if rule_code not in rule_versions:
                    failed_rules.append(rule_code)
                    raise RuleEvaluationFailureError(
                        f"No active version found for rule {rule_code}"
                    )
                
                rule_version = rule_versions[rule_code]
                
                # Evaluate
                draft = evaluator.evaluate(transaction, context, rule_version)
                results.append(draft)
                
                # Persist evaluation result immediately
                self._persist_evaluation(transaction, draft, rule_version.rule_id)
                
            except Exception as e:
                failed_rules.append(rule_code)
                # Single rule failure causes entire ingestion to fail
                raise RuleEvaluationFailureError(
                    f"Rule evaluation failed for {rule_code}: {e!s}"
                )
        
        # Compute aggregate metrics
        matched_rules = [r for r in results if r.outcome == RuleOutcome.MATCH.value]
        matched_rules_count = len(matched_rules)
        max_rule_score = max([r.score for r in matched_rules], default=0)
        any_match = matched_rules_count > 0
        
        return EvaluationBatchResult(
            results=results,
            matched_rules_count=matched_rules_count,
            max_rule_score=max_rule_score,
            any_match=any_match,
            failed_rules=failed_rules
        )
    
    def _persist_evaluation(
        self,
        transaction: Transaction,
        draft: RuleEvaluationDraft,
        rule_id: int
    ) -> None:
        """Persist a single rule evaluation result."""
        result = RuleEvaluationResult(
            transaction_id=transaction.id,
            rule_id=rule_id,
            rule_code=draft.rule_code,
            rule_version=draft.rule_version,
            result=draft.outcome,
            severity=draft.severity,
            score=draft.score,
            explanation=draft.explanation,
            evidence_snapshot=json.dumps(draft.evidence_snapshot),
            created_at=datetime.utcnow()
        )
        self.db.add(result)
        # Flush to ensure persistence within transaction
        self.db.flush()
