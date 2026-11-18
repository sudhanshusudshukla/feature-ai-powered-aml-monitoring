"""Case state machine for lifecycle transitions and permitted actions."""

from app.common.enums import CaseState, UserRole
from app.common.errors import InvalidStateTransitionError

# State transition table from LLD Section 7.3
STATE_TRANSITIONS = {
    CaseState.OPEN: {
        "START_INVESTIGATION": CaseState.UNDER_INVESTIGATION,
        "REQUEST_INFO": CaseState.INFORMATION_REQUESTED,
    },
    CaseState.UNDER_INVESTIGATION: {
        "REQUEST_INFO": CaseState.INFORMATION_REQUESTED,
        "SUBMIT": CaseState.PENDING_DECISION,
        "ESCALATE": CaseState.ESCALATED,
        "CLOSE_FALSE_POSITIVE": CaseState.CLOSED,
    },
    CaseState.INFORMATION_REQUESTED: {
        "RECORD_RESPONSE": CaseState.UNDER_INVESTIGATION,
        "REQUEST_INFO": CaseState.INFORMATION_REQUESTED,
    },
    CaseState.PENDING_DECISION: {
        "REQUEST_INFO": CaseState.INFORMATION_REQUESTED,
        "APPROVE": CaseState.APPROVED,
        "REJECT": CaseState.REJECTED,
        "ESCALATE": CaseState.ESCALATED,
    },
    CaseState.ESCALATED: {
        "APPROVE": CaseState.APPROVED,
        "REJECT": CaseState.REJECTED,
    },
}

# Terminal states - no further transitions allowed
TERMINAL_STATES = {CaseState.APPROVED, CaseState.REJECTED, CaseState.CLOSED}


class CaseStateMachine:
    """
    Case state machine implementing lifecycle transitions and action permissions.
    
    Enforces state transition rules from LLD Section 7.3 and computes permitted
    actions based on current state, actor role, and business rules.
    """
    
    @staticmethod
    def validate_transition(current_state: str, action: str) -> str:
        """
        Validate and return next state for a given action.
        
        Args:
            current_state: Current case state
            action: Action to perform
        
        Returns:
            Next state if transition is valid
        
        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        try:
            current_enum = CaseState(current_state)
        except ValueError:
            raise InvalidStateTransitionError(f"Invalid current state: {current_state}")
        
        # Check if state is terminal
        if current_enum in TERMINAL_STATES:
            raise InvalidStateTransitionError(
                f"Case is in terminal state {current_state}, no further transitions allowed"
            )
        
        # Check if transition exists
        if current_enum not in STATE_TRANSITIONS:
            raise InvalidStateTransitionError(
                f"No transitions defined for state {current_state}"
            )
        
        transitions = STATE_TRANSITIONS[current_enum]
        if action not in transitions:
            raise InvalidStateTransitionError(
                f"Action {action} not allowed from state {current_state}"
            )
        
        next_state = transitions[action]
        return next_state.value
    
    @staticmethod
    def transition(current_state: str, action: str) -> str:
        """
        Execute state transition and return next state.
        
        This is an alias for validate_transition for compatibility.
        
        Args:
            current_state: Current case state
            action: Action to perform
        
        Returns:
            Next state if transition is valid
        
        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        return CaseStateMachine.validate_transition(current_state, action)
    
    @staticmethod
    def permitted_actions(
        current_state: str,
        actor_role: str,
        is_creator: bool,
        has_open_info_requests: bool = False
    ) -> list[str]:
        """
        Compute permitted actions for current state and actor context.
        
        Args:
            current_state: Current case state
            actor_role: Actor's role (UserRole enum value)
            is_creator: Whether actor is the case creator
            has_open_info_requests: Whether case has open information requests
        
        Returns:
            List of permitted action strings
        """
        try:
            current_enum = CaseState(current_state)
        except ValueError:
            return []
        
        # Terminal states have no actions
        if current_enum in TERMINAL_STATES:
            return []
        
        # Get available transitions for current state
        if current_enum not in STATE_TRANSITIONS:
            return []
        
        available_actions = set(STATE_TRANSITIONS[current_enum].keys())
        permitted: set[str] = set()
        
        # Apply role-based and business rule filters
        try:
            role_enum = UserRole(actor_role)
        except ValueError:
            return []
        
        # Analyst actions
        if role_enum == UserRole.AML_ANALYST:
            permitted.update(available_actions & {
                "START_INVESTIGATION",
                "REQUEST_INFO",
                "RECORD_RESPONSE",
                "SUBMIT",
            })
        
        # Officer actions (with creator-decider separation)
        elif role_enum == UserRole.AML_OFFICER:
            officer_actions = available_actions & {
                "REQUEST_INFO",
                "APPROVE",
                "REJECT",
                "ESCALATE",
                "CLOSE_FALSE_POSITIVE",
            }
            
            # Creator-decider separation: creator cannot decide their own case
            if is_creator:
                officer_actions.discard("APPROVE")
                officer_actions.discard("REJECT")
            
            permitted.update(officer_actions)
        
        # Manager actions
        elif role_enum == UserRole.AML_MANAGER:
            permitted.update(available_actions & {
                "REQUEST_INFO",
                "RECORD_RESPONSE",
                "ESCALATE",
                "APPROVE",
                "REJECT",
                "CLOSE_FALSE_POSITIVE",
            })
        
        # Administrator can perform all available actions
        elif role_enum == UserRole.ADMINISTRATOR:
            permitted.update(available_actions)
        
        return sorted(list(permitted))
