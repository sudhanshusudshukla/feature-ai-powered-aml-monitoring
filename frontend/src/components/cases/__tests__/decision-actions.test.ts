/**
 * Tests for decision actions permission logic
 * Verifies permitted actions matrix matches backend logic
 */

import { describe, it, expect } from 'vitest';
import {
  computeDecisionPermissions,
  hasAnyDecisionPermission,
  getPermittedActions,
} from '../../../lib/decision-actions';

describe('computeDecisionPermissions', () => {
  describe('PENDING_DECISION state', () => {
    it('permits APPROVE and REJECT for officer who is not creator with no open request', () => {
      const permissions = computeDecisionPermissions({
        state: 'PENDING_DECISION',
        role: 'AML_OFFICER',
        isCreator: false,
        hasOpenRequest: false,
      });

      const approve = permissions.find((p) => p.action === 'APPROVE');
      const reject = permissions.find((p) => p.action === 'REJECT');

      expect(approve?.permitted).toBe(true);
      expect(reject?.permitted).toBe(true);
    });

    it('blocks APPROVE and REJECT for creator (separation of duties)', () => {
      const permissions = computeDecisionPermissions({
        state: 'PENDING_DECISION',
        role: 'AML_OFFICER',
        isCreator: true,
        hasOpenRequest: false,
      });

      const approve = permissions.find((p) => p.action === 'APPROVE');
      const reject = permissions.find((p) => p.action === 'REJECT');

      expect(approve?.permitted).toBe(false);
      expect(approve?.reason).toContain('Creator cannot');
      expect(reject?.permitted).toBe(false);
      expect(reject?.reason).toContain('Creator cannot');
    });

    it('blocks APPROVE and REJECT when open information request exists', () => {
      const permissions = computeDecisionPermissions({
        state: 'PENDING_DECISION',
        role: 'AML_OFFICER',
        isCreator: false,
        hasOpenRequest: true,
      });

      const approve = permissions.find((p) => p.action === 'APPROVE');
      const reject = permissions.find((p) => p.action === 'REJECT');

      expect(approve?.permitted).toBe(false);
      expect(approve?.reason).toContain('Open information request');
      expect(reject?.permitted).toBe(false);
      expect(reject?.reason).toContain('Open information request');
    });

    it('permits ESCALATE for officer regardless of creator status', () => {
      const permissions = computeDecisionPermissions({
        state: 'PENDING_DECISION',
        role: 'AML_OFFICER',
        isCreator: true,
        hasOpenRequest: false,
      });

      const escalate = permissions.find((p) => p.action === 'ESCALATE');
      expect(escalate?.permitted).toBe(true);
    });

    it('blocks decisions for analyst role', () => {
      const permissions = computeDecisionPermissions({
        state: 'PENDING_DECISION',
        role: 'AML_ANALYST',
        isCreator: false,
        hasOpenRequest: false,
      });

      const approve = permissions.find((p) => p.action === 'APPROVE');
      const reject = permissions.find((p) => p.action === 'REJECT');

      expect(approve?.permitted).toBe(false);
      expect(reject?.permitted).toBe(false);
    });
  });

  describe('ESCALATED state', () => {
    it('permits APPROVE and REJECT for officer', () => {
      const permissions = computeDecisionPermissions({
        state: 'ESCALATED',
        role: 'AML_OFFICER',
        isCreator: false,
        hasOpenRequest: false,
      });

      const approve = permissions.find((p) => p.action === 'APPROVE');
      const reject = permissions.find((p) => p.action === 'REJECT');

      expect(approve?.permitted).toBe(true);
      expect(reject?.permitted).toBe(true);
    });

    it('permits APPROVE and REJECT for manager', () => {
      const permissions = computeDecisionPermissions({
        state: 'ESCALATED',
        role: 'AML_MANAGER',
        isCreator: false,
        hasOpenRequest: false,
      });

      const approve = permissions.find((p) => p.action === 'APPROVE');
      const reject = permissions.find((p) => p.action === 'REJECT');

      expect(approve?.permitted).toBe(true);
      expect(reject?.permitted).toBe(true);
    });
  });

  describe('UNDER_INVESTIGATION state', () => {
    it('permits ESCALATE for officer', () => {
      const permissions = computeDecisionPermissions({
        state: 'UNDER_INVESTIGATION',
        role: 'AML_OFFICER',
        isCreator: false,
        hasOpenRequest: false,
      });

      const escalate = permissions.find((p) => p.action === 'ESCALATE');
      expect(escalate?.permitted).toBe(true);
    });

    it('permits CLOSE_FALSE_POSITIVE for officer', () => {
      const permissions = computeDecisionPermissions({
        state: 'UNDER_INVESTIGATION',
        role: 'AML_OFFICER',
        isCreator: false,
        hasOpenRequest: false,
      });

      const close = permissions.find((p) => p.action === 'CLOSE_FALSE_POSITIVE');
      expect(close?.permitted).toBe(true);
    });

    it('blocks CLOSE_FALSE_POSITIVE for analyst', () => {
      const permissions = computeDecisionPermissions({
        state: 'UNDER_INVESTIGATION',
        role: 'AML_ANALYST',
        isCreator: false,
        hasOpenRequest: false,
      });

      const close = permissions.find((p) => p.action === 'CLOSE_FALSE_POSITIVE');
      expect(close?.permitted).toBe(false);
    });
  });

  describe('Terminal states', () => {
    it('returns no actions for APPROVED state', () => {
      const permissions = computeDecisionPermissions({
        state: 'APPROVED',
        role: 'AML_OFFICER',
        isCreator: false,
        hasOpenRequest: false,
      });

      expect(permissions).toHaveLength(0);
    });

    it('returns no actions for REJECTED state', () => {
      const permissions = computeDecisionPermissions({
        state: 'REJECTED',
        role: 'AML_OFFICER',
        isCreator: false,
        hasOpenRequest: false,
      });

      expect(permissions).toHaveLength(0);
    });

    it('returns no actions for CLOSED state', () => {
      const permissions = computeDecisionPermissions({
        state: 'CLOSED',
        role: 'AML_OFFICER',
        isCreator: false,
        hasOpenRequest: false,
      });

      expect(permissions).toHaveLength(0);
    });
  });

  describe('Administrator role', () => {
    it('permits all decision actions when not creator', () => {
      const permissions = computeDecisionPermissions({
        state: 'PENDING_DECISION',
        role: 'ADMINISTRATOR',
        isCreator: false,
        hasOpenRequest: false,
      });

      const approve = permissions.find((p) => p.action === 'APPROVE');
      const reject = permissions.find((p) => p.action === 'REJECT');
      const escalate = permissions.find((p) => p.action === 'ESCALATE');

      expect(approve?.permitted).toBe(true);
      expect(reject?.permitted).toBe(true);
      expect(escalate?.permitted).toBe(true);
    });

    it('still blocks APPROVE/REJECT for creator (separation of duties)', () => {
      const permissions = computeDecisionPermissions({
        state: 'PENDING_DECISION',
        role: 'ADMINISTRATOR',
        isCreator: true,
        hasOpenRequest: false,
      });

      const approve = permissions.find((p) => p.action === 'APPROVE');
      const reject = permissions.find((p) => p.action === 'REJECT');

      expect(approve?.permitted).toBe(false);
      expect(reject?.permitted).toBe(false);
    });
  });
});

describe('hasAnyDecisionPermission', () => {
  it('returns true when at least one action is permitted', () => {
    const permissions = computeDecisionPermissions({
      state: 'PENDING_DECISION',
      role: 'AML_OFFICER',
      isCreator: false,
      hasOpenRequest: false,
    });

    expect(hasAnyDecisionPermission(permissions)).toBe(true);
  });

  it('returns false when no actions are permitted', () => {
    const permissions = computeDecisionPermissions({
      state: 'APPROVED',
      role: 'AML_OFFICER',
      isCreator: false,
      hasOpenRequest: false,
    });

    expect(hasAnyDecisionPermission(permissions)).toBe(false);
  });
});

describe('getPermittedActions', () => {
  it('returns only permitted actions', () => {
    const permissions = computeDecisionPermissions({
      state: 'PENDING_DECISION',
      role: 'AML_OFFICER',
      isCreator: false,
      hasOpenRequest: false,
    });

    const permitted = getPermittedActions(permissions);

    expect(permitted).toContain('APPROVE');
    expect(permitted).toContain('REJECT');
    expect(permitted).toContain('ESCALATE');
  });

  it('returns empty array when no actions are permitted', () => {
    const permissions = computeDecisionPermissions({
      state: 'APPROVED',
      role: 'AML_OFFICER',
      isCreator: false,
      hasOpenRequest: false,
    });

    const permitted = getPermittedActions(permissions);

    expect(permitted).toHaveLength(0);
  });
});
