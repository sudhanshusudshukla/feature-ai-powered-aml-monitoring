"""Customer repository for database operations."""
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.alert.models import Alert
from app.common.errors import NotFoundError
from app.customer.models import Account, Customer
from app.customer.schemas import HistoricalMetrics, ScreeningContext
from app.risk.models import CountryRisk
from app.transaction.models import Transaction


class CustomerRepository:
    """Repository for customer-related database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_customer_by_id(self, customer_id: int) -> Customer | None:
        """Retrieve customer by ID with eager-loaded risk profile."""
        return (
            self.db.query(Customer)
            .options(joinedload(Customer.risk_profile))
            .filter(Customer.id == customer_id)
            .first()
        )
    
    def get_account_by_id(self, account_id: int) -> Account | None:
        """Retrieve account by ID with eager-loaded customer and risk profile."""
        return (
            self.db.query(Account)
            .options(
                joinedload(Account.customer).joinedload(Customer.risk_profile)
            )
            .filter(Account.id == account_id)
            .first()
        )


class AccountRepository:
    """Repository for account context and transaction history."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_screening_context(self, account_id: int, correlation_id: str) -> ScreeningContext:
        """
        Retrieve complete screening context for an account.
        
        Loads account, customer, risk profile, and computes historical metrics.
        Raises NotFoundError if account does not exist.
        """
        # Load account with customer and risk profile
        account = (
            self.db.query(Account)
            .options(
                joinedload(Account.customer).joinedload(Customer.risk_profile)
            )
            .filter(Account.id == account_id)
            .first()
        )
        
        if not account:
            raise NotFoundError("Account not found")
        
        if not account.customer:
            raise NotFoundError("Customer not found for account")
        
        if not account.customer.risk_profile:
            raise NotFoundError("Risk profile not found for customer")
        
        # Compute historical metrics
        metrics = self.get_transaction_window_metrics(
            account_id=account.id,
            customer_id=account.customer.id,
            as_of=datetime.utcnow()
        )
        
        # Build screening context
        return ScreeningContext(
            account_id=account.id,
            account_number=account.account_number,
            account_status=account.status,
            customer_id=account.customer.id,
            customer_number=account.customer.customer_number,
            customer_full_name=account.customer.full_name,
            residency_country=account.customer.residency_country,
            pep_status=account.customer.pep_status,
            sanctioned_status=account.customer.sanctioned_status,
            risk_level=account.customer.risk_profile.risk_level,
            risk_base_score=account.customer.risk_profile.base_score,
            historical_metrics=metrics,
            correlation_id=correlation_id
        )
    
    def get_transaction_window_metrics(
        self,
        account_id: int,
        customer_id: int,
        as_of: datetime
    ) -> HistoricalMetrics:
        """
        Compute historical transaction metrics for rule evaluation.
        
        Returns metrics for:
        - rolling_24h_total: sum of amounts in last 24 hours
        - rolling_7d_count: count of transactions in last 7 days
        - rolling_30m_count: count of transactions in last 30 minutes
        - rolling_30m_total: sum of amounts in last 30 minutes
        - rolling_90d_average: average transaction amount over last 90 days
        - cross_border_count: count of cross-border transactions (origin != destination)
        - high_risk_country_flag: whether any recent transaction involved high-risk countries
        - prior_alert_count: count of alerts for this customer
        """
        # Time windows
        window_24h = as_of - timedelta(hours=24)
        window_7d = as_of - timedelta(days=7)
        window_30m = as_of - timedelta(minutes=30)
        window_90d = as_of - timedelta(days=90)
        
        # Rolling 24h total
        rolling_24h_result = (
            self.db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.account_id == account_id,
                Transaction.transaction_timestamp >= window_24h,
                Transaction.transaction_timestamp < as_of
            )
            .scalar()
        )
        rolling_24h_total = Decimal(str(rolling_24h_result)) if rolling_24h_result else Decimal(0)
        
        # Rolling 7d count
        rolling_7d_count = (
            self.db.query(func.count(Transaction.id))
            .filter(
                Transaction.account_id == account_id,
                Transaction.transaction_timestamp >= window_7d,
                Transaction.transaction_timestamp < as_of
            )
            .scalar() or 0
        )
        
        # Rolling 30m count and total
        rolling_30m_count = (
            self.db.query(func.count(Transaction.id))
            .filter(
                Transaction.account_id == account_id,
                Transaction.transaction_timestamp >= window_30m,
                Transaction.transaction_timestamp < as_of
            )
            .scalar() or 0
        )
        
        rolling_30m_result = (
            self.db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(
                Transaction.account_id == account_id,
                Transaction.transaction_timestamp >= window_30m,
                Transaction.transaction_timestamp < as_of
            )
            .scalar()
        )
        rolling_30m_total = Decimal(str(rolling_30m_result)) if rolling_30m_result else Decimal(0)
        
        # Rolling 90d average
        rolling_90d_result = (
            self.db.query(func.avg(Transaction.amount))
            .filter(
                Transaction.account_id == account_id,
                Transaction.transaction_timestamp >= window_90d,
                Transaction.transaction_timestamp < as_of
            )
            .scalar()
        )
        rolling_90d_average = Decimal(str(rolling_90d_result)) if rolling_90d_result else Decimal(0)
        
        # Cross-border count (origin != destination in last 90 days)
        cross_border_count = (
            self.db.query(func.count(Transaction.id))
            .filter(
                Transaction.account_id == account_id,
                Transaction.transaction_timestamp >= window_90d,
                Transaction.transaction_timestamp < as_of,
                Transaction.origin_country != Transaction.destination_country
            )
            .scalar() or 0
        )
        
        # High-risk country flag: check if any recent transaction involved high-risk countries
        high_risk_country_flag = (
            self.db.query(Transaction.id)
            .join(
                CountryRisk,
                or_(
                    Transaction.origin_country == CountryRisk.country_code,
                    Transaction.destination_country == CountryRisk.country_code
                )
            )
            .filter(
                Transaction.account_id == account_id,
                Transaction.transaction_timestamp >= window_90d,
                Transaction.transaction_timestamp < as_of,
                CountryRisk.is_high_risk == True
            )
            .first() is not None
        )
        
        # Prior alert count for this customer
        prior_alert_count = (
            self.db.query(func.count(Alert.id))
            .join(Transaction, Alert.transaction_id == Transaction.id)
            .filter(Transaction.account_id == account_id)
            .scalar() or 0
        )
        
        return HistoricalMetrics(
            rolling_24h_total=rolling_24h_total,
            rolling_7d_count=rolling_7d_count,
            rolling_30m_count=rolling_30m_count,
            rolling_30m_total=rolling_30m_total,
            rolling_90d_average=rolling_90d_average,
            cross_border_count=cross_border_count,
            high_risk_country_flag=high_risk_country_flag,
            prior_alert_count=prior_alert_count
        )
