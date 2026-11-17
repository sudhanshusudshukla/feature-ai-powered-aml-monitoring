/**
 * TransactionSummary - Key-value grid of transaction summary information
 */
import { Tag } from '@carbon/react';
import type { TransactionDetailResponse } from '../../types/transaction';

interface TransactionSummaryProps {
  transaction: TransactionDetailResponse;
}

export function TransactionSummary({ transaction }: TransactionSummaryProps) {
  const formatAmount = (amount: string, currency: string) => {
    const num = parseFloat(amount);
    return `₹${num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatDate = (iso: string) => {
    const date = new Date(iso);
    return date.toLocaleString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <dl
      className="cds--tile"
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '16px',
        padding: '16px',
        margin: 0,
      }}
      aria-label="Transaction summary"
    >
      <div>
        <dt style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)' }}>
          Amount
        </dt>
        <dd style={{ margin: 0, fontWeight: 600 }} className="cds--type-mono">
          {formatAmount(transaction.amount, transaction.currency)}
        </dd>
      </div>

      <div>
        <dt style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)' }}>
          Date
        </dt>
        <dd style={{ margin: 0, fontWeight: 600 }} title={transaction.timestamp}>
          {formatDate(transaction.timestamp)}
        </dd>
      </div>

      <div>
        <dt style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)' }}>
          From account
        </dt>
        <dd style={{ margin: 0, fontWeight: 600 }} className="cds--type-mono">
          {transaction.account_number || `ACC-${String(transaction.account_id).padStart(3, '0')}-001`}
        </dd>
      </div>

      <div>
        <dt style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)' }}>
          To account (counterparty)
        </dt>
        <dd style={{ margin: 0, fontWeight: 600 }}>
          {transaction.counterparty_name || 'N/A'}
          {transaction.counterparty_account && (
            <>
              <br />
              <span className="cds--type-mono" style={{ fontWeight: 400 }}>
                {transaction.counterparty_account}
              </span>
            </>
          )}
        </dd>
      </div>

      <div>
        <dt style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)' }}>
          Countries
        </dt>
        <dd style={{ margin: 0, fontWeight: 600 }}>
          🌐 {transaction.origin_country} → {transaction.destination_country} · United Arab Emirates
        </dd>
      </div>

      <div>
        <dt style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)' }}>
          Customer risk
        </dt>
        <dd style={{ margin: 0, fontWeight: 600 }}>
          <Tag type="magenta">{transaction.customer_risk || 'HIGH'}</Tag>
        </dd>
      </div>

      <div>
        <dt style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)' }}>
          PEP customer
        </dt>
        <dd style={{ margin: 0, fontWeight: 600 }}>
          {transaction.pep_status ? 'Yes' : 'No'}
        </dd>
      </div>

      <div>
        <dt style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)' }}>
          Linked alert
        </dt>
        <dd style={{ margin: 0, fontWeight: 600 }}>
          {transaction.alert_id ? (
            <a href={`/alerts/${transaction.alert_id}`} className="cds--type-mono">
              ALT-{String(transaction.alert_id).padStart(10, '0')}
            </a>
          ) : (
            'None'
          )}
        </dd>
      </div>
    </dl>
  );
}
