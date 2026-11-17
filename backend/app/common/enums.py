"""Shared enumerations used across the AML platform."""
from enum import Enum


class UserRole(str, Enum):
    """User role definitions."""
    AML_ANALYST = "AML_ANALYST"
    AML_OFFICER = "AML_OFFICER"
    AML_MANAGER = "AML_MANAGER"
    ADMINISTRATOR = "ADMINISTRATOR"
    AUDITOR = "AUDITOR"


class TransactionType(str, Enum):
    """Transaction type classifications."""
    TRANSFER = "TRANSFER"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    PAYMENT = "PAYMENT"


class RuleOutcome(str, Enum):
    """Rule evaluation outcome."""
    PASS = "PASS"
    MATCH = "MATCH"


class RuleSeverity(str, Enum):
    """Rule severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertPriority(str, Enum):
    """Alert priority bands."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """Alert lifecycle status."""
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CLOSED = "CLOSED"


class CaseState(str, Enum):
    """Case lifecycle states."""
    OPEN = "OPEN"
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION"
    INFORMATION_REQUESTED = "INFORMATION_REQUESTED"
    PENDING_DECISION = "PENDING_DECISION"
    ESCALATED = "ESCALATED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class InformationRequestStatus(str, Enum):
    """Information request status."""
    OPEN = "OPEN"
    RESPONDED = "RESPONDED"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class CaseDecision(str, Enum):
    """Case decision types."""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ESCALATE = "ESCALATE"
    CLOSE_FALSE_POSITIVE = "CLOSE_FALSE_POSITIVE"
    REQUEST_INFO = "REQUEST_INFO"


class RiskLevel(str, Enum):
    """Customer risk levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class AccountStatus(str, Enum):
    """Account status."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    CLOSED = "CLOSED"
    SUSPENDED = "SUSPENDED"


class CountryRiskRating(str, Enum):
    """Country risk rating."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
