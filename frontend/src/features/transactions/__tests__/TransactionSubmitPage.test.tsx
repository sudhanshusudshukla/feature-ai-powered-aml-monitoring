/**
 * Component tests for TransactionSubmitPage
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { TransactionSubmitPage } from '../TransactionSubmitPage';
import { transactionApi } from '../../../lib/transaction-api';
import { ApiError } from '../../../lib/api-client';

vi.mock('../../../lib/transaction-api', () => ({
  transactionApi: {
    submitTransaction: vi.fn(),
  },
}));

const mockSubmitTransaction = transactionApi.submitTransaction as ReturnType<typeof vi.fn>;

function renderPage() {
  return render(
    <BrowserRouter>
      <TransactionSubmitPage />
    </BrowserRouter>
  );
}

describe('TransactionSubmitPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page title and form', () => {
    renderPage();

    expect(screen.getByRole('heading', { name: /submit transaction/i })).toBeInTheDocument();
    expect(screen.getByText(/synthetic data only/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit for screening/i })).toBeInTheDocument();
  });

  it('displays success toast after successful submission', async () => {
    const mockResponse = {
      id: 1,
      transaction_reference: 'TXN-2026-001234',
      account_id: 1,
      amount: '850000.00',
      currency: 'INR',
      transaction_type: 'TRANSFER' as const,
      origin_country: 'IN',
      destination_country: 'AE',
      timestamp: '2026-11-03T08:35:00Z',
      matched_rules_count: 4,
      alert_raised: true,
      alert_id: 1184,
      correlation_id: 'c0a8f3e2-4b1e-4d3a-9e55-2a6b8c01d4f7',
      evaluation_results: [
        { rule_code: 'AML-001', rule_name: 'Test', rule_version: 1, outcome: 'MATCH' as const, severity: 'HIGH' as const, score: 28, explanation: 'Test', evidence_snapshot: {} },
        { rule_code: 'AML-002', rule_name: 'Test', rule_version: 1, outcome: 'PASS' as const, severity: 'MEDIUM' as const, score: 0, explanation: 'Test', evidence_snapshot: {} },
        { rule_code: 'AML-003', rule_name: 'Test', rule_version: 1, outcome: 'MATCH' as const, severity: 'HIGH' as const, score: 16, explanation: 'Test', evidence_snapshot: {} },
        { rule_code: 'AML-004', rule_name: 'Test', rule_version: 1, outcome: 'MATCH' as const, severity: 'MEDIUM' as const, score: 22, explanation: 'Test', evidence_snapshot: {} },
        { rule_code: 'AML-005', rule_name: 'Test', rule_version: 1, outcome: 'PASS' as const, severity: 'CRITICAL' as const, score: 0, explanation: 'Test', evidence_snapshot: {} },
        { rule_code: 'AML-006', rule_name: 'Test', rule_version: 1, outcome: 'PASS' as const, severity: 'HIGH' as const, score: 0, explanation: 'Test', evidence_snapshot: {} },
        { rule_code: 'AML-007', rule_name: 'Test', rule_version: 1, outcome: 'PASS' as const, severity: 'MEDIUM' as const, score: 0, explanation: 'Test', evidence_snapshot: {} },
        { rule_code: 'AML-008', rule_name: 'Test', rule_version: 1, outcome: 'MATCH' as const, severity: 'LOW' as const, score: 9, explanation: 'Test', evidence_snapshot: {} },
      ],
    };

    mockSubmitTransaction.mockResolvedValue(mockResponse);
    renderPage();

    const submitButton = screen.getByRole('button', { name: /submit for screening/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/transaction received and screened/i)).toBeInTheDocument();
    });

    expect(screen.getAllByText(/TXN-2026-001234/).length).toBeGreaterThan(0);
    expect(screen.getByText(/4 of 8 rules matched/i)).toBeInTheDocument();
  });

  it('displays response panel with evaluation results', async () => {
    const mockResponse = {
      id: 1,
      transaction_reference: 'TXN-2026-001234',
      account_id: 1,
      amount: '850000.00',
      currency: 'INR',
      transaction_type: 'TRANSFER' as const,
      origin_country: 'IN',
      destination_country: 'AE',
      timestamp: '2026-11-03T08:35:00Z',
      matched_rules_count: 2,
      alert_raised: false,
      alert_id: null,
      correlation_id: 'test-correlation-id',
      evaluation_results: [
        { rule_code: 'AML-001', rule_name: 'Test', rule_version: 1, outcome: 'MATCH' as const, severity: 'HIGH' as const, score: 28, explanation: 'Test', evidence_snapshot: {} },
        { rule_code: 'AML-002', rule_name: 'Test', rule_version: 1, outcome: 'PASS' as const, severity: 'MEDIUM' as const, score: 0, explanation: 'Test', evidence_snapshot: {} },
      ],
    };

    mockSubmitTransaction.mockResolvedValue(mockResponse);
    renderPage();

    const submitButton = screen.getByRole('button', { name: /submit for screening/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/HTTP 201/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/matchedRulesCount/i)).toBeInTheDocument();
    expect(screen.getByText(/alertRaised/i)).toBeInTheDocument();
    expect(screen.getByTestId('rule-result-AML-001')).toBeInTheDocument();
    expect(screen.getByTestId('rule-result-AML-002')).toBeInTheDocument();
  });

  it('displays error notification on submission failure', async () => {
    mockSubmitTransaction.mockRejectedValue(new ApiError(404, 'NOT_FOUND', 'Account not found'));
    renderPage();

    const submitButton = screen.getByRole('button', { name: /submit for screening/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/account not found/i)).toBeInTheDocument();
    });
  });

  it('renders look up transaction section', () => {
    renderPage();

    expect(screen.getByRole('heading', { name: /look up transaction/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/transaction id/i)).toBeInTheDocument();
  });
});
