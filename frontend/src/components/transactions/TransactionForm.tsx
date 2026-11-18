/**
 * TransactionForm - Form for submitting transactions for screening
 */
import { useState, FormEvent } from 'react';
import {
  Form,
  FormGroup,
  TextInput,
  Select,
  SelectItem,
  Button,
  Stack,
  InlineNotification,
} from '@carbon/react';
import type { TransactionIngestRequest } from '../../types/transaction';

interface TransactionFormProps {
  onSubmit: (data: TransactionIngestRequest) => Promise<void>;
  loading: boolean;
  error: string | null;
}

const ACCOUNTS = [
  { id: 1, number: 'ACC-001-001', name: 'Rajesh Kumar' },
  { id: 2, number: 'ACC-002-001', name: 'Sarah Johnson' },
  { id: 3, number: 'ACC-003-001', name: 'Ahmed Hassan' },
  { id: 4, number: 'ACC-004-001', name: 'Maria Garcia' },
];

export function TransactionForm({ onSubmit, loading, error }: TransactionFormProps) {
  const [formData, setFormData] = useState({
    transaction_reference: `TXN-2026-${String(Math.floor(Math.random() * 999999)).padStart(6, '0')}`,
    account_id: '1',
    amount: '850000.00',
    currency: 'INR',
    transaction_type: 'TRANSFER',
    origin_country: 'IN',
    destination_country: 'AE',
    counterparty_name: 'Al Noor Trading FZE',
    counterparty_account: 'AE07 0331 2345 6789 0123 456',
    timestamp: new Date().toISOString().slice(0, 16),
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (validationErrors[field]) {
      setValidationErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    
    if (!formData.transaction_reference.trim()) {
      errors.transaction_reference = 'Transaction reference is required';
    }
    if (!formData.account_id) {
      errors.account_id = 'Account is required';
    }
    if (!formData.amount.trim()) {
      errors.amount = 'Amount is required';
    }
    if (!formData.transaction_type) {
      errors.transaction_type = 'Transaction type is required';
    }
    if (!formData.origin_country) {
      errors.origin_country = 'Origin country is required';
    }
    if (!formData.destination_country) {
      errors.destination_country = 'Destination country is required';
    }
    if (!formData.timestamp) {
      errors.timestamp = 'Timestamp is required';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    const payload: TransactionIngestRequest = {
      transaction_reference: formData.transaction_reference,
      account_id: parseInt(formData.account_id, 10),
      amount: formData.amount,
      currency: formData.currency,
      transaction_type: formData.transaction_type as TransactionIngestRequest['transaction_type'],
      origin_country: formData.origin_country,
      destination_country: formData.destination_country,
      counterparty_name: formData.counterparty_name || undefined,
      counterparty_account: formData.counterparty_account || undefined,
      timestamp: new Date(formData.timestamp).toISOString(),
    };

    await onSubmit(payload);
  };

  const handleReset = () => {
    setFormData({
      transaction_reference: `TXN-2026-${String(Math.floor(Math.random() * 999999)).padStart(6, '0')}`,
      account_id: '1',
      amount: '850000.00',
      currency: 'INR',
      transaction_type: 'TRANSFER',
      origin_country: 'IN',
      destination_country: 'AE',
      counterparty_name: 'Al Noor Trading FZE',
      counterparty_account: 'AE07 0331 2345 6789 0123 456',
      timestamp: new Date().toISOString().slice(0, 16),
    });
    setValidationErrors({});
  };

  return (
    <Form onSubmit={handleSubmit}>
      {error && Object.keys(validationErrors).length > 0 && (
        <InlineNotification
          kind="error"
          title={`Fix ${Object.keys(validationErrors).length} field${Object.keys(validationErrors).length > 1 ? 's' : ''} to continue`}
          subtitle={Object.values(validationErrors).join('. ')}
          lowContrast
        />
      )}
      
      {error && Object.keys(validationErrors).length === 0 && (
        <InlineNotification
          kind="error"
          title="Submission failed"
          subtitle={error}
          lowContrast
        />
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 288px)', columnGap: '24px' }}>
        <FormGroup legendText="">
          <TextInput
            id="ref"
            labelText="Transaction reference (required)"
            value={formData.transaction_reference}
            onChange={(e) => handleChange('transaction_reference', e.target.value)}
            invalid={!!validationErrors.transaction_reference}
            invalidText={validationErrors.transaction_reference}
            helperText="Duplicate references are not yet defined (D-05)."
            disabled={loading}
          />
        </FormGroup>

        <FormGroup legendText="">
          <Select
            id="acc"
            labelText="Account (required)"
            value={formData.account_id}
            onChange={(e) => handleChange('account_id', e.target.value)}
            invalid={!!validationErrors.account_id}
            invalidText={validationErrors.account_id}
            helperText="Account ID is sent as a UUID (5b1e7c90…)."
            disabled={loading}
          >
            {ACCOUNTS.map((account) => (
              <SelectItem
                key={account.id}
                value={String(account.id)}
                text={`${account.number} · ${account.name}`}
              />
            ))}
          </Select>
        </FormGroup>

        <FormGroup legendText="">
          <TextInput
            id="amt"
            labelText="Amount (required)"
            value={formData.amount}
            onChange={(e) => handleChange('amount', e.target.value)}
            invalid={!!validationErrors.amount}
            invalidText={validationErrors.amount}
            helperText="Exact decimal, for example 850000.00"
            disabled={loading}
          />
        </FormGroup>

        <FormGroup legendText="">
          <Select
            id="cur"
            labelText="Currency"
            value={formData.currency}
            onChange={(e) => handleChange('currency', e.target.value)}
            helperText="All amounts are INR."
            disabled={loading}
          >
            <SelectItem value="INR" text="INR" />
          </Select>
        </FormGroup>

        <FormGroup legendText="">
          <Select
            id="typ"
            labelText="Transaction type (required)"
            value={formData.transaction_type}
            onChange={(e) => handleChange('transaction_type', e.target.value)}
            invalid={!!validationErrors.transaction_type}
            invalidText={validationErrors.transaction_type}
            disabled={loading}
          >
            <SelectItem value="TRANSFER" text="TRANSFER" />
            <SelectItem value="DEPOSIT" text="DEPOSIT" />
            <SelectItem value="WITHDRAWAL" text="WITHDRAWAL" />
            <SelectItem value="PAYMENT" text="PAYMENT" />
          </Select>
        </FormGroup>

        <FormGroup legendText="">
          <TextInput
            id="ts"
            type="datetime-local"
            labelText="Timestamp (required)"
            value={formData.timestamp}
            onChange={(e) => handleChange('timestamp', e.target.value)}
            invalid={!!validationErrors.timestamp}
            invalidText={validationErrors.timestamp}
            helperText="Date picker with time. Stored as UTC."
            disabled={loading}
          />
        </FormGroup>

        <FormGroup legendText="">
          <Select
            id="org"
            labelText="Origin country (required)"
            value={formData.origin_country}
            onChange={(e) => handleChange('origin_country', e.target.value)}
            invalid={!!validationErrors.origin_country}
            invalidText={validationErrors.origin_country}
            disabled={loading}
          >
            <SelectItem value="IN" text="IN · India" />
            <SelectItem value="US" text="US · United States" />
            <SelectItem value="AE" text="AE · United Arab Emirates" />
            <SelectItem value="GB" text="GB · United Kingdom" />
          </Select>
        </FormGroup>

        <FormGroup legendText="">
          <Select
            id="dst"
            labelText="Destination country (required)"
            value={formData.destination_country}
            onChange={(e) => handleChange('destination_country', e.target.value)}
            invalid={!!validationErrors.destination_country}
            invalidText={validationErrors.destination_country}
            disabled={loading}
          >
            <SelectItem value="AE" text="AE · United Arab Emirates" />
            <SelectItem value="IN" text="IN · India" />
            <SelectItem value="US" text="US · United States" />
            <SelectItem value="GB" text="GB · United Kingdom" />
          </Select>
        </FormGroup>

        <FormGroup legendText="">
          <TextInput
            id="cpn"
            labelText="Counterparty name"
            value={formData.counterparty_name}
            onChange={(e) => handleChange('counterparty_name', e.target.value)}
            disabled={loading}
          />
        </FormGroup>

        <FormGroup legendText="">
          <TextInput
            id="cpa"
            labelText="Counterparty account"
            value={formData.counterparty_account}
            onChange={(e) => handleChange('counterparty_account', e.target.value)}
            disabled={loading}
          />
        </FormGroup>
      </div>

      <Stack gap={4} orientation="horizontal" style={{ marginTop: '16px' }}>
        <Button type="submit" disabled={loading}>
          {loading ? 'Screening transaction…' : 'Submit for screening'}
        </Button>
        <Button kind="ghost" type="button" onClick={handleReset} disabled={loading}>
          Clear form
        </Button>
      </Stack>
    </Form>
  );
}
