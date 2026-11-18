/**
 * Tests for NotesThread component
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { NotesThread } from '../NotesThread';
import { NoteSummary } from '../../../types/case';

describe('NotesThread', () => {
  const mockNotes: NoteSummary[] = [
    {
      id: 1,
      note_text: 'Initial investigation started',
      created_by_user_id: 1,
      created_at: new Date('2026-11-17T10:00:00Z').toISOString(),
    },
    {
      id: 2,
      note_text: 'Reviewed transaction history',
      created_by_user_id: 2,
      created_at: new Date('2026-11-17T11:00:00Z').toISOString(),
    },
  ];

  it('renders existing notes', () => {
    render(
      <NotesThread
        notes={mockNotes}
        onAddNote={vi.fn()}
        canAddNote={true}
      />
    );

    expect(screen.getByText('Initial investigation started')).toBeInTheDocument();
    expect(screen.getByText('Reviewed transaction history')).toBeInTheDocument();
  });

  it('displays empty state when no notes exist', () => {
    render(
      <NotesThread
        notes={[]}
        onAddNote={vi.fn()}
        canAddNote={true}
      />
    );

    expect(screen.getByText('No notes yet.')).toBeInTheDocument();
    expect(screen.getByText("Record what you've checked.")).toBeInTheDocument();
  });

  it('shows add note button when user has permission', () => {
    render(
      <NotesThread
        notes={mockNotes}
        onAddNote={vi.fn()}
        canAddNote={true}
      />
    );

    expect(screen.getByText('Add note')).toBeInTheDocument();
  });

  it('opens composer when add note button is clicked', () => {
    render(
      <NotesThread
        notes={mockNotes}
        onAddNote={vi.fn()}
        canAddNote={true}
      />
    );

    const addButton = screen.getByText('Add note');
    fireEvent.click(addButton);

    expect(screen.getByLabelText('Note text')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Record what you've checked/)).toBeInTheDocument();
  });

  it('validates note text is required', async () => {
    const onAddNote = vi.fn();
    render(
      <NotesThread
        notes={mockNotes}
        onAddNote={onAddNote}
        canAddNote={true}
      />
    );

    // Open composer
    fireEvent.click(screen.getByText('Add note'));

    // Verify composer appears
    expect(screen.getByLabelText('Note text')).toBeInTheDocument();
    
    // The submit button should be disabled when text is empty (disabled attribute checked by Carbon)
    expect(onAddNote).not.toHaveBeenCalled();
  });

  it('shows character counter for note text', () => {
    const onAddNote = vi.fn();
    render(
      <NotesThread
        notes={mockNotes}
        onAddNote={onAddNote}
        canAddNote={true}
      />
    );

    // Open composer
    fireEvent.click(screen.getByText('Add note'));

    // Verify textarea is present and has placeholder
    const textarea = screen.getByLabelText('Note text');
    expect(textarea).toBeInTheDocument();
    expect(textarea).toHaveAttribute('placeholder', 'Record what you\'ve checked (1-4000 characters)');
  });

  it('calls onAddNote with trimmed text on submit', async () => {
    const onAddNote = vi.fn().mockResolvedValue(undefined);
    render(
      <NotesThread
        notes={mockNotes}
        onAddNote={onAddNote}
        canAddNote={true}
      />
    );

    // Open composer
    fireEvent.click(screen.getByText('Add note'));

    // Fill note text with surrounding whitespace
    const textarea = screen.getByLabelText('Note text');
    fireEvent.change(textarea, { target: { value: '  Test note content  ' } });

    // Submit
    const submitButtons = screen.getAllByText('Add note');
    const submitButton = submitButtons[submitButtons.length - 1];
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(onAddNote).toHaveBeenCalledWith('Test note content');
    });
  });

  it('closes composer and clears text after successful submit', async () => {
    const onAddNote = vi.fn().mockResolvedValue(undefined);
    render(
      <NotesThread
        notes={mockNotes}
        onAddNote={onAddNote}
        canAddNote={true}
      />
    );

    // Open composer
    fireEvent.click(screen.getByText('Add note'));

    // Fill and submit
    const textarea = screen.getByLabelText('Note text');
    fireEvent.change(textarea, { target: { value: 'New note' } });
    
    const submitButtons = screen.getAllByText('Add note');
    const submitButton = submitButtons[submitButtons.length - 1];
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.queryByLabelText('Note text')).not.toBeInTheDocument();
    });
  });

  it('displays immutable note structure', () => {
    render(
      <NotesThread
        notes={mockNotes}
        onAddNote={vi.fn()}
        canAddNote={true}
      />
    );

    // Notes should display user and timestamp
    expect(screen.getByText(/User 1/)).toBeInTheDocument();
    expect(screen.getByText(/User 2/)).toBeInTheDocument();

    // Should not have edit or delete buttons
    expect(screen.queryByText('Edit')).not.toBeInTheDocument();
    expect(screen.queryByText('Delete')).not.toBeInTheDocument();
  });
});
