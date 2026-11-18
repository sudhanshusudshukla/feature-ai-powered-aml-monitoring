"""Customer domain schemas for API and context structures."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CustomerResponse(BaseModel):
    """Customer summary response."""
    id: int
    customer_number: str
    full_name: str
    residency_country: str
    pep_status: bool
    sanctioned_status: bool
    
    model_config = ConfigDict(from_attributes=True)


class CustomerRiskProfileResponse(BaseModel):
    """Customer risk profile response."""
    id: int
    customer_id: int
    risk_level: str
    base_score: int
    last_reviewed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AccountResponse(BaseModel):
    """Account summary response."""
    id: int
    account_number: str
    customer_id: int
    status: str
    opened_at: datetime
    current_balance: str
    currency: str
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm_with_decimal(cls, account):
        """Create response from ORM model with decimal conversion."""
        return cls(
            id=account.id,
            account_number=account.account_number,
            customer_id=account.customer_id,
            status=account.status,
            opened_at=account.opened_at,
            current_balance=str(account.current_balance),
            currency=account.currency
        )


class HistoricalMetrics(BaseModel):
    """Historical transaction metrics for rule evaluation."""
    rolling_24h_total: Decimal
    rolling_7d_count: int
    rolling_30m_count: int
    rolling_30m_total: Decimal
    rolling_90d_average: Decimal
    cross_border_count: int
    high_risk_country_flag: bool
    prior_alert_count: int
    
    model_config = ConfigDict(from_attributes=True)


class ScreeningContext(BaseModel):
    """Complete screening context for transaction evaluation."""
    account_id: int
    account_number: str
    account_status: str
    customer_id: int
    customer_number: str
    customer_full_name: str
    residency_country: str
    pep_status: bool
    sanctioned_status: bool
    risk_level: str
    risk_base_score: int
    historical_metrics: HistoricalMetrics
    correlation_id: str
    
    model_config = ConfigDict(from_attributes=True)
