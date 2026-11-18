"""AML rule evaluator classes for deterministic evaluation."""
import json
from abc import ABC, abstractmethod
from decimal import Decimal

from app.common.enums import RuleOutcome, RuleSeverity
from app.customer.schemas import ScreeningContext
from app.rules.models import RuleVersion
from app.rules.schemas import RuleEvaluationDraft
from app.transaction.models import Transaction


class AMLRuleEvaluator(ABC):
    """Base interface for AML rule evaluators."""
    
    @abstractmethod
    def rule_code(self) -> str:
        """Return rule code identifier."""
    
    @abstractmethod
    def rule_name(self) -> str:
        """Return display name for the rule."""
    
    @abstractmethod
    def evaluate(
        self,
        transaction: Transaction,
        context: ScreeningContext,
        rule_version: RuleVersion
    ) -> RuleEvaluationDraft:
        """
        Evaluate the rule against the transaction and context.
        Returns a draft evaluation result.
        """


class HighValueTransactionEvaluator(AMLRuleEvaluator):
    """AML-001: High Value Transaction Detection."""
    
    def rule_code(self) -> str:
        return "AML-001"
    
    def rule_name(self) -> str:
        return "High Value Transaction"
    
    def evaluate(
        self,
        transaction: Transaction,
        context: ScreeningContext,
        rule_version: RuleVersion
    ) -> RuleEvaluationDraft:
        params = json.loads(rule_version.parameters_json)
        threshold = Decimal(str(params.get("threshold", 100000)))
        
        outcome = RuleOutcome.MATCH if transaction.amount >= threshold else RuleOutcome.PASS
        severity = RuleSeverity.HIGH if outcome == RuleOutcome.MATCH else RuleSeverity.LOW
        score = 30 if outcome == RuleOutcome.MATCH else 0
        
        explanation = (
            f"Transaction amount {transaction.amount} {transaction.currency} "
            f"{'exceeds' if outcome == RuleOutcome.MATCH else 'is below'} "
            f"threshold {threshold} {transaction.currency}."
        )
        
        evidence = {
            "transaction_amount": str(transaction.amount),
            "currency": transaction.currency,
            "threshold": str(threshold)
        }
        
        return RuleEvaluationDraft(
            rule_code=self.rule_code(),
            rule_name=self.rule_name(),
            rule_version=rule_version.version_number,
            outcome=outcome.value,
            severity=severity.value,
            score=score,
            explanation=explanation,
            evidence_snapshot=evidence
        )


class VelocityCountEvaluator(AMLRuleEvaluator):
    """AML-002: Transaction Velocity by Count."""
    
    def rule_code(self) -> str:
        return "AML-002"
    
    def rule_name(self) -> str:
        return "Transaction Velocity (Count)"
    
    def evaluate(
        self,
        transaction: Transaction,
        context: ScreeningContext,
        rule_version: RuleVersion
    ) -> RuleEvaluationDraft:
        params = json.loads(rule_version.parameters_json)
        threshold_7d = params.get("threshold_7d_count", 10)
        
        actual_count = context.historical_metrics.rolling_7d_count + 1  # Include current
        
        outcome = RuleOutcome.MATCH if actual_count > threshold_7d else RuleOutcome.PASS
        severity = RuleSeverity.MEDIUM if outcome == RuleOutcome.MATCH else RuleSeverity.LOW
        score = 20 if outcome == RuleOutcome.MATCH else 0
        
        explanation = (
            f"Transaction count in 7-day window is {actual_count}, "
            f"{'exceeding' if outcome == RuleOutcome.MATCH else 'within'} "
            f"threshold of {threshold_7d}."
        )
        
        evidence = {
            "rolling_7d_count": actual_count,
            "threshold": threshold_7d
        }
        
        return RuleEvaluationDraft(
            rule_code=self.rule_code(),
            rule_name=self.rule_name(),
            rule_version=rule_version.version_number,
            outcome=outcome.value,
            severity=severity.value,
            score=score,
            explanation=explanation,
            evidence_snapshot=evidence
        )


class VelocityAmountEvaluator(AMLRuleEvaluator):
    """AML-003: Transaction Velocity by Amount."""
    
    def rule_code(self) -> str:
        return "AML-003"
    
    def rule_name(self) -> str:
        return "Transaction Velocity (Amount)"
    
    def evaluate(
        self,
        transaction: Transaction,
        context: ScreeningContext,
        rule_version: RuleVersion
    ) -> RuleEvaluationDraft:
        params = json.loads(rule_version.parameters_json)
        threshold_24h = Decimal(str(params.get("threshold_24h_total", 500000)))
        
        actual_total = context.historical_metrics.rolling_24h_total + transaction.amount
        
        outcome = RuleOutcome.MATCH if actual_total > threshold_24h else RuleOutcome.PASS
        severity = RuleSeverity.HIGH if outcome == RuleOutcome.MATCH else RuleSeverity.LOW
        score = 25 if outcome == RuleOutcome.MATCH else 0
        
        explanation = (
            f"Total amount in 24-hour window is {actual_total} {transaction.currency}, "
            f"{'exceeding' if outcome == RuleOutcome.MATCH else 'within'} "
            f"threshold of {threshold_24h}."
        )
        
        evidence = {
            "rolling_24h_total": str(actual_total),
            "currency": transaction.currency,
            "threshold": str(threshold_24h)
        }
        
        return RuleEvaluationDraft(
            rule_code=self.rule_code(),
            rule_name=self.rule_name(),
            rule_version=rule_version.version_number,
            outcome=outcome.value,
            severity=severity.value,
            score=score,
            explanation=explanation,
            evidence_snapshot=evidence
        )


class HighRiskGeographyEvaluator(AMLRuleEvaluator):
    """AML-004: High Risk Geography Detection."""
    
    def rule_code(self) -> str:
        return "AML-004"
    
    def rule_name(self) -> str:
        return "High Risk Geography"
    
    def evaluate(
        self,
        transaction: Transaction,
        context: ScreeningContext,
        rule_version: RuleVersion
    ) -> RuleEvaluationDraft:
        # Check if high_risk_country_flag is already set in context
        is_high_risk = context.historical_metrics.high_risk_country_flag
        
        outcome = RuleOutcome.MATCH if is_high_risk else RuleOutcome.PASS
        severity = RuleSeverity.MEDIUM if outcome == RuleOutcome.MATCH else RuleSeverity.LOW
        score = 20 if outcome == RuleOutcome.MATCH else 0
        
        explanation = (
            f"Transaction involves "
            f"{'high-risk' if is_high_risk else 'standard-risk'} "
            f"geography (origin: {transaction.origin_country}, "
            f"destination: {transaction.destination_country})."
        )
        
        evidence = {
            "origin_country": transaction.origin_country,
            "destination_country": transaction.destination_country,
            "high_risk_flag": is_high_risk
        }
        
        return RuleEvaluationDraft(
            rule_code=self.rule_code(),
            rule_name=self.rule_name(),
            rule_version=rule_version.version_number,
            outcome=outcome.value,
            severity=severity.value,
            score=score,
            explanation=explanation,
            evidence_snapshot=evidence
        )


class SanctionedOrPepEvaluator(AMLRuleEvaluator):
    """AML-005: Sanctioned or PEP Customer Detection."""
    
    def rule_code(self) -> str:
        return "AML-005"
    
    def rule_name(self) -> str:
        return "Sanctioned or PEP Customer"
    
    def evaluate(
        self,
        transaction: Transaction,
        context: ScreeningContext,
        rule_version: RuleVersion
    ) -> RuleEvaluationDraft:
        is_pep = context.pep_status
        is_sanctioned = context.sanctioned_status
        
        outcome = RuleOutcome.MATCH if (is_pep or is_sanctioned) else RuleOutcome.PASS
        severity = RuleSeverity.CRITICAL if outcome == RuleOutcome.MATCH else RuleSeverity.LOW
        score = 40 if outcome == RuleOutcome.MATCH else 0
        
        status_desc = []
        if is_pep:
            status_desc.append("PEP")
        if is_sanctioned:
            status_desc.append("sanctioned")
        
        explanation = (
            f"Customer {context.customer_number} is "
            f"{'flagged as ' + ' and '.join(status_desc) if outcome == RuleOutcome.MATCH else 'not flagged as PEP or sanctioned'}."
        )
        
        evidence = {
            "customer_id": context.customer_id,
            "customer_number": context.customer_number,
            "pep_status": is_pep,
            "sanctioned_status": is_sanctioned
        }
        
        return RuleEvaluationDraft(
            rule_code=self.rule_code(),
            rule_name=self.rule_name(),
            rule_version=rule_version.version_number,
            outcome=outcome.value,
            severity=severity.value,
            score=score,
            explanation=explanation,
            evidence_snapshot=evidence
        )


class StructuringEvaluator(AMLRuleEvaluator):
    """AML-006: Structuring Pattern Detection."""
    
    def rule_code(self) -> str:
        return "AML-006"
    
    def rule_name(self) -> str:
        return "Structuring Pattern"
    
    def evaluate(
        self,
        transaction: Transaction,
        context: ScreeningContext,
        rule_version: RuleVersion
    ) -> RuleEvaluationDraft:
        params = json.loads(rule_version.parameters_json)
        count_threshold = params.get("count_threshold_30m", 5)
        amount_below_threshold = Decimal(str(params.get("amount_below_threshold", 50000)))
        
        count_30m = context.historical_metrics.rolling_30m_count + 1  # Include current
        is_below_threshold = transaction.amount < amount_below_threshold
        
        outcome = RuleOutcome.MATCH if (count_30m >= count_threshold and is_below_threshold) else RuleOutcome.PASS
        severity = RuleSeverity.HIGH if outcome == RuleOutcome.MATCH else RuleSeverity.LOW
        score = 35 if outcome == RuleOutcome.MATCH else 0
        
        explanation = (
            f"{'Pattern detected: ' if outcome == RuleOutcome.MATCH else 'No structuring pattern. '}"
            f"{count_30m} transactions in 30-minute window, "
            f"current amount {transaction.amount} {transaction.currency} "
            f"{'below' if is_below_threshold else 'above'} threshold {amount_below_threshold}."
        )
        
        evidence = {
            "rolling_30m_count": count_30m,
            "transaction_amount": str(transaction.amount),
            "amount_threshold": str(amount_below_threshold),
            "count_threshold": count_threshold
        }
        
        return RuleEvaluationDraft(
            rule_code=self.rule_code(),
            rule_name=self.rule_name(),
            rule_version=rule_version.version_number,
            outcome=outcome.value,
            severity=severity.value,
            score=score,
            explanation=explanation,
            evidence_snapshot=evidence
        )


class DormancySpikeEvaluator(AMLRuleEvaluator):
    """AML-007: Dormancy Spike Detection."""
    
    def rule_code(self) -> str:
        return "AML-007"
    
    def rule_name(self) -> str:
        return "Dormancy Spike"
    
    def evaluate(
        self,
        transaction: Transaction,
        context: ScreeningContext,
        rule_version: RuleVersion
    ) -> RuleEvaluationDraft:
        params = json.loads(rule_version.parameters_json)
        spike_multiplier = Decimal(str(params.get("spike_multiplier", 5.0)))
        
        avg_90d = context.historical_metrics.rolling_90d_average
        current_amount = transaction.amount
        
        # Spike if current transaction is significantly higher than 90-day average
        # Note: Only detect spike when there IS a historical baseline (avg_90d > 0)
        # If avg_90d == 0, this is a new/dormant account with no history - not a spike
        is_spike = avg_90d > 0 and current_amount >= avg_90d * spike_multiplier
        
        outcome = RuleOutcome.MATCH if is_spike else RuleOutcome.PASS
        severity = RuleSeverity.MEDIUM if outcome == RuleOutcome.MATCH else RuleSeverity.LOW
        score = 25 if outcome == RuleOutcome.MATCH else 0
        
        explanation = (
            f"Transaction amount {current_amount} {transaction.currency} "
            f"{'represents a significant spike' if is_spike else 'is consistent with'} "
            f"compared to 90-day average {avg_90d} {transaction.currency}."
        )
        
        evidence = {
            "transaction_amount": str(current_amount),
            "rolling_90d_average": str(avg_90d),
            "spike_multiplier": str(spike_multiplier)
        }
        
        return RuleEvaluationDraft(
            rule_code=self.rule_code(),
            rule_name=self.rule_name(),
            rule_version=rule_version.version_number,
            outcome=outcome.value,
            severity=severity.value,
            score=score,
            explanation=explanation,
            evidence_snapshot=evidence
        )


class RoundAmountPatternEvaluator(AMLRuleEvaluator):
    """AML-008: Round Amount Pattern Detection."""
    
    def rule_code(self) -> str:
        return "AML-008"
    
    def rule_name(self) -> str:
        return "Round Amount Pattern"
    
    def evaluate(
        self,
        transaction: Transaction,
        context: ScreeningContext,
        rule_version: RuleVersion
    ) -> RuleEvaluationDraft:
        params = json.loads(rule_version.parameters_json)
        min_round_amount = Decimal(str(params.get("min_round_amount", 10000)))
        
        amount = transaction.amount
        # Check if amount is a round number (divisible by min_round_amount)
        is_round = amount >= min_round_amount and (amount % min_round_amount == 0)
        
        outcome = RuleOutcome.MATCH if is_round else RuleOutcome.PASS
        severity = RuleSeverity.LOW if outcome == RuleOutcome.MATCH else RuleSeverity.LOW
        score = 10 if outcome == RuleOutcome.MATCH else 0
        
        explanation = (
            f"Transaction amount {amount} {transaction.currency} "
            f"{f'is a round number (divisible by {min_round_amount})' if is_round else 'is not a suspicious round amount'}."
        )
        
        evidence = {
            "transaction_amount": str(amount),
            "min_round_amount": str(min_round_amount),
            "is_round": is_round
        }
        
        return RuleEvaluationDraft(
            rule_code=self.rule_code(),
            rule_name=self.rule_name(),
            rule_version=rule_version.version_number,
            outcome=outcome.value,
            severity=severity.value,
            score=score,
            explanation=explanation,
            evidence_snapshot=evidence
        )
