/**
 * Decision actions permission logic
 * Matches backend permitted actions matrix from TASK-8 and TASK-9
 */

export type CaseState =
  | 'OPEN'
  | 'UNDER_INVESTIGATION'
  | 'INFORMATION_REQUESTED'
  | 'PENDING_DECISION'
  | 'ESCALATED'
  | 'APPROVED'
  | 'REJECTED'
  | 'CLOSED';

export type UserRole =
  | 'AML_ANALYST'
  | 'AML_OFFICER'
  | 'AML_MANAGER'
  | 'ADMINISTRATOR'
  | 'AUDITOR';

export type DecisionAction =
  | 'APPROVE'
  | 'REJECT'
  | 'ESCALATE'
  | 'CLOSE_FALSE_POSITIVE';

export interface DecisionPermission {
  action: DecisionAction;
  permitted: boolean;
  reason: string;
}

/**
 * Compute permitted decision actions for the current user and case context
 * This is a client-side helper for UI rendering — backend is authoritative
 */
export function computeDecisionPermissions(params: {
  state: CaseState;
  role: UserRole;
  isCreator: boolean;
  hasOpenRequest: boolean;
}): DecisionPermission[] {
  const { state, role, isCreator, hasOpenRequest } = params;

  const permissions: DecisionPermission[] = [];

  // Terminal states have no actions
  if (state === 'APPROVED' || state === 'REJECTED' || state === 'CLOSED') {
    return permissions;
  }

  // Approve action
  if (state === 'PENDING_DECISION' || state === 'ESCALATED') {
    if (
      (role === 'AML_OFFICER' || role === 'AML_MANAGER' || role === 'ADMINISTRATOR') &&
      !isCreator &&
      !hasOpenRequest
    ) {
      permissions.push({
        action: 'APPROVE',
        permitted: true,
        reason: 'Officer, not the creator, no open request',
      });
    } else if (isCreator) {
      permissions.push({
        action: 'APPROVE',
        permitted: false,
        reason: 'Creator cannot approve own case',
      });
    } else if (hasOpenRequest) {
      permissions.push({
        action: 'APPROVE',
        permitted: false,
        reason: 'Open information request blocks decisions',
      });
    } else {
      permissions.push({
        action: 'APPROVE',
        permitted: false,
        reason: 'Insufficient role',
      });
    }
  }

  // Reject action
  if (state === 'PENDING_DECISION' || state === 'ESCALATED') {
    if (
      (role === 'AML_OFFICER' || role === 'AML_MANAGER' || role === 'ADMINISTRATOR') &&
      !isCreator &&
      !hasOpenRequest
    ) {
      permissions.push({
        action: 'REJECT',
        permitted: true,
        reason: 'Officer, not the creator, no open request',
      });
    } else if (isCreator) {
      permissions.push({
        action: 'REJECT',
        permitted: false,
        reason: 'Creator cannot reject own case',
      });
    } else if (hasOpenRequest) {
      permissions.push({
        action: 'REJECT',
        permitted: false,
        reason: 'Open information request blocks decisions',
      });
    } else {
      permissions.push({
        action: 'REJECT',
        permitted: false,
        reason: 'Insufficient role',
      });
    }
  }

  // Escalate action
  if (state === 'UNDER_INVESTIGATION' || state === 'PENDING_DECISION') {
    if (
      role === 'AML_OFFICER' ||
      role === 'AML_MANAGER' ||
      role === 'ADMINISTRATOR'
    ) {
      permissions.push({
        action: 'ESCALATE',
        permitted: true,
        reason: 'Officer or manager can escalate',
      });
    } else {
      permissions.push({
        action: 'ESCALATE',
        permitted: false,
        reason: 'Insufficient role',
      });
    }
  }

  // Close as false positive
  if (state === 'UNDER_INVESTIGATION') {
    if (
      role === 'AML_OFFICER' ||
      role === 'AML_MANAGER' ||
      role === 'ADMINISTRATOR'
    ) {
      permissions.push({
        action: 'CLOSE_FALSE_POSITIVE',
        permitted: true,
        reason: 'Officer or manager can close',
      });
    } else {
      permissions.push({
        action: 'CLOSE_FALSE_POSITIVE',
        permitted: false,
        reason: 'Insufficient role',
      });
    }
  }

  return permissions;
}

/**
 * Check if any decision action is permitted
 */
export function hasAnyDecisionPermission(permissions: DecisionPermission[]): boolean {
  return permissions.some((p) => p.permitted);
}

/**
 * Get permitted actions from the list
 */
export function getPermittedActions(permissions: DecisionPermission[]): DecisionAction[] {
  return permissions.filter((p) => p.permitted).map((p) => p.action);
}
