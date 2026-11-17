/**
 * RequestInfoDialog component
 * Modal for requesting additional information during case investigation
 * Follows design spec dialog patterns from wireframe_06
 */

import { useState } from 'react';
import { Modal, TextArea, DatePicker, DatePickerInput, InlineLoading } from '@carbon/react';

interface RequestInfoDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: { requested_what: string; reason: string; due_date: string }) => Promise<void>;
}

export function RequestInfoDialog({ open, onClose, onSubmit }: RequestInfoDialogProps) {
  const [requestedWhat, setRequestedWhat] = useState('');
  const [reason, setReason] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);

    // Validate required fields
    if (!requestedWhat.trim()) {
      setError('Information requested is required');
      return;
    }
    if (!reason.trim()) {
      setError('Reason is required');
      return;
    }
    if (!dueDate) {
      setError('Due date is required');
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit({
        requested_what: requestedWhat.trim(),
        reason: reason.trim(),
        due_date: dueDate,
      });
      // Clear form on success
      setRequestedWhat('');
      setReason('');
      setDueDate('');
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit request');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!submitting) {
      setRequestedWhat('');
      setReason('');
      setDueDate('');
      setError(null);
      onClose();
    }
  };

  const today = new Date().toISOString().split('T')[0];

  return (
    <Modal
      open={open}
      onRequestClose={handleClose}
      onRequestSubmit={handleSubmit}
      modalHeading="Request information"
      primaryButtonText="Send request"
      secondaryButtonText="Cancel"
      primaryButtonDisabled={submitting || !requestedWhat.trim() || !reason.trim() || !dueDate}
      size="sm"
    >
      <p style={{ marginBottom: '16px', color: 'var(--cds-text-secondary)', fontSize: '14px' }}>
        Case moves to Information requested. Decisions are blocked until a response is recorded.
      </p>

      <TextArea
        id="requested-what"
        labelText="Information requested (required)"
        placeholder="Describe what information is needed"
        value={requestedWhat}
        onChange={(e) => setRequestedWhat(e.target.value)}
        rows={3}
        style={{ marginBottom: '16px' }}
      />

      <TextArea
        id="reason"
        labelText="Reason (required)"
        placeholder="Explain why this information is needed"
        value={reason}
        onChange={(e) => setReason(e.target.value)}
        rows={3}
        style={{ marginBottom: '16px' }}
      />

      <DatePicker
        datePickerType="single"
        minDate={today}
        onChange={(dates) => {
          if (dates && dates.length > 0) {
            setDueDate(dates[0].toISOString().split('T')[0]);
          }
        }}
      >
        <DatePickerInput
          id="due-date"
          labelText="Due date (required)"
          placeholder="mm/dd/yyyy"
          onChange={(e) => {
            // Handle manual text input for testing
            const value = e.target.value;
            if (value && /^\d{4}-\d{2}-\d{2}$/.test(value)) {
              setDueDate(value);
            }
          }}
        />
      </DatePicker>

      {error && (
        <p style={{ color: 'var(--cds-support-error)', marginTop: '16px', fontSize: '12px' }}>
          {error}
        </p>
      )}

      {submitting && (
        <InlineLoading
          description="Submitting request..."
          status="active"
          style={{ marginTop: '16px' }}
        />
      )}
    </Modal>
  );
}
