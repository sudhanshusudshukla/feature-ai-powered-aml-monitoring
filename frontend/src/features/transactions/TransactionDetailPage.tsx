/**
 * TransactionDetailPage - View transaction screening details (wireframe 2)
 */
import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Grid,
  Column,
  Breadcrumb,
  BreadcrumbItem,
  Tile,
  Tag,
  SkeletonText,
  InlineNotification,
} from '@carbon/react';
import { TransactionOutcomeTag } from '../../components/status/TransactionOutcomeTag';
import { TransactionSummary } from '../../components/transactions/TransactionSummary';
import { ScreeningRunSteps } from '../../components/transactions/ScreeningRunSteps';
import { RuleResultTag } from '../../components/status/RuleResultTag';
import { transactionApi } from '../../lib/transaction-api';
import { ApiError } from '../../lib/api-client';
import type { TransactionDetailResponse } from '../../types/transaction';

export function TransactionDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [transaction, setTransaction] = useState<TransactionDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTransaction = async () => {
      if (!id) {
        setError('Transaction ID is required');
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const result = await transactionApi.getTransactionDetail(id);
        setTransaction(result);
      } catch (err) {
        if (err instanceof ApiError) {
          if (err.status === 404) {
            setError('Transaction not found');
          } else {
            setError(err.message);
          }
        } else {
          setError('An unexpected error occurred');
        }
      } finally {
        setLoading(false);
      }
    };

    loadTransaction();
  }, [id]);

  if (loading) {
    return (
      <div style={{ padding: '32px', maxWidth: '1184px' }}>
        <SkeletonText heading />
        <SkeletonText paragraph lineCount={3} />
        <SkeletonText paragraph lineCount={5} />
      </div>
    );
  }

  if (error === 'Transaction not found') {
    return (
      <div style={{ padding: '32px', maxWidth: '1184px' }}>
        <Tile style={{ textAlign: 'center', padding: '48px 24px' }}>
          <h3 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 16px' }}>
            Transaction not found
          </h3>
          <p style={{ color: 'var(--cds-text-secondary)', margin: '0 0 16px' }}>
            No transaction matches this ID.
          </p>
          <Link
            to="/transactions"
            style={{ color: 'var(--cds-link-primary)', textDecoration: 'none' }}
          >
            Back to transactions
          </Link>
        </Tile>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '32px', maxWidth: '1184px' }}>
        <InlineNotification
          kind="error"
          title="Something went wrong"
          subtitle={error}
          lowContrast
        />
      </div>
    );
  }

  if (!transaction) {
    return null;
  }

  const matchedRules = transaction.evaluation_results.filter((r) => r.outcome === 'MATCH');
  const passedRules = transaction.evaluation_results.filter((r) => r.outcome === 'PASS');

  return (
    <div style={{ padding: '32px', maxWidth: '1184px' }}>
      <Breadcrumb noTrailingSlash style={{ marginBottom: '16px' }}>
        <BreadcrumbItem>
          <Link to="/transactions" style={{ textDecoration: 'none', color: 'inherit' }}>
            Transactions
          </Link>
        </BreadcrumbItem>
        <BreadcrumbItem isCurrentPage>{transaction.transaction_reference}</BreadcrumbItem>
      </Breadcrumb>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', lineHeight: '36px', fontWeight: 400, margin: 0 }}>
          Transaction {transaction.transaction_reference}
        </h1>
        <TransactionOutcomeTag
          alertRaised={transaction.alert_raised}
          testId="transaction-outcome-tag"
        />
      </div>

      <p style={{ color: 'var(--cds-text-secondary)', margin: '0 0 24px' }}>
        Screened on receipt against {transaction.evaluation_results.length} rules. Results are historical and do not change when rule parameters change.
      </p>

      <TransactionSummary transaction={transaction} />

      <Grid fullWidth condensed style={{ padding: 0, margin: '24px 0 0' }}>
        <Column sm={4} md={6} lg={11} xlg={11}>
          <Tile style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 16px' }}>
              Screening run
            </h2>
            <ScreeningRunSteps transaction={transaction} />

            <h3 style={{ fontSize: '16px', lineHeight: '24px', fontWeight: 600, margin: '8px 0' }}>
              Result summary
            </h3>

            {matchedRules.length > 0 && (
              <p style={{ margin: '0 0 8px' }}>
                <RuleResultTag outcome="MATCH" />{' '}
                {matchedRules.map((r) => (
                  <span key={r.rule_code} className="cds--type-mono" style={{ marginRight: '8px' }}>
                    {r.rule_code}
                  </span>
                ))}
              </p>
            )}

            {passedRules.length > 0 && (
              <p style={{ margin: '0 0 8px' }}>
                <RuleResultTag outcome="PASS" />{' '}
                {passedRules.map((r) => (
                  <span key={r.rule_code} className="cds--type-mono" style={{ marginRight: '8px' }}>
                    {r.rule_code}
                  </span>
                ))}
              </p>
            )}

            <p style={{ margin: 0 }}>
              <Link
                to={`/alerts/${transaction.alert_id}`}
                style={{ color: 'var(--cds-link-primary)', textDecoration: 'none' }}
              >
                View all {transaction.evaluation_results.length} rule results with explanations
              </Link>
            </p>
          </Tile>
        </Column>

        <Column sm={4} md={2} lg={5} xlg={5}>
          <Tile>
            <h2 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 16px' }}>
              Account and customer context
            </h2>
            <p
              style={{
                fontSize: '12px',
                lineHeight: '16px',
                color: 'var(--cds-text-secondary)',
                margin: '0 0 16px',
              }}
            >
              AccountRepository · read before the rules ran
            </p>
            <dl
              style={{
                margin: 0,
                display: 'grid',
                gridTemplateColumns: '170px 1fr',
                borderTop: '1px solid var(--cds-border-subtle-01)',
              }}
            >
              <dt
                style={{
                  margin: 0,
                  padding: '8px 0',
                  borderBottom: '1px solid var(--cds-border-subtle-01)',
                  color: 'var(--cds-text-secondary)',
                  fontSize: '12px',
                  lineHeight: '20px',
                }}
              >
                Customer
              </dt>
              <dd
                style={{
                  margin: 0,
                  padding: '8px 0',
                  borderBottom: '1px solid var(--cds-border-subtle-01)',
                }}
              >
                {transaction.customer_name || 'N/A'}
              </dd>

              <dt
                style={{
                  margin: 0,
                  padding: '8px 0',
                  borderBottom: '1px solid var(--cds-border-subtle-01)',
                  color: 'var(--cds-text-secondary)',
                  fontSize: '12px',
                  lineHeight: '20px',
                }}
              >
                Customer risk
              </dt>
              <dd
                style={{
                  margin: 0,
                  padding: '8px 0',
                  borderBottom: '1px solid var(--cds-border-subtle-01)',
                }}
              >
                <Tag type="magenta">{transaction.customer_risk || 'HIGH'}</Tag>
              </dd>

              <dt
                style={{
                  margin: 0,
                  padding: '8px 0',
                  borderBottom: '1px solid var(--cds-border-subtle-01)',
                  color: 'var(--cds-text-secondary)',
                  fontSize: '12px',
                  lineHeight: '20px',
                }}
              >
                PEP
              </dt>
              <dd
                style={{
                  margin: 0,
                  padding: '8px 0',
                  borderBottom: '1px solid var(--cds-border-subtle-01)',
                }}
              >
                {transaction.pep_status ? 'Yes' : 'No'}
              </dd>

              <dt
                style={{
                  margin: 0,
                  padding: '8px 0',
                  borderBottom: '1px solid var(--cds-border-subtle-01)',
                  color: 'var(--cds-text-secondary)',
                  fontSize: '12px',
                  lineHeight: '20px',
                }}
              >
                Account
              </dt>
              <dd
                style={{
                  margin: 0,
                  padding: '8px 0',
                  borderBottom: '1px solid var(--cds-border-subtle-01)',
                }}
                className="cds--type-mono"
              >
                {transaction.account_number || `ACC-${transaction.account_id}`}
              </dd>

              <dt
                style={{
                  margin: 0,
                  padding: '8px 0',
                  borderBottom: '1px solid var(--cds-border-subtle-01)',
                  color: 'var(--cds-text-secondary)',
                  fontSize: '12px',
                  lineHeight: '20px',
                }}
              >
                Account status
              </dt>
              <dd
                style={{
                  margin: 0,
                  padding: '8px 0',
                  borderBottom: '1px solid var(--cds-border-subtle-01)',
                }}
              >
                {transaction.account_status || 'Active'} · INR
              </dd>
            </dl>

            <p
              style={{
                fontSize: '12px',
                lineHeight: '16px',
                color: 'var(--cds-text-secondary)',
                margin: '16px 0 0',
              }}
            >
              Synthetic data only. No external screening is performed.
            </p>
          </Tile>
        </Column>
      </Grid>
    </div>
  );
}
