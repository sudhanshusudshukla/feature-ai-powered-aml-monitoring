"""Alert service for alert creation and risk scoring."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.alert.models import Alert
from app.alert.repository import AlertRepository
from app.alert.schemas import RiskScoreResult
from app.common.enums import AlertPriority, AlertStatus, RiskLevel
from app.customer.schemas import ScreeningContext
from app.rules.schemas import RuleEvaluationDraft
from app.transaction.models import Transaction


class AlertService:
    """Service for alert creation and risk scoring."""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = AlertRepository(db)
    
    def create_alert_for_matches(
        self,
        transaction: Transaction,
        evaluations: list[RuleEvaluationDraft],
        context: ScreeningContext,
        correlation_id: str
    ) -> Alert | None:
        """
        Create exactly one alert for a transaction with matched rules.
        Returns None if no matches.
        """
        # Filter to matched evaluations only
        matched = [e for e in evaluations if e.outcome == "MATCH"]
        
        if not matched:
            return None
        
        # Compute risk score and priority
        risk_result = self.compute_risk_score(evaluations, context)
        
        # Generate alert number
        alert_number = self.repository.generate_alert_number()
        
        # Create alert
        alert = Alert(
            alert_number=alert_number,
            transaction_id=transaction.id,
            risk_score=risk_result.final_score,
            priority=risk_result.priority,
            status=AlertStatus.NEW.value,
            assigned_to_user_id=None,
            priority_rationale=risk_result.priority_rationale,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=1
        )
        
        persisted = self.repository.create(alert)
        self.db.flush()
        
        return persisted
    
    def compute_risk_score(
        self,
        evaluations: list[RuleEvaluationDraft],
        context: ScreeningContext
    ) -> RiskScoreResult:
        """
        Compute deterministic risk score and priority.
        
        Algorithm:
        1. Sum all matched rule scores
        2. Add customer risk adjustment
        3. Add geography adjustment
        4. Bound to 0-100
        5. Determine priority band
        6. Apply PEP/sanctioned floor (raise to at least HIGH)
        """
        # Base score: sum of all matched rule scores
        matched = [e for e in evaluations if e.outcome == "MATCH"]
        base_score = sum(e.score for e in matched)
        
        # Customer risk adjustment based on risk level
        customer_risk_adjustment = self._get_customer_risk_adjustment(context.risk_level)
        
        # Geography adjustment
        geography_adjustment = self._get_geography_adjustment(context)
        
        # Calculate unbounded score
        unbounded_score = base_score + customer_risk_adjustment + geography_adjustment
        
        # Bound to 0-100
        final_score = max(0, min(100, unbounded_score))
        
        # Determine priority band
        priority = self._determine_priority_band(final_score)
        
        # Apply PEP/sanctioned floor
        if context.pep_status or context.sanctioned_status:
            if priority in [AlertPriority.LOW.value, AlertPriority.MEDIUM.value]:
                priority = AlertPriority.HIGH.value
        
        # Build rationale
        rationale_parts = [
            f"Base score from {len(matched)} matched rules: {base_score}",
            f"Customer risk adjustment ({context.risk_level}): {customer_risk_adjustment:+d}",
            f"Geography adjustment: {geography_adjustment:+d}",
            f"Final score: {final_score}"
        ]
        
        if context.pep_status or context.sanctioned_status:
            rationale_parts.append("Priority raised to HIGH due to PEP/sanctioned status")
        
        priority_rationale = "; ".join(rationale_parts)
        
        return RiskScoreResult(
            base_score=base_score,
            customer_risk_adjustment=customer_risk_adjustment,
            geography_adjustment=geography_adjustment,
            final_score=final_score,
            priority=priority,
            priority_rationale=priority_rationale
        )
    
    def _get_customer_risk_adjustment(self, risk_level: str) -> int:
        """Get adjustment based on customer risk level."""
        adjustments = {
            RiskLevel.LOW.value: 0,
            RiskLevel.MEDIUM.value: 5,
            RiskLevel.HIGH.value: 10,
            RiskLevel.VERY_HIGH.value: 15
        }
        return adjustments.get(risk_level, 0)
    
    def _get_geography_adjustment(self, context: ScreeningContext) -> int:
        """Get adjustment for high-risk geography."""
        if context.historical_metrics.high_risk_country_flag:
            return 10
        return 0
    
    def _determine_priority_band(self, score: int) -> str:
        """
        Determine priority band from score.
        CRITICAL >= 80
        HIGH 60-79
        MEDIUM 35-59
        LOW < 35
        """
        if score >= 80:
            return AlertPriority.CRITICAL.value
        elif score >= 60:
            return AlertPriority.HIGH.value
        elif score >= 35:
            return AlertPriority.MEDIUM.value
        else:
            return AlertPriority.LOW.value
