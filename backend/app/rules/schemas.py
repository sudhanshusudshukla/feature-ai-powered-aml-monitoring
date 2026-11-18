"""Rules domain schemas for evaluation and versioning."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RuleParameters(BaseModel):
    """Rule version parameters."""
    model_config = ConfigDict(extra="allow")


class RuleVersionResponse(BaseModel):
    """Rule version response."""
    id: int
    rule_id: int
    version_number: int
    parameters_json: dict
    effective_from: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RuleEvaluationDraft(BaseModel):
    """Draft rule evaluation result before persistence."""
    rule_code: str
    rule_name: str
    rule_version: int
    outcome: str  # PASS or MATCH
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    score: int  # 0-100
    explanation: str
    evidence_snapshot: dict


class EvaluationBatchResult(BaseModel):
    """Batch evaluation result for all rules."""
    results: list[RuleEvaluationDraft]
    matched_rules_count: int
    max_rule_score: int
    any_match: bool
    failed_rules: list[str] = Field(default_factory=list)
