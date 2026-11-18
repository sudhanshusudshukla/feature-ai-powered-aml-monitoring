"""Dashboard schemas for KPI and summary statistics."""
from pydantic import BaseModel, ConfigDict


class KPICounts(BaseModel):
    """KPI count metrics."""
    total_alerts: int
    new_alerts: int
    open_cases: int
    high_priority_alerts: int
    transactions_today: int
    rules_active: int


class ChartDataPoint(BaseModel):
    """Single chart data point."""
    label: str
    value: int


class DashboardSummaryResponse(BaseModel):
    """Dashboard summary with KPIs and chart data."""
    model_config = ConfigDict(from_attributes=True)
    
    kpis: KPICounts
    alerts_by_priority: list[ChartDataPoint]
    alerts_by_status: list[ChartDataPoint]
    cases_by_state: list[ChartDataPoint]
    transactions_by_type: list[ChartDataPoint]
