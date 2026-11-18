"""Transaction request and response schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TransactionIngestRequest(BaseModel):
    """Request schema for transaction ingestion."""
    transaction_reference: str = Field(..., min_length=1, max_length=100, description="External/business reference")
    account_id: int = Field(..., gt=0, description="Owning account ID")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Transaction amount")
    currency: str = Field(default="INR", min_length=3, max_length=3, description="Transaction currency")
    transaction_type: str = Field(..., description="TRANSFER, DEPOSIT, WITHDRAWAL, or PAYMENT")
    origin_country: str = Field(..., min_length=2, max_length=2, description="Origin country code")
    destination_country: str = Field(..., min_length=2, max_length=2, description="Destination country code")
    counterparty_name: str | None = Field(None, max_length=255, description="Optional counterparty name")
    counterparty_account: str | None = Field(None, max_length=100, description="Optional counterparty account")
    timestamp: datetime = Field(..., description="Transaction occurrence time")


class TransactionListItem(BaseModel):
    """Transaction list item for paginated list endpoint."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    transaction_reference: str
    account_id: int
    customer_name: str
    amount: str
    currency: str
    transaction_type: str
    origin_country: str
    destination_country: str
    timestamp: datetime
    matched_rules_count: int
    alert_raised: bool
    alert_id: Optional[int] = None


class RuleEvaluationItem(BaseModel):
    """Single rule evaluation result."""
    rule_code: str = Field(..., description="Rule code AML-001..AML-008")
    rule_name: str = Field(..., description="Display name")
    rule_version: int = Field(..., description="Parameter version used")
    outcome: str = Field(..., description="PASS or MATCH")
    severity: str = Field(..., description="LOW, MEDIUM, HIGH, or CRITICAL")
    score: int = Field(..., ge=0, le=100, description="Score contribution 0-100")
    explanation: str = Field(..., description="Plain-language rationale")
    evidence_snapshot: dict = Field(..., description="Serialized reconstruction inputs")
    
    model_config = ConfigDict(from_attributes=True)


class TransactionIngestResponse(BaseModel):
    """Response schema for transaction ingestion."""
    id: int = Field(..., description="Persisted transaction ID")
    transaction_reference: str = Field(..., description="External reference")
    account_id: int = Field(..., description="Account ID")
    amount: str = Field(..., description="Exact amount as string")
    currency: str = Field(..., description="Transaction currency")
    transaction_type: str = Field(..., description="Transaction type")
    origin_country: str = Field(..., description="Origin country")
    destination_country: str = Field(..., description="Destination country")
    timestamp: datetime = Field(..., description="Transaction timestamp")
    matched_rules_count: int = Field(..., description="Number of MATCH outcomes")
    alert_raised: bool = Field(..., description="Whether alert was created")
    alert_id: int | None = Field(None, description="Alert ID if raised")
    correlation_id: str = Field(..., description="Workflow trace ID")
    evaluation_results: list[RuleEvaluationItem] = Field(..., description="Exactly 8 evaluation results")
    
    model_config = ConfigDict(from_attributes=True)


class TransactionDetailResponse(BaseModel):
    """Response schema for transaction detail retrieval."""
    id: int = Field(..., description="Transaction ID")
    transaction_reference: str = Field(..., description="External reference")
    account_id: int = Field(..., description="Account ID")
    amount: str = Field(..., description="Exact amount as string")
    currency: str = Field(..., description="Transaction currency")
    transaction_type: str = Field(..., description="Transaction type")
    origin_country: str = Field(..., description="Origin country")
    destination_country: str = Field(..., description="Destination country")
    counterparty_name: str | None = Field(None, description="Counterparty name")
    counterparty_account: str | None = Field(None, description="Counterparty account")
    timestamp: datetime = Field(..., description="Transaction timestamp")
    matched_rules_count: int = Field(..., description="Count of MATCH outcomes")
    alert_raised: bool = Field(..., description="Whether alert exists")
    alert_id: int | None = Field(None, description="Linked alert ID")
    evaluation_results: list[RuleEvaluationItem] = Field(..., description="8 evaluation results")
    correlation_id: str = Field(..., description="Workflow trace ID")
    
    model_config = ConfigDict(from_attributes=True)
