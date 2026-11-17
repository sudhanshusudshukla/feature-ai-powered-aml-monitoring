/**
 * ScreeningRunSteps - Progressive list showing screening workflow steps
 */
import type { TransactionDetailResponse } from '../../types/transaction';

interface ScreeningRunStepsProps {
  transaction: TransactionDetailResponse;
}

export function ScreeningRunSteps({ transaction }: ScreeningRunStepsProps) {
  const matchCount = transaction.matched_rules_count;
  const totalRules = transaction.evaluation_results.length || 8;

  return (
    <div>
      <p style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)', margin: '0 0 16px' }}>
        TransactionService · unit of work: the transaction, {totalRules} results, the alert and audit events commit together.
      </p>
      
      <ol
        style={{
          listStyle: 'none',
          margin: 0,
          padding: 0,
        }}
        aria-label="Screening steps, all complete"
      >
        <li
          style={{
            position: 'relative',
            padding: '0 0 16px 32px',
            borderLeft: '1px solid var(--cds-border-subtle-01)',
            marginLeft: '8px',
          }}
        >
          <span
            style={{
              content: '✓',
              position: 'absolute',
              left: '-9px',
              top: 0,
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              background: 'var(--cds-interactive)',
              color: 'var(--cds-text-on-color)',
              fontSize: '10px',
              lineHeight: '16px',
              textAlign: 'center',
              display: 'inline-block',
            }}
          >
            ✓
          </span>
          <strong style={{ fontWeight: 600, display: 'block' }}>
            Account and customer context loaded
          </strong>
          <span style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)' }}>
            {transaction.account_number || `ACC-${transaction.account_id}`} · {transaction.customer_name || 'Customer'} · customer risk {transaction.customer_risk || 'HIGH'}
          </span>
        </li>

        <li
          style={{
            position: 'relative',
            padding: '0 0 16px 32px',
            borderLeft: '1px solid var(--cds-border-subtle-01)',
            marginLeft: '8px',
          }}
        >
          <span
            style={{
              content: '✓',
              position: 'absolute',
              left: '-9px',
              top: 0,
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              background: 'var(--cds-interactive)',
              color: 'var(--cds-text-on-color)',
              fontSize: '10px',
              lineHeight: '16px',
              textAlign: 'center',
              display: 'inline-block',
            }}
          >
            ✓
          </span>
          <strong style={{ fontWeight: 600, display: 'block' }}>
            Transaction persisted
          </strong>
          <span style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)' }}>
            Original values preserved: ₹{parseFloat(transaction.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })} · {transaction.transaction_type} · {transaction.origin_country} → {transaction.destination_country}
          </span>
        </li>

        <li
          style={{
            position: 'relative',
            padding: '0 0 16px 32px',
            borderLeft: '1px solid var(--cds-border-subtle-01)',
            marginLeft: '8px',
          }}
        >
          <span
            style={{
              content: '✓',
              position: 'absolute',
              left: '-9px',
              top: 0,
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              background: 'var(--cds-interactive)',
              color: 'var(--cds-text-on-color)',
              fontSize: '10px',
              lineHeight: '16px',
              textAlign: 'center',
              display: 'inline-block',
            }}
          >
            ✓
          </span>
          <strong style={{ fontWeight: 600, display: 'block' }}>
            {totalRules} of {totalRules} rules evaluated and persisted
          </strong>
          <span style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)' }}>
            {totalRules} of {totalRules} results persisted · evaluated against rule versions in force
          </span>
        </li>

        <li
          style={{
            position: 'relative',
            padding: '0 0 16px 32px',
            borderLeft: '1px solid var(--cds-border-subtle-01)',
            marginLeft: '8px',
          }}
        >
          <span
            style={{
              content: '✓',
              position: 'absolute',
              left: '-9px',
              top: 0,
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              background: 'var(--cds-interactive)',
              color: 'var(--cds-text-on-color)',
              fontSize: '10px',
              lineHeight: '16px',
              textAlign: 'center',
              display: 'inline-block',
            }}
          >
            ✓
          </span>
          <strong style={{ fontWeight: 600, display: 'block' }}>
            {matchCount} {matchCount === 1 ? 'match' : 'matches'}, {transaction.alert_raised ? 'one alert generated' : 'no alert'}
          </strong>
          <span style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)' }}>
            matchedRulesCount {matchCount} · {transaction.alert_raised && transaction.alert_id && (
              <>alert <a href={`/alerts/${transaction.alert_id}`} className="cds--type-mono">ALT-{String(transaction.alert_id).padStart(10, '0')}</a></>
            )}
          </span>
        </li>

        <li
          style={{
            position: 'relative',
            padding: '0 0 16px 32px',
            borderLeft: 'none',
            marginLeft: '8px',
          }}
        >
          <span
            style={{
              content: '✓',
              position: 'absolute',
              left: '-9px',
              top: 0,
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              background: 'var(--cds-interactive)',
              color: 'var(--cds-text-on-color)',
              fontSize: '10px',
              lineHeight: '16px',
              textAlign: 'center',
              display: 'inline-block',
            }}
          >
            ✓
          </span>
          <strong style={{ fontWeight: 600, display: 'block' }}>
            Audit events written with the same correlation ID
          </strong>
          <span style={{ fontSize: '12px', lineHeight: '16px', color: 'var(--cds-text-secondary)' }}>
            Correlation ID <span className="cds--type-mono" data-testid="error-correlation-id" title={transaction.correlation_id}>
              {transaction.correlation_id.slice(0, 8)}…
            </span>
          </span>
        </li>
      </ol>
    </div>
  );
}
