/**
 * RecordResponseDialog component
 * Modal for recording response to information request
 * Follows design spec dialog patterns from wireframe_06
 */

import { useState } from 'react';
import { Modal, TextArea, TextInput, InlineLoading } from '@carbon/react';

interface RecordResponseDialogProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: { response_text: string; evidence_reference?: string }) => Promise<void>;
}

export function RecordResponseDialog({ open, onClose, onSubmit }: RecordResponseDialogProps) {
  const [responseText, setResponseText] = useState('');
  const [evidenceReference, setEvidenceReference] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    setError(null);

    // Validate required fields
    if (!responseText.trim()) {
      setError('Response text is required');
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit({
        response_text: responseText.trim(),
        evidence_reference: evidenceReference.trim() || undefined,
      });
      // Clear form on success
      setResponseText('');
      setEvidenceReference('');
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record response');
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!submitting) {
      setResponseText('');
      setEvidenceReference('');
      setError(null);
      onClose();
    }
  };

  return (
    <Modal
      open={open}
      onRequestClose={handleClose}
      onRequestSubmit={handleSubmit}
      modalHeading="Record response"
      primaryButtonText="Record response"
      secondaryButtonText="Cancel"
      primaryButtonDisabled={submitting || !responseText.trim()}
      size="sm"
    >
      <p style={{ marginBottom: '16px', color: 'var(--cds-text-secondary)', fontSize: '14px' }}>
        Investigation resumes.
      </p>

      <TextArea
        id="response-text"
        labelText="Response (required)"
        placeholder="Enter the response to the information request"
        value={responseText}
        onChange={(e) => setResponseText(e.target.value)}
        rows={5}
        style={{ marginBottom: '16px' }}
      />

      <TextInput
        id="evidence-reference"
        labelText="Evidence reference (optional)"
        placeholder="Document reference or identifier"
        value={evidenceReference}
        onChange={(e) => setEvidenceReference(e.target.value)}
      />

      {error && (
        <p style={{ color: 'var(--cds-support-error)', marginTop: '16px', fontSize: '12px' }}>
          {error}
        </p>
      )}

      {submitting && (
        <InlineLoading
          description="Recording response..."
          status="active"
          style={{ marginTop: '16px' }}
        />
      )}
    </Modal>
  );
}
