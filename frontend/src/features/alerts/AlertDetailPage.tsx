/**
 * Alert detail page showing complete alert information, matched rules,
 * risk score breakdown, transaction summary, and customer snapshot
 */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Grid, Column, Loading, InlineNotification } from '@carbon/react';
import { getAlertDetail } from '../../lib/alert-api';
import { ApiError } from '../../lib/api-client';
import { PriorityTag } from '../../components/status/PriorityTag';
import { SeverityTag } from '../../components/status/SeverityTag';
import { ExplanationCallout } from '../../components/rules/ExplanationCallout';
import { ScoreBreakdown } from '../../components/rules/ScoreBreakdown';
import { AlertSummary } from '../../components/alerts/AlertSummary';
import { CustomerSnapshot } from '../../components/customer/CustomerSnapshot';
import { AuditTimeline } from '../../components/audit/AuditTimeline';
import type { AlertDetail, RuleEvaluationSummary } from '../../types/alert';

export default function AlertDetailPage() {
  const { alertId } = useParams<{ alertId: string }>();
  const [alert, setAlert] = useState<AlertDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!alertId) return;

    const fetchAlert = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getAlertDetail(parseInt(alertId, 10));
        setAlert(data);
      } catch (err) {
        if (err instanceof ApiError) {
          if (err.status === 404) {
            setError('Alert not found');
          } else if (err.status === 401) {
            setError('Authentication required');
          } else if (err.status === 403) {
            setError('You do not have permission to view this alert');
          } else {
            setError(err.message || 'Failed to load alert');
          }
        } else {
          setError('An unexpected error occurred');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchAlert();
  }, [alertId]);

  if (loading) {
    return (
      <div style={{ padding: '32px' }}>
        <Loading description="Loading alert..." withOverlay={false} />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '32px' }}>
        <InlineNotification
          kind="error"
          title="Error loading alert"
          subtitle={error}
          lowContrast
        />
      </div>
    );
  }

  if (!alert) {
    return (
      <div style={{ padding: '32px' }}>
        <InlineNotification
          kind="info"
          title="Alert not found"
          subtitle="No alert matches this ID"
          lowContrast
        />
      </div>
    );
  }

  // Determine if PEP floor was applied
  const pepApplied = alert.customer_snapshot.pep_status || alert.customer_snapshot.sanctioned_status;

  return (
    <div style={{ padding: '32px' }}>
      {/* Breadcrumb */}
      <div style={{ fontSize: '12px', lineHeight: '16px', color: '#525252', marginBottom: '16px' }}>
        <Link to="/alerts">Alerts</Link>
        <span style={{ margin: '0 4px' }}>/</span>
        {alert.alert_number}
      </div>

      {/* Page title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', lineHeight: '36px', fontWeight: 400, margin: 0 }}>
          Alert {alert.alert_number}
        </h1>
        <PriorityTag priority={alert.priority} data-testid="priority-tag" />
        <span style={{
          display: 'inline-flex',
          alignItems: 'center',
          height: '24px',
          padding: '0 8px',
          borderRadius: '24px',
          fontSize: '12px',
          lineHeight: '16px',
          background: '#dde1e6',
          color: '#121619'
        }}>
          {alert.status}
        </span>
      </div>

      {/* Description */}
      <p style={{ color: '#525252', marginBottom: '24px' }}>
        Raised {new Date(alert.created_at).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })},{' '}
        {new Date(alert.created_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })} · Customer: {alert.customer_snapshot.full_name} · Risk score {alert.risk_score} · One alert for{' '}
        {alert.matched_rules.length} matched rules on{' '}
        <Link
          to={`/transactions/${alert.transaction_id}`}
          style={{ fontFamily: 'IBM Plex Mono, monospace' }}
        >
          {alert.transaction.transaction_reference}
        </Link>
      </p>

      <Grid fullWidth narrow>
        {/* Main content column */}
        <Column lg={11} md={8} sm={4}>
          {/* Matched rules */}
          <section aria-labelledby="matched-rules-heading">
            <h2 id="matched-rules-heading" style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 16px' }}>
              Matched rules
            </h2>
            {alert.matched_rules.map((rule: RuleEvaluationSummary) => (
              <ExplanationCallout key={rule.rule_code} rule={rule} />
            ))}
          </section>

          {/* Rule results table placeholder */}
          <section style={{ marginTop: '32px' }} aria-labelledby="rule-results-heading">
            <h2 id="rule-results-heading" style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 8px' }}>
              Rule results
            </h2>
            <p style={{ fontSize: '12px', lineHeight: '16px', color: '#525252', margin: '0 0 8px' }}>
              <strong style={{ color: '#161616' }}>{alert.matched_rules.length} of 8 rules matched · score {alert.risk_score}</strong> · RuleEvaluationEngine · all results are always shown
            </p>
            <div style={{
              background: '#f4f4f4',
              border: '1px solid #c6c6c6',
              padding: '16px'
            }}>
              {alert.matched_rules.map((rule: RuleEvaluationSummary) => (
                <div
                  key={rule.rule_code}
                  data-testid={`rule-result-${rule.rule_code}`}
                  style={{
                    padding: '8px 0',
                    borderBottom: '1px solid #c6c6c6',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <span style={{ fontWeight: 600, fontFamily: 'IBM Plex Mono, monospace' }}>
                      {rule.rule_code}
                    </span>
                    <span>{rule.rule_name}</span>
                    <SeverityTag severity={rule.severity as 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'} />
                    <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#525252' }}>
                      Score: {rule.score}
                    </span>
                  </div>
                  <p style={{ margin: '4px 0 0', fontSize: '14px', color: '#525252' }}>
                    {rule.explanation}
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* Alert summary */}
          <section style={{ marginTop: '32px' }}>
            <AlertSummary alert={alert} />
          </section>

          {/* Audit timeline */}
          <AuditTimeline correlationId={alert.transaction.transaction_reference} />
        </Column>

        {/* Sidebar column */}
        <Column lg={5} md={8} sm={4}>
          {/* Priority rationale */}
          <ScoreBreakdown
            baseScore={alert.base_score}
            customerRiskAdjustment={alert.customer_risk_adjustment}
            geographyAdjustment={alert.geography_adjustment}
            finalScore={alert.risk_score}
            priority={alert.priority}
            priorityRationale={alert.priority_rationale}
            pepApplied={pepApplied}
          />

          {/* Customer snapshot */}
          <CustomerSnapshot customer={alert.customer_snapshot} />
        </Column>
      </Grid>
    </div>
  );
}
