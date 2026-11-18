/**
 * DecisionPanel component
 * Sticky panel showing permitted decision actions for the current case
 * Matches wireframe_07 decision panel design
 */

import { Button } from '@carbon/react';
import { DecisionAction } from '../../lib/decision-actions';

export interface DecisionPanelProps {
  permittedActions: string[];
  onDecisionClick: (action: DecisionAction) => void;
  isBlocked: boolean;
  blockReason?: string;
}

export function DecisionPanel({
  permittedActions,
  onDecisionClick,
  isBlocked,
  blockReason,
}: DecisionPanelProps) {
  // When blocked, only show REQUEST_INFO and ESCALATE actions (not APPROVE/REJECT)
  const visibleActions = isBlocked
    ? permittedActions.filter(action => !['APPROVE', 'REJECT', 'CLOSE_FALSE_POSITIVE'].includes(action))
    : permittedActions;

  const hasApprove = visibleActions.includes('APPROVE');
  const hasReject = visibleActions.includes('REJECT');
  const hasEscalate = visibleActions.includes('ESCALATE');
  const hasCloseFalsePositive = visibleActions.includes('CLOSE_FALSE_POSITIVE');

  return (
    <div
      data-testid="decision-panel"
      style={{
        background: 'var(--cds-layer-01)',
        padding: '16px',
        position: 'sticky',
        top: '64px',
      }}
    >
      <h2
        style={{
          fontSize: '20px',
          lineHeight: '28px',
          fontWeight: 400,
          margin: '0 0 8px',
        }}
      >
        Decision
      </h2>

      <p style={{
        fontSize: '14px',
        color: 'var(--cds-text-secondary)',
        margin: '0 0 16px',
      }}>
        Permitted actions
      </p>

      {isBlocked && blockReason ? (
        <div
          style={{
            display: 'flex',
            gap: '12px',
            padding: '12px 16px',
            background: 'var(--cds-layer-01)',
            border: '1px solid var(--cds-border-subtle-01)',
            borderLeft: '3px solid var(--cds-support-warning)',
            marginBottom: '8px',
          }}
          role="status"
        >
          <div
            style={{
              flex: 'none',
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              background: 'var(--cds-support-warning)',
              color: 'var(--cds-text-primary)',
              fontSize: '11px',
              lineHeight: '16px',
              textAlign: 'center',
              fontWeight: 600,
            }}
          >
            !
          </div>
          <div>
            <b style={{ fontWeight: 600 }}>{blockReason}</b>
          </div>
        </div>
      ) : null}

      {hasApprove && (
        <Button
          kind="primary"
          data-testid="decision-action-approve"
          onClick={() => onDecisionClick('APPROVE')}
          style={{
            width: '100%',
            justifyContent: 'flex-start',
            marginBottom: '16px',
          }}
        >
          Approve
        </Button>
      )}

      {hasReject && (
        <Button
          kind="danger--tertiary"
          data-testid="decision-action-reject"
          onClick={() => onDecisionClick('REJECT')}
          style={{
            width: '100%',
            justifyContent: 'flex-start',
            marginBottom: '16px',
          }}
        >
          Reject
        </Button>
      )}

      {hasEscalate && (
        <Button
          kind="secondary"
          data-testid="decision-action-escalate"
          onClick={() => onDecisionClick('ESCALATE')}
          style={{
            width: '100%',
            justifyContent: 'flex-start',
            marginBottom: '16px',
          }}
        >
          Escalate
        </Button>
      )}

      {hasCloseFalsePositive && (
        <Button
          kind="ghost"
          data-testid="decision-action-close-false-positive"
          onClick={() => onDecisionClick('CLOSE_FALSE_POSITIVE')}
          style={{
            width: '100%',
            justifyContent: 'flex-start',
            marginBottom: '16px',
          }}
        >
          Close as false positive
        </Button>
      )}

      {!isBlocked && (hasApprove || hasReject || hasEscalate || hasCloseFalsePositive) && (
        <p
          style={{
            fontSize: '12px',
            lineHeight: '16px',
            color: 'var(--cds-text-secondary)',
            margin: 0,
          }}
        >
          Decisions are final and recorded in the audit trail.
        </p>
      )}
    </div>
  );
}
