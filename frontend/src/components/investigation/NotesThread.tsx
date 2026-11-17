/**
 * NotesThread component
 * Displays chronological notes with immutable append-only behavior
 * Follows design spec from §5.4 Case workspace components
 */

import { useState } from 'react';
import { TextArea, Button, InlineLoading } from '@carbon/react';
import { NoteSummary } from '../../types/case';

interface NotesThreadProps {
  notes: NoteSummary[];
  onAddNote: (noteText: string) => Promise<void>;
  canAddNote: boolean;
}

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
  return date.toLocaleDateString('en-US', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function NotesThread({ notes, onAddNote, canAddNote }: NotesThreadProps) {
  const [noteText, setNoteText] = useState('');
  const [composerOpen, setComposerOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!noteText.trim()) {
      setError('Note text cannot be empty');
      return;
    }

    if (noteText.length > 4000) {
      setError('Note text cannot exceed 4000 characters');
      return;
    }

    setError(null);
    setSubmitting(true);

    try {
      await onAddNote(noteText.trim());
      setNoteText('');
      setComposerOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add note');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    setNoteText('');
    setComposerOpen(false);
    setError(null);
  };

  return (
    <div data-testid="notes-section" style={{ marginTop: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ fontSize: '16px', lineHeight: '24px', fontWeight: 600, margin: 0 }}>
          Notes
        </h3>
        {canAddNote && !composerOpen && (
          <Button
            kind="ghost"
            size="sm"
            onClick={() => setComposerOpen(true)}
          >
            Add note
          </Button>
        )}
      </div>

      {composerOpen && (
        <div style={{ marginBottom: '24px', background: 'var(--cds-layer-01)', padding: '16px' }}>
          <TextArea
            id="note-composer"
            labelText="Note text"
            placeholder="Record what you've checked (1-4000 characters)"
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            rows={4}
            maxLength={4000}
            enableCounter
            style={{ marginBottom: '16px' }}
          />

          {error && (
            <p style={{ color: 'var(--cds-support-error)', marginBottom: '8px', fontSize: '12px' }}>
              {error}
            </p>
          )}

          <div style={{ display: 'flex', gap: '8px' }}>
            <Button
              kind="primary"
              size="sm"
              onClick={handleSubmit}
              disabled={submitting || !noteText.trim()}
            >
              {submitting ? 'Adding...' : 'Add note'}
            </Button>
            <Button
              kind="secondary"
              size="sm"
              onClick={handleCancel}
              disabled={submitting}
            >
              Cancel
            </Button>
          </div>

          {submitting && (
            <InlineLoading
              description="Adding note..."
              status="active"
              style={{ marginTop: '8px' }}
            />
          )}
        </div>
      )}

      {notes.length === 0 && !composerOpen && (
        <div style={{ textAlign: 'center', padding: '24px', background: 'var(--cds-layer-01)' }}>
          <h3 style={{ fontSize: '20px', fontWeight: 400, margin: '0 0 8px' }}>No notes yet.</h3>
          <p style={{ fontSize: '12px', color: 'var(--cds-text-secondary)', margin: 0 }}>
            Record what you've checked.
          </p>
        </div>
      )}

      {notes.length > 0 && (
        <div style={{ border: '1px solid var(--cds-border-subtle-01)' }}>
          {notes.map((note, index) => (
            <div
              key={note.id}
              style={{
                padding: '16px',
                borderBottom: index < notes.length - 1 ? '1px solid var(--cds-border-subtle-01)' : 'none',
              }}
            >
              <div style={{ fontSize: '12px', color: 'var(--cds-text-secondary)', marginBottom: '8px' }}>
                User {note.created_by_user_id} · {formatTimestamp(note.created_at)}
              </div>
              <div style={{ fontSize: '14px', lineHeight: '20px' }}>
                {note.note_text}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
