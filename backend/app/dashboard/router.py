"""Dashboard API router."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.alert.models import Alert
from app.case_management.models import AMLCase
from app.dashboard.schemas import ChartDataPoint, DashboardSummaryResponse, KPICounts
from app.database import get_db
from app.rules.models import DetectionRule
from app.security.dependencies import get_current_user
from app.security.models import User
from app.transaction.models import Transaction

router = APIRouter()


@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard summary with KPI counts and chart data.
    
    Requires authentication.
    """
    # Calculate today's start
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # KPI counts
    total_alerts = db.query(func.count(Alert.id)).scalar()
    new_alerts = db.query(func.count(Alert.id)).filter(Alert.status == "NEW").scalar()
    open_cases = db.query(func.count(AMLCase.id)).filter(
        AMLCase.state.in_(["OPEN", "UNDER_INVESTIGATION", "INFORMATION_REQUESTED", "PENDING_DECISION"])
    ).scalar()
    high_priority_alerts = db.query(func.count(Alert.id)).filter(
        Alert.priority.in_(["HIGH", "CRITICAL"])
    ).scalar()
    transactions_today = db.query(func.count(Transaction.id)).filter(
        Transaction.transaction_timestamp >= today_start
    ).scalar()
    rules_active = db.query(func.count(DetectionRule.id)).filter(
        DetectionRule.is_active == True
    ).scalar()
    
    kpis = KPICounts(
        total_alerts=total_alerts or 0,
        new_alerts=new_alerts or 0,
        open_cases=open_cases or 0,
        high_priority_alerts=high_priority_alerts or 0,
        transactions_today=transactions_today or 0,
        rules_active=rules_active or 0
    )
    
    # Alerts by priority
    alerts_by_priority_data = db.query(
        Alert.priority,
        func.count(Alert.id)
    ).group_by(Alert.priority).all()
    
    alerts_by_priority = [
        ChartDataPoint(label=priority, value=count)
        for priority, count in alerts_by_priority_data
    ]
    
    # Alerts by status
    alerts_by_status_data = db.query(
        Alert.status,
        func.count(Alert.id)
    ).group_by(Alert.status).all()
    
    alerts_by_status = [
        ChartDataPoint(label=status, value=count)
        for status, count in alerts_by_status_data
    ]
    
    # Cases by state
    cases_by_state_data = db.query(
        AMLCase.state,
        func.count(AMLCase.id)
    ).group_by(AMLCase.state).all()
    
    cases_by_state = [
        ChartDataPoint(label=state, value=count)
        for state, count in cases_by_state_data
    ]
    
    # Transactions by type
    transactions_by_type_data = db.query(
        Transaction.transaction_type,
        func.count(Transaction.id)
    ).group_by(Transaction.transaction_type).all()
    
    transactions_by_type = [
        ChartDataPoint(label=tx_type, value=count)
        for tx_type, count in transactions_by_type_data
    ]
    
    return DashboardSummaryResponse(
        kpis=kpis,
        alerts_by_priority=alerts_by_priority,
        alerts_by_status=alerts_by_status,
        cases_by_state=cases_by_state,
        transactions_by_type=transactions_by_type
    )
