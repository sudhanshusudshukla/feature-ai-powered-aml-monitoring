"""Case management service for business logic orchestration."""
from datetime import datetime

from sqlalchemy.orm import Session

from app.alert.models import Alert
from app.audit.service import AuditService
from app.case_management.models import AMLCase
from app.case_management.repository import CaseRepository
from app.case_management.schemas import (
    AlertSummary,
    CaseDetailResponse,
    DecisionSummary,
    InformationRequestSummary,
    NoteSummary,
)
from app.case_management.state_machine import CaseStateMachine
from app.common.correlation import get_correlation_id
from app.common.enums import AlertPriority, CaseState
from app.common.errors import (
    AuthorizationError,
    DomainValidationError,
    NotFoundError,
)
from app.security.models import User


class CaseManagementService:
    """
    Service for case lifecycle management.
    
    Orchestrates case creation from alerts, assignment, state transitions,
    decision recording with separation-of-duties enforcement, and audit logging.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = CaseRepository(db)
        self.audit_service = AuditService(db)
        self.state_machine = CaseStateMachine()
    
    def create_case(
        self,
        title: str,
        alert_ids: list[int],
        actor_user: User
    ) -> CaseDetailResponse:
        """
        Create a new case from one or more alerts.
        
        Args:
            title: Case title
            alert_ids: List of alert IDs to link
            actor_user: User creating the case
        
        Returns:
            Case detail response
        
        Raises:
            DomainValidationError: If alerts are invalid or ineligible
            NotFoundError: If alerts don't exist
        """
        # Validate alerts exist and are eligible
        alerts = self.db.query(Alert).filter(Alert.id.in_(alert_ids)).all()
        
        if len(alerts) != len(alert_ids):
            found_ids = {a.id for a in alerts}
            missing_ids = set(alert_ids) - found_ids
            raise NotFoundError(f"Alerts not found: {missing_ids}")
        
        # Check if any alerts are already linked to cases
        for alert in alerts:
            if self.repository.is_alert_already_linked(alert.id):
                raise DomainValidationError(
                    f"Alert {alert.alert_number} is already linked to a case",
                    detail="ALERT_ALREADY_LINKED"
                )
        
        # Determine case priority from alerts (use highest alert priority)
        priority_order = {
            AlertPriority.LOW: 1,
            AlertPriority.MEDIUM: 2,
            AlertPriority.HIGH: 3,
            AlertPriority.CRITICAL: 4,
        }
        
        max_priority = AlertPriority.LOW
        for alert in alerts:
            alert_priority = AlertPriority(alert.priority)
            if priority_order[alert_priority] > priority_order[max_priority]:
                max_priority = alert_priority
        
        # Get customer from first alert's transaction
        first_alert = alerts[0]
        transaction = first_alert.transaction
        customer_id = transaction.account.customer_id
        
        # Generate case number
        case_number = self.repository.generate_case_number()
        
        # Create case entity
        now = datetime.utcnow()
        case = AMLCase(
            case_number=case_number,
            title=title,
            customer_id=customer_id,
            state=CaseState.OPEN.value,
            priority=max_priority.value,
            created_by_user_id=actor_user.id,
            assigned_to_user_id=None,
            created_at=now,
            updated_at=now,
            version=1
        )
        
        case = self.repository.create(case)
        
        # Link alerts to case
        self.repository.link_alerts(
            case_id=case.id,
            alert_ids=alert_ids,
            linked_by_user_id=actor_user.id,
            linked_at=now
        )
        
        # Record audit event
        correlation_id = get_correlation_id()
        self.audit_service.record_event(
            action="CASE_CREATED",
            entity_type="case",
            entity_id=case.id,
            correlation_id=correlation_id,
            details={
                "case_number": case_number,
                "alert_ids": alert_ids,
                "customer_id": customer_id,
                "priority": max_priority.value,
            },
            actor_user_id=actor_user.id,
            actor_username=actor_user.username,
            actor_role=actor_user.role
        )
        
        # Commit transaction
        self.db.commit()
        
        # Return case detail
        return self.get_case_detail(case.id, actor_user)
    
    def get_case_detail(
        self,
        case_id: int,
        actor_user: User
    ) -> CaseDetailResponse:
        """
        Get complete case detail with permitted actions.
        
        Args:
            case_id: Case ID
            actor_user: User requesting case detail
        
        Returns:
            Case detail response
        
        Raises:
            NotFoundError: If case doesn't exist
        """
        case = self.repository.get_by_id(case_id, eager_load=True)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")
        
        # Get linked alerts
        linked_alerts = self.repository.get_linked_alerts(case_id)
        
        # Get information requests
        info_requests = self.repository.get_information_requests(case_id)
        
        # Compute permitted actions
        is_creator = (actor_user.id == case.created_by_user_id)
        has_open_info_requests = any(
            req.status == "OPEN" for req in info_requests
        )
        
        permitted_actions = self.state_machine.permitted_actions(
            current_state=case.state,
            actor_role=actor_user.role,
            is_creator=is_creator,
            has_open_info_requests=has_open_info_requests
        )
        
        # Build response
        return CaseDetailResponse(
            id=case.id,
            case_number=case.case_number,
            title=case.title,
            customer_id=case.customer_id,
            state=case.state,
            priority=case.priority,
            created_by_user_id=case.created_by_user_id,
            assigned_to_user_id=case.assigned_to_user_id,
            closure_reason=case.closure_reason,
            created_at=case.created_at,
            updated_at=case.updated_at,
            version=case.version,
            linked_alerts=[
                AlertSummary(
                    id=alert.id,
                    alert_number=alert.alert_number,
                    transaction_id=alert.transaction_id,
                    risk_score=alert.risk_score,
                    priority=alert.priority,
                    status=alert.status
                )
                for alert in linked_alerts
            ],
            notes=[
                NoteSummary(
                    id=note.id,
                    note_text=note.note_text,
                    created_by_user_id=note.created_by_user_id,
                    created_at=note.created_at
                )
                for note in case.notes
            ],
            decisions=[
                DecisionSummary(
                    id=decision.id,
                    decision=decision.decision,
                    reason=decision.reason,
                    comments=decision.comments,
                    decided_by_user_id=decision.decided_by_user_id,
                    decided_at=decision.decided_at
                )
                for decision in case.decisions
            ],
            information_requests=[
                InformationRequestSummary(
                    id=req.id,
                    requested_what=req.requested_what,
                    reason=req.reason,
                    due_date=req.due_date,
                    status=req.status,
                    requested_by_user_id=req.requested_by_user_id,
                    created_at=req.created_at
                )
                for req in info_requests
            ],
            permitted_actions=permitted_actions
        )
    
    def assign_case(
        self,
        case_id: int,
        assigned_to_user_id: int,
        expected_version: int,
        actor_user: User
    ) -> CaseDetailResponse:
        """
        Assign or reassign a case to a user.
        
        Args:
            case_id: Case ID
            assigned_to_user_id: User ID to assign to
            expected_version: Expected version for optimistic locking
            actor_user: User performing assignment
        
        Returns:
            Updated case detail
        
        Raises:
            NotFoundError: If case or user not found
            OptimisticLockConflictError: If version mismatch
        """
        # Verify assignee exists
        assignee = self.db.query(User).filter(User.id == assigned_to_user_id).first()
        if not assignee:
            raise NotFoundError(f"User {assigned_to_user_id} not found")
        
        # Get previous assignment for audit
        case = self.repository.get_by_id(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")
        
        previous_assignee_id = case.assigned_to_user_id
        
        # Update case
        now = datetime.utcnow()
        case = self.repository.update_with_version(
            case_id=case_id,
            expected_version=expected_version,
            updates={
                "assigned_to_user_id": assigned_to_user_id,
                "updated_at": now
            }
        )
        
        # Record audit event
        correlation_id = get_correlation_id()
        self.audit_service.record_event(
            action="CASE_ASSIGNED",
            entity_type="case",
            entity_id=case_id,
            correlation_id=correlation_id,
            details={
                "case_number": case.case_number,
                "previous_assignee_id": previous_assignee_id,
                "new_assignee_id": assigned_to_user_id,
            },
            actor_user_id=actor_user.id,
            actor_username=actor_user.username,
            actor_role=actor_user.role
        )
        
        # Commit transaction
        self.db.commit()
        
        return self.get_case_detail(case_id, actor_user)
    
    def record_decision(
        self,
        case_id: int,
        decision: str,
        expected_version: int,
        actor_user: User,
        reason: str | None = None,
        comments: str | None = None
    ) -> CaseDetailResponse:
        """
        Record a case decision with separation-of-duties enforcement.
        
        Args:
            case_id: Case ID
            decision: Decision type (APPROVE, REJECT, ESCALATE, etc.)
            expected_version: Expected version for optimistic locking
            actor_user: User making decision
            reason: Reason for decision
            comments: Additional comments
        
        Returns:
            Updated case detail
        
        Raises:
            NotFoundError: If case not found
            AuthorizationError: If creator tries to decide own case
            InvalidStateTransitionError: If state transition invalid
            OptimisticLockConflictError: If version mismatch
        """
        # Get case
        case = self.repository.get_by_id(case_id)
        if not case:
            raise NotFoundError(f"Case {case_id} not found")
        
        # Enforce separation of duties: creator cannot decide
        if actor_user.id == case.created_by_user_id:
            raise AuthorizationError(
                "Case creator cannot make decision on their own case",
                detail="CREATOR_DECIDER_CONFLICT"
            )
        
        # Save previous state before transition
        previous_state = case.state
        
        # Map decision to action
        action_map = {
            "APPROVE": "APPROVE",
            "REJECT": "REJECT",
            "ESCALATE": "ESCALATE",
            "CLOSE_FALSE_POSITIVE": "CLOSE_FALSE_POSITIVE",
            "REQUEST_INFO": "REQUEST_INFO",
        }
        
        if decision not in action_map:
            raise DomainValidationError(f"Invalid decision: {decision}")
        
        action = action_map[decision]
        
        # Validate state transition
        # The state machine validates the transition is legal for the current state
        next_state = self.state_machine.validate_transition(case.state, action)
        
        # Add decision record
        self.repository.add_decision(
            case_id=case_id,
            decision=decision,
            decided_by_user_id=actor_user.id,
            reason=reason,
            comments=comments
        )
        
        # Update case state
        now = datetime.utcnow()
        case = self.repository.update_with_version(
            case_id=case_id,
            expected_version=expected_version,
            updates={
                "state": next_state,
                "updated_at": now
            }
        )
        
        # Record audit event
        correlation_id = get_correlation_id()
        self.audit_service.record_event(
            action="CASE_DECISION",
            entity_type="case",
            entity_id=case_id,
            correlation_id=correlation_id,
            details={
                "case_number": case.case_number,
                "decision": decision,
                "previous_state": previous_state,
                "new_state": next_state,
                "reason": reason,
            },
            actor_user_id=actor_user.id,
            actor_username=actor_user.username,
            actor_role=actor_user.role
        )
        
        # Commit transaction
        self.db.commit()
        
        return self.get_case_detail(case_id, actor_user)
