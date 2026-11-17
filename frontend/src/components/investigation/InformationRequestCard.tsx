/**
 * InformationRequestCard component
 * Displays information request status with due date and overdue indicator
 * Matches wireframe_05 specification
 */

import { ActionableNotification } from '@carbon/react';
import { WarningAltFilled } from '@carbon/icons-react';
import { InformationRequestSummary } from '../../types/case';

interface InformationRequestCardProps {
  request: InformationRequestSummary;
  onRecordResponse: () => void;
  canRecordResponse: boolean;
}

/**
 * Calculate if request is overdue and how many days
 */
function calculateOverdue(dueDate: string): { isOverdue: boolean; daysOverdue: number } {
  const due = new Date(dueDate);
  const now = new Date();
  const diffMs = now.getTime() - due.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  return {
    isOverdue: diffDays > 0,
    daysOverdue: diffDays,
  };
}

/**
 * Format due date for display
 */
function formatDueDate(dueDate: string): string {
  const date = new Date(dueDate);
  return date.toLocaleDateString('en-US', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).replace(',', '');
}

export function InformationRequestCard({
  request,
  onRecordResponse,
  canRecordResponse,
}: InformationRequestCardProps) {
  const { isOverdue, daysOverdue } = calculateOverdue(request.due_date);
  const formattedDueDate = formatDueDate(request.due_date);

  // Only show card for OPEN or OVERDUE status
  if (request.status === 'RESPONDED' || request.status === 'CANCELLED') {
    return null;
  }

  const title = isOverdue
    ? `Overdue by ${daysOverdue} ${daysOverdue === 1 ? 'day' : 'days'}`
    : `Awaiting response · due ${formattedDueDate}`;

  const subtitle = (
    <div>
      <p><strong>Requested information:</strong> {request.requested_what}</p>
      <p><strong>Reason:</strong> {request.reason}</p>
    </div>
  );

  return (
    <div style={{ marginBottom: '16px' }}>
      <ActionableNotification
        inline
        kind="warning"
        lowContrast={false}
        hideCloseButton
        title={title}
        subtitle={subtitle}
        role="status"
      >
        {isOverdue && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
            <WarningAltFilled size={16} style={{ color: 'var(--cds-support-warning)' }} />
            <span style={{ color: 'var(--cds-text-primary)' }}>
              Overdue by {daysOverdue} {daysOverdue === 1 ? 'day' : 'days'}
            </span>
          </div>
        )}
      </ActionableNotification>
      {canRecordResponse && (
        <button
          onClick={onRecordResponse}
          className="cds--btn cds--btn--primary cds--btn--sm"
          type="button"
          style={{ marginTop: '8px' }}
          data-testid="record-response-button"
        >
          Record response
        </button>
      )}
    </div>
  );
}
