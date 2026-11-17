/**
 * TransactionSubmitPage - Submit transaction for screening (wireframe 1)
 */
import { useState } from 'react';
import {
  Grid,
  Column,
  Breadcrumb,
  BreadcrumbItem,
  Tag,
  ToastNotification,
  Tile,
  Link as CarbonLink,
  TextInput,
} from '@carbon/react';
import { TransactionForm } from '../../components/transactions/TransactionForm';
import { RuleResultList } from '../../components/rules/RuleResultList';
import { transactionApi } from '../../lib/transaction-api';
import { ApiError } from '../../lib/api-client';
import type {
  TransactionIngestRequest,
  TransactionIngestResponse,
} from '../../types/transaction';
import { Link } from 'react-router-dom';

export function TransactionSubmitPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<TransactionIngestResponse | null>(null);
  const [showToast, setShowToast] = useState(false);

  const handleSubmit = async (data: TransactionIngestRequest) => {
    setLoading(true);
    setError(null);
    setShowToast(false);

    try {
      const result = await transactionApi.submitTransaction(data);
      setResponse(result);
      setShowToast(true);
      setError(null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
      setResponse(null);
      setShowToast(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '32px', maxWidth: '1184px' }}>
      {showToast && response && (
        <div
          style={{
            position: 'fixed',
            top: '80px',
            right: '32px',
            zIndex: 9000,
          }}
        >
          <ToastNotification
            kind="success"
            title="Transaction received and screened"
            subtitle={`${response.transaction_reference} · ${response.matched_rules_count} of ${response.evaluation_results.length} rules matched${response.alert_raised ? ` · alert ALT-${String(response.alert_id).padStart(10, '0')} raised` : ''}.`}
            timeout={5000}
            onClose={() => setShowToast(false)}
          />
        </div>
      )}

      <Breadcrumb noTrailingSlash style={{ marginBottom: '16px' }}>
        <BreadcrumbItem>
          <Link to="/transactions" style={{ textDecoration: 'none', color: 'inherit' }}>
            Transactions
          </Link>
        </BreadcrumbItem>
        <BreadcrumbItem isCurrentPage>New</BreadcrumbItem>
      </Breadcrumb>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', lineHeight: '36px', fontWeight: 400, margin: 0 }}>
          Submit transaction
        </h1>
        <Tag type="gray">Synthetic data only</Tag>
      </div>

      <p style={{ color: 'var(--cds-text-secondary)', margin: '0 0 24px' }}>
        Send a synthetic transaction for screening. The amount is stored exactly as entered. No currency conversion is applied.
      </p>

      <Grid fullWidth condensed style={{ padding: 0, margin: 0 }}>
        <Column sm={4} md={6} lg={11} xlg={11}>
          <Tile style={{ padding: '24px' }}>
            <h2 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 16px' }}>
              Transaction details
            </h2>
            <TransactionForm onSubmit={handleSubmit} loading={loading} error={error} />
          </Tile>
        </Column>

        <Column sm={4} md={2} lg={5} xlg={5}>
          <Tile>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h2 style={{ margin: 0, fontSize: '20px', lineHeight: '28px', fontWeight: 400 }}>
                Ingest response
              </h2>
              {response && (
                <Tag type="green">HTTP 201</Tag>
              )}
            </div>

            {response && (
              <>
                <dl
                  style={{
                    margin: 0,
                    display: 'grid',
                    gridTemplateColumns: '150px 1fr',
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
                    id
                  </dt>
                  <dd
                    style={{
                      margin: 0,
                      padding: '8px 0',
                      borderBottom: '1px solid var(--cds-border-subtle-01)',
                    }}
                    className="cds--type-mono"
                  >
                    {response.id}
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
                    transactionReference
                  </dt>
                  <dd
                    style={{
                      margin: 0,
                      padding: '8px 0',
                      borderBottom: '1px solid var(--cds-border-subtle-01)',
                    }}
                    className="cds--type-mono"
                  >
                    {response.transaction_reference}
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
                    matchedRulesCount
                  </dt>
                  <dd
                    style={{
                      margin: 0,
                      padding: '8px 0',
                      borderBottom: '1px solid var(--cds-border-subtle-01)',
                    }}
                    className="cds--type-mono"
                  >
                    {response.matched_rules_count}
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
                    alertRaised
                  </dt>
                  <dd
                    style={{
                      margin: 0,
                      padding: '8px 0',
                      borderBottom: '1px solid var(--cds-border-subtle-01)',
                    }}
                  >
                    {response.alert_raised ? (
                      <>
                        <Tag type="red" style={{ marginRight: '8px' }}>Flagged</Tag>
                        <span className="cds--type-mono">true</span>
                      </>
                    ) : (
                      <>
                        <Tag type="gray" style={{ marginRight: '8px' }}>Clear</Tag>
                        <span className="cds--type-mono">false</span>
                      </>
                    )}
                  </dd>

                  {response.alert_id && (
                    <>
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
                        alertId
                      </dt>
                      <dd
                        style={{
                          margin: 0,
                          padding: '8px 0',
                          borderBottom: '1px solid var(--cds-border-subtle-01)',
                        }}
                      >
                        <CarbonLink href={`/alerts/${response.alert_id}`} className="cds--type-mono">
                          ALT-{String(response.alert_id).padStart(10, '0')}
                        </CarbonLink>
                      </dd>
                    </>
                  )}

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
                    correlationId
                  </dt>
                  <dd
                    style={{
                      margin: 0,
                      padding: '8px 0',
                      borderBottom: '1px solid var(--cds-border-subtle-01)',
                    }}
                    className="cds--type-mono"
                    data-testid="error-correlation-id"
                    title={response.correlation_id}
                  >
                    {response.correlation_id.slice(0, 8)}…
                  </dd>
                </dl>

                <p
                  style={{
                    fontSize: '12px',
                    lineHeight: '16px',
                    color: 'var(--cds-text-secondary)',
                    margin: '16px 0 8px',
                  }}
                >
                  evaluationResults: {response.evaluation_results.length} returned
                </p>

                <RuleResultList results={response.evaluation_results} />

                <p style={{ margin: '16px 0 0' }}>
                  <Link
                    to={`/transactions/${response.id}`}
                    style={{ color: 'var(--cds-link-primary)', textDecoration: 'none' }}
                  >
                    View transaction details
                  </Link>
                </p>
              </>
            )}

            {!response && (
              <p style={{ color: 'var(--cds-text-secondary)', margin: 0 }}>
                Submit a transaction to see the response
              </p>
            )}
          </Tile>
        </Column>

        <Column sm={4} md={8} lg={16} xlg={16}>
          <Tile style={{ marginTop: '24px' }}>
            <h2 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 16px' }}>
              Look up transaction
            </h2>
            <TextInput
              id="lk"
              labelText="Transaction ID"
              className="cds--type-mono"
              style={{ maxWidth: '480px', marginBottom: '8px' }}
              placeholder="Enter transaction ID"
              helperText="Reads GET /api/v1/transactions/{id}."
            />
          </Tile>
        </Column>
      </Grid>
    </div>
  );
}
