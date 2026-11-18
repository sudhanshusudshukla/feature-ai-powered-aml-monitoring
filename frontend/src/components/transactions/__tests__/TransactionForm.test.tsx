/**
 * Component tests for TransactionForm
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { TransactionForm } from '../TransactionForm';

describe('TransactionForm', () => {
  it('renders all required form fields', () => {
    const mockSubmit = vi.fn();
    render(<TransactionForm onSubmit={mockSubmit} loading={false} error={null} />);

    expect(screen.getByLabelText(/transaction reference/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^account \(required\)$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/amount/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/currency/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/transaction type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/timestamp/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/origin country/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/destination country/i)).toBeInTheDocument();
  });

  it('validates required fields before submission', async () => {
    const mockSubmit = vi.fn();
    render(<TransactionForm onSubmit={mockSubmit} loading={false} error={null} />);

    // Clear amount field
    const amountInput = screen.getByLabelText(/amount/i);
    fireEvent.change(amountInput, { target: { value: '' } });

    // Submit form
    const submitButton = screen.getByRole('button', { name: /submit for screening/i });
    fireEvent.click(submitButton);

    // Assert validation error appears
    await waitFor(() => {
      expect(screen.getByText(/amount is required/i)).toBeInTheDocument();
    });

    // Assert onSubmit was not called
    expect(mockSubmit).not.toHaveBeenCalled();
  });

  it('calls onSubmit with form data when valid', async () => {
    const mockSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TransactionForm onSubmit={mockSubmit} loading={false} error={null} />);

    // Form has default values, so we can submit directly
    const submitButton = screen.getByRole('button', { name: /submit for screening/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalledTimes(1);
    });

    // Assert payload structure
    const payload = mockSubmit.mock.calls[0][0];
    expect(payload).toHaveProperty('transaction_reference');
    expect(payload).toHaveProperty('account_id');
    expect(payload).toHaveProperty('amount');
    expect(payload).toHaveProperty('transaction_type');
    expect(payload).toHaveProperty('origin_country');
    expect(payload).toHaveProperty('destination_country');
    expect(payload).toHaveProperty('timestamp');
  });

  it('disables form fields when loading', () => {
    const mockSubmit = vi.fn();
    render(<TransactionForm onSubmit={mockSubmit} loading={true} error={null} />);

    const amountInput = screen.getByLabelText(/amount/i);
    const submitButton = screen.getByRole('button', { name: /screening transaction/i });

    expect(amountInput).toBeDisabled();
    expect(submitButton).toBeDisabled();
  });

  it('displays error notification when error prop is provided', () => {
    const mockSubmit = vi.fn();
    render(
      <TransactionForm
        onSubmit={mockSubmit}
        loading={false}
        error="Account not found"
      />
    );

    expect(screen.getByText(/submission failed/i)).toBeInTheDocument();
    expect(screen.getByText(/account not found/i)).toBeInTheDocument();
  });

  it('clears form when reset button is clicked', async () => {
    const mockSubmit = vi.fn();
    render(<TransactionForm onSubmit={mockSubmit} loading={false} error={null} />);

    // Change a field
    const amountInput = screen.getByLabelText(/amount/i);
    fireEvent.change(amountInput, { target: { value: '12345.00' } });
    expect(amountInput).toHaveValue('12345.00');

    // Click reset
    const resetButton = screen.getByRole('button', { name: /clear form/i });
    fireEvent.click(resetButton);

    // Assert form is reset (amount will be back to default 850000.00)
    await waitFor(() => {
      expect(amountInput).toHaveValue('850000.00');
    });
  });

  it('converts account_id to integer in payload', async () => {
    const mockSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TransactionForm onSubmit={mockSubmit} loading={false} error={null} />);

    const submitButton = screen.getByRole('button', { name: /submit for screening/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalled();
    });

    const payload = mockSubmit.mock.calls[0][0];
    expect(typeof payload.account_id).toBe('number');
  });

  it('includes optional counterparty fields when provided', async () => {
    const mockSubmit = vi.fn().mockResolvedValue(undefined);
    render(<TransactionForm onSubmit={mockSubmit} loading={false} error={null} />);

    // Default values include counterparty info
    const submitButton = screen.getByRole('button', { name: /submit for screening/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockSubmit).toHaveBeenCalled();
    });

    const payload = mockSubmit.mock.calls[0][0];
    expect(payload.counterparty_name).toBe('Al Noor Trading FZE');
    expect(payload.counterparty_account).toBe('AE07 0331 2345 6789 0123 456');
  });
});
