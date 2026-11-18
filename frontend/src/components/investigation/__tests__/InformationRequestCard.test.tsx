/**
 * Tests for InformationRequestCard component
 */

import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { InformationRequestCard } from '../InformationRequestCard';
import { InformationRequestSummary } from '../../../types/case';

describe('InformationRequestCard', () => {
  const mockRequest: InformationRequestSummary = {
    id: 1,
    requested_what: 'Bank statements for last 3 months',
    reason: 'Verify transaction history',
    due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 7 days from now
    status: 'OPEN',
    requested_by_user_id: 1,
    created_at: new Date().toISOString(),
  };

  it('renders request information', () => {
    render(
      <InformationRequestCard
        request={mockRequest}
        onRecordResponse={vi.fn()}
        canRecordResponse={true}
      />
    );

    expect(screen.getByText(/Bank statements for last 3 months/)).toBeInTheDocument();
    expect(screen.getByText(/Verify transaction history/)).toBeInTheDocument();
    expect(screen.getByText(/Awaiting response/)).toBeInTheDocument();
  });

  it('shows record response button when user has permission', () => {
    render(
      <InformationRequestCard
        request={mockRequest}
        onRecordResponse={vi.fn()}
        canRecordResponse={true}
      />
    );

    expect(screen.getByText('Record response')).toBeInTheDocument();
  });

  it('hides record response button when user lacks permission', () => {
    render(
      <InformationRequestCard
        request={mockRequest}
        onRecordResponse={vi.fn()}
        canRecordResponse={false}
      />
    );

    expect(screen.queryByText('Record response')).not.toBeInTheDocument();
  });

  it('calculates and displays overdue status', () => {
    const overdueRequest: InformationRequestSummary = {
      ...mockRequest,
      due_date: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), // 3 days ago
    };

    render(
      <InformationRequestCard
        request={overdueRequest}
        onRecordResponse={vi.fn()}
        canRecordResponse={true}
      />
    );

    // Check for overdue text - there may be multiple instances
    const overdueElements = screen.getAllByText(/Overdue by/);
    expect(overdueElements.length).toBeGreaterThan(0);
    expect(screen.getAllByText(/days/).length).toBeGreaterThan(0);
  });

  it('does not render for responded requests', () => {
    const respondedRequest: InformationRequestSummary = {
      ...mockRequest,
      status: 'RESPONDED',
    };

    const { container } = render(
      <InformationRequestCard
        request={respondedRequest}
        onRecordResponse={vi.fn()}
        canRecordResponse={true}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('does not render for cancelled requests', () => {
    const cancelledRequest: InformationRequestSummary = {
      ...mockRequest,
      status: 'CANCELLED',
    };

    const { container } = render(
      <InformationRequestCard
        request={cancelledRequest}
        onRecordResponse={vi.fn()}
        canRecordResponse={true}
      />
    );

    expect(container.firstChild).toBeNull();
  });
});
