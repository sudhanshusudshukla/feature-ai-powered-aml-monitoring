"""Alert domain schemas for alert creation and risk scoring."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RiskScoreResult(BaseModel):
    """Risk score calculation result."""
    base_score: int = Field(..., description="Base score from matched rules")
    customer_risk_adjustment: int = Field(..., description="Customer risk level adjustment")
    geography_adjustment: int = Field(..., description="High-risk geography adjustment")
    final_score: int = Field(..., ge=0, le=100, description="Final bounded risk score")
    priority: str = Field(..., description="Computed priority band")
    priority_rationale: str = Field(..., description="Explanation of priority determination")


class RuleEvaluationSummary(BaseModel):
    """Rule evaluation result summary for alert detail."""
    model_config = ConfigDict(from_attributes=True)
    
    rule_code: str
    rule_name: str
    rule_version: int
    outcome: str
    severity: str
    score: int
    explanation: str
    evidence_snapshot: dict


class TransactionSummary(BaseModel):
    """Transaction summary for alert detail."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    transaction_reference: str
    amount: str
    currency: str
    transaction_type: str
    origin_country: str
    destination_country: str
    timestamp: datetime


class CustomerSnapshotData(BaseModel):
    """Customer snapshot for alert detail."""
    customer_id: int
    customer_number: str
    full_name: str
    residency_country: str
    pep_status: bool
    sanctioned_status: bool
    risk_level: str
    account_number: str
    account_status: str


class AlertListItem(BaseModel):
    """Alert list item for paginated list endpoint."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    alert_number: str
    transaction_id: int
    risk_score: int
    priority: str
    status: str
    created_at: datetime
    assigned_to_user_id: Optional[int] = None
    customer_name: str
    transaction_reference: str
    transaction_amount: str
    transaction_currency: str


class AlertDetailResponse(BaseModel):
    """Complete alert detail response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    alert_number: str
    transaction_id: int
    risk_score: int
    priority: str
    status: str
    created_at: datetime
    priority_rationale: str
    assigned_to_user_id: int | None
    
    # Risk score breakdown
    base_score: int
    customer_risk_adjustment: int
    geography_adjustment: int
    
    # Related data
    transaction: TransactionSummary
    matched_rules: list[RuleEvaluationSummary]
    customer_snapshot: CustomerSnapshotData
