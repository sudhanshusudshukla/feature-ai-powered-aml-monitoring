/**
 * DecisionDialog component
 * Modal for recording case decisions with validation
 * Matches wireframe_07 decision dialog design
 */

import { useState } from 'react';
import { Modal, TextInput, TextArea } from '@carbon/react';
import { DecisionAction } from '../../lib/decision-actions';

export interface DecisionDialogProps {
  open: boolean;
  action: DecisionAction | null;
  onClose: () => void;
  onSubmit: (data: {
    decision: DecisionAction;
    reason?: string;
    comments?: string;
  }) => void;
  isSubmitting?: boolean;
}

interface DecisionConfig {
  title: string;
  consequence: string;
  requireReason: boolean;
  requireComments: boolean;
  buttonKind: 'primary' | 'danger';
  buttonLabel: string;
}

const DECISION_CONFIGS: Record<DecisionAction, DecisionConfig> = {
  APPROVE: {
    title: 'Approve case',
    consequence: 'This decision is final and recorded in the audit trail.',
    requireReason: false,
    requireComments: true,
    buttonKind: 'primary',
    buttonLabel: 'Approve case',
  },
  REJECT: {
    title: 'Reject case',
    consequence: 'This decision is final and recorded in the audit trail.',
    requireReason: true,
    requireComments: true,
    buttonKind: 'danger',
    buttonLabel: 'Reject case',
  },
  ESCALATE: {
    title: 'Escalate',
    consequence: 'Case moves to Escalated.',
    requireReason: true,
    requireComments: true,
    buttonKind: 'primary',
    buttonLabel: 'Escalate',
  },
  CLOSE_FALSE_POSITIVE: {
    title: 'Close as false positive',
    consequence: 'Case closes and all linked alerts are closed.',
    requireReason: true,
    requireComments: true,
    buttonKind: 'danger',
    buttonLabel: 'Close as false positive',
  },
};

export function DecisionDialog({
  open,
  action,
  onClose,
  onSubmit,
  isSubmitting = false,
}: DecisionDialogProps) {
  const [reason, setReason] = useState('');
  const [comments, setComments] = useState('');
  const [errors, setErrors] = useState<{
    reason?: string;
    comments?: string;
  }>({});

  if (!action) return null;

  const config = DECISION_CONFIGS[action];

  const handleSubmit = () => {
    const newErrors: typeof errors = {};

    if (config.requireReason && !reason.trim()) {
      newErrors.reason = 'Reason is required';
    }

    if (config.requireComments && !comments.trim()) {
      newErrors.comments = 'Comments are required';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    onSubmit({
      decision: action,
      reason: reason.trim() || undefined,
      comments: comments.trim() || undefined,
    });
  };

  const handleClose = () => {
    setReason('');
    setComments('');
    setErrors({});
    onClose();
  };

  return (
    <Modal
      open={open}
      onRequestClose={handleClose}
      modalHeading={config.title}
      primaryButtonText={isSubmitting ? 'Submitting…' : config.buttonLabel}
      secondaryButtonText="Cancel"
      onRequestSubmit={handleSubmit}
      primaryButtonDisabled={isSubmitting}
      danger={config.buttonKind === 'danger'}
      size="sm"
    >
      <div style={{ marginBottom: '16px' }}>
        <p style={{ margin: 0, fontSize: '14px', lineHeight: '20px' }}>
          {config.consequence}
        </p>
      </div>

      {config.requireReason && (
        <div style={{ marginBottom: '16px' }}>
          <TextInput
            id="decision-reason"
            labelText="Reason (required)"
            value={reason}
            onChange={(e) => {
              setReason(e.target.value);
              if (errors.reason) {
                setErrors({ ...errors, reason: undefined });
              }
            }}
            invalid={!!errors.reason}
            invalidText={errors.reason}
          />
        </div>
      )}

      <div style={{ marginBottom: '16px' }}>
        <TextArea
          id="decision-comments"
          labelText={
            config.requireComments ? 'Comments (required)' : 'Comments (optional)'
          }
          value={comments}
          onChange={(e) => {
            setComments(e.target.value);
            if (errors.comments) {
              setErrors({ ...errors, comments: undefined });
            }
          }}
          invalid={!!errors.comments}
          invalidText={errors.comments}
          rows={4}
        />
      </div>
    </Modal>
  );
}
