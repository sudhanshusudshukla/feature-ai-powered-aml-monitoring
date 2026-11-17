/**
 * Component tests for TransactionDetailPage
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { TransactionDetailPage } from '../TransactionDetailPage';
import { transactionApi } from '../../../lib/transaction-api';
import { ApiError } from '../../../lib/api-client';

vi.mock('../../../lib/transaction-api', () => ({
  transactionApi: {
    getTransactionDetail: vi.fn(),
  },
}));

const mockGetTransactionDetail = transactionApi.getTransactionDetail as ReturnType<typeof vi.fn>;

function renderPage(transactionId = '1') {
  return render(
    <MemoryRouter initialEntries={[`/transactions/${transactionId}`]}>
      <Routes>
        <Route path="/transactions/:id" element={<TransactionDetailPage />} />
      </Routes>
    </MemoryRouter>
  );
}

const mockTransaction = {
  id: 1,
  transaction_reference: 'TXN-2026-004217',
  account_id: 1,
  amount: '850000.00',
  currency: 'INR',
  transaction_type: 'TRANSFER',
  origin_country: 'IN',
  destination_country: 'AE',
  counterparty_name: 'Al Noor Trading FZE',
  counterparty_account: 'AE07 0331 2345 6789 0123 456',
  timestamp: '2026-11-03T08:35:00Z',
  matched_rules_count: 4,
  alert_raised: true,
  alert_id: 1184,
  correlation_id: 'c0a8f3e2-4b1e-4d3a-9e55-2a6b8c01d4f7',
  evaluation_results: [
    { rule_code: 'AML-001', rule_name: 'High Value', rule_version: 1, outcome: 'MATCH', severity: 'HIGH', score: 28, explanation: 'Test', evidence_snapshot: {} },
    { rule_code: 'AML-002', rule_name: 'Velocity', rule_version: 1, outcome: 'PASS', severity: 'MEDIUM', score: 0, explanation: 'Test', evidence_snapshot: {} },
    { rule_code: 'AML-003', rule_name: 'Amount', rule_version: 1, outcome: 'MATCH', severity: 'HIGH', score: 16, explanation: 'Test', evidence_snapshot: {} },
    { rule_code: 'AML-004', rule_name: 'Geography', rule_version: 1, outcome: 'MATCH', severity: 'MEDIUM', score: 22, explanation: 'Test', evidence_snapshot: {} },
    { rule_code: 'AML-005', rule_name: 'PEP', rule_version: 1, outcome: 'PASS', severity: 'CRITICAL', score: 0, explanation: 'Test', evidence_snapshot: {} },
    { rule_code: 'AML-006', rule_name: 'Structuring', rule_version: 1, outcome: 'PASS', severity: 'HIGH', score: 0, explanation: 'Test', evidence_snapshot: {} },
    { rule_code: 'AML-007', rule_name: 'Dormancy', rule_version: 1, outcome: 'PASS', severity: 'MEDIUM', score: 0, explanation: 'Test', evidence_snapshot: {} },
    { rule_code: 'AML-008', rule_name: 'Round', rule_version: 1, outcome: 'MATCH', severity: 'LOW', score: 9, explanation: 'Test', evidence_snapshot: {} },
  ],
  account_number: 'ACC-7720-4411-09',
  customer_name: 'Rohan Mehta',
  customer_risk: 'HIGH',
  pep_status: false,
  account_status: 'Active',
};

describe('TransactionDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads and displays transaction details', async () => {
    mockGetTransactionDetail.mockResolvedValue(mockTransaction);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Transaction TXN-2026-004217/i)).toBeInTheDocument();
    });

    expect(screen.getByTestId('transaction-outcome-tag')).toBeInTheDocument();
    expect(screen.getByText(/Screened on receipt against 8 rules/i)).toBeInTheDocument();
  });

  it('displays transaction summary with all fields', async () => {
    mockGetTransactionDetail.mockResolvedValue(mockTransaction);
    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/Transaction summary/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Amount/i)).toBeInTheDocument();
    expect(screen.getByText(/Date/i)).toBeInTheDocument();
    expect(screen.getByText(/From account/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Customer risk/i).length).toBeGreaterThan(0);
  });

  it('displays screening run steps', async () => {
    mockGetTransactionDetail.mockResolvedValue(mockTransaction);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Screening run/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Account and customer context loaded/i)).toBeInTheDocument();
    expect(screen.getByText(/Transaction persisted/i)).toBeInTheDocument();
    expect(screen.getByText(/rules evaluated and persisted/i)).toBeInTheDocument();
    expect(screen.getByText(/Audit events written with the same correlation ID/i)).toBeInTheDocument();
  });

  it('displays result summary with matched and passed rules', async () => {
    mockGetTransactionDetail.mockResolvedValue(mockTransaction);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Result summary/i)).toBeInTheDocument();
    });

    // Should show rule codes in summary
    expect(screen.getByText(/AML-001/)).toBeInTheDocument();
    expect(screen.getByText(/AML-002/)).toBeInTheDocument();
  });

  it('displays account and customer context panel', async () => {
    mockGetTransactionDetail.mockResolvedValue(mockTransaction);
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /Account and customer context/i })).toBeInTheDocument();
    });

    expect(screen.getAllByText(/Rohan Mehta/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/ACC-7720-4411-09/).length).toBeGreaterThan(0);
    expect(screen.getByText(/PEP customer/i)).toBeInTheDocument();
  });

  it('displays correlation ID', async () => {
    mockGetTransactionDetail.mockResolvedValue(mockTransaction);
    renderPage();

    await waitFor(() => {
      expect(screen.getByTestId('error-correlation-id')).toBeInTheDocument();
    });
  });

  it('shows 404 message for non-existent transaction', async () => {
    mockGetTransactionDetail.mockRejectedValue(new ApiError(404, 'NOT_FOUND', 'Transaction not found'));
    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Transaction not found/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/No transaction matches this ID/i)).toBeInTheDocument();
    expect(screen.getByText(/Back to transactions/i)).toBeInTheDocument();
  });

  it('shows error notification for other errors', async () => {
    mockGetTransactionDetail.mockRejectedValue(new Error('Server error'));
    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Something went wrong/i)).toBeInTheDocument();
    });
  });

  it('displays breadcrumb navigation', async () => {
    mockGetTransactionDetail.mockResolvedValue(mockTransaction);
    renderPage();

    await waitFor(() => {
      expect(screen.getByRole('navigation')).toBeInTheDocument();
    });

    const breadcrumbs = screen.getAllByText(/TXN-2026-004217/);
    expect(breadcrumbs.length).toBeGreaterThan(0);
  });

  it('shows loading state initially', async () => {
    mockGetTransactionDetail.mockImplementation(() => new Promise(() => {}));
    renderPage();

    // Loading skeleton should be visible
    await waitFor(() => {
      const skeletons = document.querySelectorAll('[class*="cds--skeleton"]');
      expect(skeletons.length).toBeGreaterThan(0);
    });
  });
});
