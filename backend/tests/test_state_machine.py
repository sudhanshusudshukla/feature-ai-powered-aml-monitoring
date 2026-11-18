"""Unit tests for case state machine."""
import pytest

from app.case_management.state_machine import CaseStateMachine
from app.common.enums import CaseState, UserRole
from app.common.errors import InvalidStateTransitionError


def test_validate_transition_open_to_under_investigation():
    """Test transition from OPEN to UNDER_INVESTIGATION."""
    sm = CaseStateMachine()
    next_state = sm.validate_transition(CaseState.OPEN.value, "START_INVESTIGATION")
    assert next_state == CaseState.UNDER_INVESTIGATION.value


def test_validate_transition_under_investigation_to_information_requested():
    """Test transition from UNDER_INVESTIGATION to INFORMATION_REQUESTED."""
    sm = CaseStateMachine()
    next_state = sm.validate_transition(
        CaseState.UNDER_INVESTIGATION.value, "REQUEST_INFO"
    )
    assert next_state == CaseState.INFORMATION_REQUESTED.value


def test_validate_transition_information_requested_to_under_investigation():
    """Test transition from INFORMATION_REQUESTED back to UNDER_INVESTIGATION."""
    sm = CaseStateMachine()
    next_state = sm.validate_transition(
        CaseState.INFORMATION_REQUESTED.value, "RECORD_RESPONSE"
    )
    assert next_state == CaseState.UNDER_INVESTIGATION.value


def test_validate_transition_under_investigation_to_pending_decision():
    """Test transition from UNDER_INVESTIGATION to PENDING_DECISION."""
    sm = CaseStateMachine()
    next_state = sm.validate_transition(CaseState.UNDER_INVESTIGATION.value, "SUBMIT")
    assert next_state == CaseState.PENDING_DECISION.value


def test_validate_transition_pending_decision_to_approved():
    """Test transition from PENDING_DECISION to APPROVED."""
    sm = CaseStateMachine()
    next_state = sm.validate_transition(CaseState.PENDING_DECISION.value, "APPROVE")
    assert next_state == CaseState.APPROVED.value


def test_validate_transition_pending_decision_to_rejected():
    """Test transition from PENDING_DECISION to REJECTED."""
    sm = CaseStateMachine()
    next_state = sm.validate_transition(CaseState.PENDING_DECISION.value, "REJECT")
    assert next_state == CaseState.REJECTED.value


def test_validate_transition_pending_decision_to_escalated():
    """Test transition from PENDING_DECISION to ESCALATED."""
    sm = CaseStateMachine()
    next_state = sm.validate_transition(CaseState.PENDING_DECISION.value, "ESCALATE")
    assert next_state == CaseState.ESCALATED.value


def test_validate_transition_escalated_to_approved():
    """Test transition from ESCALATED to APPROVED."""
    sm = CaseStateMachine()
    next_state = sm.validate_transition(CaseState.ESCALATED.value, "APPROVE")
    assert next_state == CaseState.APPROVED.value


def test_validate_transition_escalated_to_rejected():
    """Test transition from ESCALATED to REJECTED."""
    sm = CaseStateMachine()
    next_state = sm.validate_transition(CaseState.ESCALATED.value, "REJECT")
    assert next_state == CaseState.REJECTED.value


def test_validate_transition_under_investigation_to_closed():
    """Test transition from UNDER_INVESTIGATION to CLOSED via CLOSE_FALSE_POSITIVE."""
    sm = CaseStateMachine()
    next_state = sm.validate_transition(
        CaseState.UNDER_INVESTIGATION.value, "CLOSE_FALSE_POSITIVE"
    )
    assert next_state == CaseState.CLOSED.value


def test_validate_transition_invalid_action_raises_error():
    """Test invalid action raises InvalidStateTransitionError."""
    sm = CaseStateMachine()
    
    with pytest.raises(InvalidStateTransitionError, match="not allowed"):
        sm.validate_transition(CaseState.OPEN.value, "APPROVE")


def test_validate_transition_from_terminal_state_raises_error():
    """Test transition from terminal state raises error."""
    sm = CaseStateMachine()
    
    with pytest.raises(InvalidStateTransitionError, match="terminal state"):
        sm.validate_transition(CaseState.APPROVED.value, "REJECT")


def test_validate_transition_invalid_state_raises_error():
    """Test invalid state value raises error."""
    sm = CaseStateMachine()
    
    with pytest.raises(InvalidStateTransitionError, match="Invalid current state"):
        sm.validate_transition("INVALID_STATE", "APPROVE")


def test_permitted_actions_analyst_open_state():
    """Test permitted actions for analyst in OPEN state."""
    sm = CaseStateMachine()
    actions = sm.permitted_actions(
        current_state=CaseState.OPEN.value,
        actor_role=UserRole.AML_ANALYST.value,
        is_creator=False
    )
    
    assert "START_INVESTIGATION" in actions


def test_permitted_actions_officer_pending_decision():
    """Test permitted actions for officer in PENDING_DECISION state."""
    sm = CaseStateMachine()
    actions = sm.permitted_actions(
        current_state=CaseState.PENDING_DECISION.value,
        actor_role=UserRole.AML_OFFICER.value,
        is_creator=False
    )
    
    assert "APPROVE" in actions
    assert "REJECT" in actions
    assert "ESCALATE" in actions
    assert "REQUEST_INFO" in actions


def test_permitted_actions_officer_creator_cannot_approve_reject():
    """Test officer who created case cannot approve or reject."""
    sm = CaseStateMachine()
    actions = sm.permitted_actions(
        current_state=CaseState.PENDING_DECISION.value,
        actor_role=UserRole.AML_OFFICER.value,
        is_creator=True  # Officer is the creator
    )
    
    assert "APPROVE" not in actions
    assert "REJECT" not in actions
    # But can still escalate or request info
    assert "ESCALATE" in actions
    assert "REQUEST_INFO" in actions


def test_permitted_actions_manager_has_broad_access():
    """Test manager has broad action permissions."""
    sm = CaseStateMachine()
    actions = sm.permitted_actions(
        current_state=CaseState.PENDING_DECISION.value,
        actor_role=UserRole.AML_MANAGER.value,
        is_creator=False
    )
    
    assert "APPROVE" in actions
    assert "REJECT" in actions
    assert "ESCALATE" in actions
    assert "REQUEST_INFO" in actions


def test_permitted_actions_administrator_has_all_actions():
    """Test administrator has all available actions."""
    sm = CaseStateMachine()
    actions = sm.permitted_actions(
        current_state=CaseState.UNDER_INVESTIGATION.value,
        actor_role=UserRole.ADMINISTRATOR.value,
        is_creator=False
    )
    
    # Administrator gets all available actions for the state
    assert "REQUEST_INFO" in actions
    assert "SUBMIT" in actions
    assert "ESCALATE" in actions
    assert "CLOSE_FALSE_POSITIVE" in actions


def test_permitted_actions_terminal_state_returns_empty():
    """Test terminal states have no permitted actions."""
    sm = CaseStateMachine()
    actions = sm.permitted_actions(
        current_state=CaseState.APPROVED.value,
        actor_role=UserRole.AML_OFFICER.value,
        is_creator=False
    )
    
    assert len(actions) == 0


def test_permitted_actions_invalid_role_returns_empty():
    """Test invalid role returns empty action list."""
    sm = CaseStateMachine()
    actions = sm.permitted_actions(
        current_state=CaseState.PENDING_DECISION.value,
        actor_role="INVALID_ROLE",
        is_creator=False
    )
    
    assert len(actions) == 0
