/**
 * CaseWorkspacePage component
 * Main case investigation workspace matching wireframe_06 and wireframe_07
 */

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Grid, Column, Button, Breadcrumb, BreadcrumbItem, InlineLoading, InlineNotification } from '@carbon/react';
import { CaseDetailResponse } from '../../types/case';
import { apiClient, getCurrentUser } from '../../lib/api-client';
import { CaseStatusTag } from '../../components/status/CaseStatusTag';
import { PriorityTag } from '../../components/status/PriorityTag';
import { LinkedAlertsPanel } from '../../components/cases/LinkedAlertsPanel';
import { InformationRequestCard } from '../../components/investigation/InformationRequestCard';
import { RequestInfoDialog } from '../../components/investigation/RequestInfoDialog';
import { RecordResponseDialog } from '../../components/investigation/RecordResponseDialog';
import { NotesThread } from '../../components/investigation/NotesThread';
import { AuditTimeline } from '../../components/audit/AuditTimeline';
import { DecisionPanel } from '../../components/cases/DecisionPanel';
import { DecisionDialog } from '../../components/cases/DecisionDialog';
import { PermissionNotice } from '../../components/cases/PermissionNotice';
import { DecisionAction } from '../../lib/decision-actions';

export function CaseWorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const [caseData, setCaseData] = useState<CaseDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [requestInfoOpen, setRequestInfoOpen] = useState(false);
  const [recordResponseOpen, setRecordResponseOpen] = useState(false);
  const [decisionDialogOpen, setDecisionDialogOpen] = useState(false);
  const [selectedAction, setSelectedAction] = useState<DecisionAction | null>(null);
  const [isSubmittingDecision, setIsSubmittingDecision] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [decisionSuccess, setDecisionSuccess] = useState<string | null>(null);

  const loadCase = async () => {
    if (!id) return;
    
    try {
      setLoading(true);
      const data = await apiClient.get<CaseDetailResponse>(`/v1/cases/${id}`);
      setCaseData(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load case');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCase();
  }, [id]);

  const handleRequestInfo = async (data: { requested_what: string; reason: string; due_date: string }) => {
    if (!id) return;
    await apiClient.post(`/v1/cases/${id}/request-info`, data);
    await loadCase(); // Refresh case data
  };

  const handleRecordResponse = async (data: { response_text: string; evidence_reference?: string }) => {
    if (!id || !caseData) return;
    
    // Find the open request
    const openRequest = caseData.information_requests.find(r => r.status === 'OPEN');
    if (!openRequest) return;

    await apiClient.post(`/v1/cases/${id}/information-requests/${openRequest.id}/respond`, data);
    await loadCase(); // Refresh case data
  };

  const handleAddNote = async (noteText: string) => {
    if (!id) return;
    await apiClient.post(`/v1/cases/${id}/notes`, { note_text: noteText });
    await loadCase(); // Refresh case data
  };

  const handleDecisionClick = (action: DecisionAction) => {
    setSelectedAction(action);
    setDecisionDialogOpen(true);
    setDecisionError(null);
    setDecisionSuccess(null);
  };

  const handleDecisionSubmit = async (data: {
    decision: DecisionAction;
    reason?: string;
    comments?: string;
  }) => {
    if (!id || !caseData) return;

    try {
      setIsSubmittingDecision(true);
      setDecisionError(null);

      await apiClient.post(`/v1/cases/${id}/decision`, {
        decision: data.decision,
        reason: data.reason,
        comments: data.comments,
        expected_version: caseData.version,
      });

      setDecisionSuccess(`Case ${data.decision.toLowerCase()}d`);
      setDecisionDialogOpen(false);
      setSelectedAction(null);
      await loadCase(); // Refresh case data
    } catch (err) {
      if (err instanceof Error) {
        // Handle specific error codes
        if (err.message.includes('INVALID_CASE_STATE')) {
          setDecisionError(
            'This case changed since you opened it. The page has been refreshed.'
          );
          await loadCase();
          setDecisionDialogOpen(false);
        } else if (err.message.includes('STALE_OBJECT')) {
          setDecisionError(
            'Someone else updated this case. The page has been refreshed.'
          );
          await loadCase();
          setDecisionDialogOpen(false);
        } else {
          setDecisionError(err.message);
        }
      }
    } finally {
      setIsSubmittingDecision(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '32px' }}>
        <InlineLoading description="Loading case..." />
      </div>
    );
  }

  if (error || !caseData) {
    return (
      <div style={{ padding: '32px' }}>
        <div style={{ textAlign: 'center', padding: '24px', background: 'var(--cds-layer-01)' }}>
          <div style={{ fontSize: '20px', fontWeight: 400, margin: '0 0 8px' }}>
            Case not found
          </div>
          <p style={{ fontSize: '12px', color: 'var(--cds-text-secondary)', margin: '0 0 16px' }}>
            No case matches this ID.
          </p>
          <Link to="/cases">Back to cases</Link>
        </div>
      </div>
    );
  }

  // Find open information request
  const openRequest = caseData.information_requests.find(
    r => r.status === 'OPEN' || r.status === 'OVERDUE'
  );

  // Check if user can record response (placeholder - needs real permission check)
  const canRecordResponse = caseData.permitted_actions.includes('RECORD_RESPONSE');
  const canAddNote = caseData.permitted_actions.includes('ADD_NOTE') || true; // Default allow
  const canRequestInfo = caseData.permitted_actions.includes('REQUEST_INFO');

  // Check for decision blocking conditions
  const hasOpenRequest = !!openRequest;
  const currentUser = getCurrentUser();
  const isCreator = currentUser ? currentUser.id === caseData.created_by_user_id : false;

  // Determine if decisions are blocked
  const isDecisionBlocked = hasOpenRequest;
  const blockReason = hasOpenRequest
    ? 'Decisions are unavailable until the information request is responded to.'
    : undefined;

  // Terminal states
  const isTerminal = ['APPROVED', 'REJECTED', 'CLOSED'].includes(caseData.state);
  
  // Show decision panel if there are any decision-related actions available
  const hasAnyDecisionActions = caseData.permitted_actions.some(action => 
    ['APPROVE', 'REJECT', 'ESCALATE', 'REQUEST_INFO', 'CLOSE_FALSE_POSITIVE'].includes(action)
  );

  return (
    <div style={{ padding: '32px' }}>
      <Breadcrumb>
        <BreadcrumbItem>
          <Link to="/cases">Cases</Link>
        </BreadcrumbItem>
        <BreadcrumbItem isCurrentPage>{caseData.case_number}</BreadcrumbItem>
      </Breadcrumb>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginTop: '16px', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', lineHeight: '36px', fontWeight: 400, margin: 0 }}>
          Case {caseData.case_number}
        </h1>
        <PriorityTag priority={caseData.priority as 'HIGH' | 'LOW' | 'MEDIUM' | 'CRITICAL'} data-testid="priority-tag" />
        <CaseStatusTag status={caseData.state} data-testid="case-status-tag" />
      </div>

      <p style={{ color: 'var(--cds-text-secondary)', marginBottom: '24px' }}>
        Customer: {caseData.customer_id} · Created {new Date(caseData.created_at).toLocaleDateString()} by User {caseData.created_by_user_id} · {caseData.linked_alerts.length} {caseData.linked_alerts.length !== 1 ? 'alerts' : 'alert'} linked
        {caseData.assigned_to_user_id && ` · Assigned to User ${caseData.assigned_to_user_id}`}
      </p>

      {decisionSuccess && (
        <InlineNotification
          kind="success"
          title={decisionSuccess}
          subtitle="The decision is recorded in the audit trail."
          onClose={() => setDecisionSuccess(null)}
          style={{ marginBottom: '16px' }}
        />
      )}

      {decisionError && (
        <InlineNotification
          kind="error"
          title="Decision failed"
          subtitle={decisionError}
          onClose={() => setDecisionError(null)}
          style={{ marginBottom: '16px' }}
        />
      )}

      <Grid narrow>
        <Column lg={11} style={{ paddingRight: '16px' }}>
          <LinkedAlertsPanel alerts={caseData.linked_alerts} />

          {openRequest && (
            <div style={{ marginTop: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: 0 }}>
                  Information request
                </h2>
                {canRequestInfo && (
                  <Button
                    kind="secondary"
                    size="sm"
                    onClick={() => setRequestInfoOpen(true)}
                  >
                    Request information
                  </Button>
                )}
              </div>
              <InformationRequestCard
                request={openRequest}
                onRecordResponse={() => setRecordResponseOpen(true)}
                canRecordResponse={canRecordResponse}
              />
            </div>
          )}

          <NotesThread
            notes={caseData.notes}
            onAddNote={handleAddNote}
            canAddNote={canAddNote}
          />

          <AuditTimeline correlationId={`case-${caseData.id}`} />
        </Column>

        <Column lg={5} style={{ paddingLeft: '16px' }}>
          {isTerminal ? (
            <div
              style={{
                background: 'var(--cds-layer-01)',
                padding: '16px',
                position: 'sticky',
                top: '64px',
              }}
            >
              <h2 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 16px' }}>
                Decision
              </h2>
              <PermissionNotice
                message="This case has a final decision. No further decision actions are available."
                type="info"
              />
            </div>
          ) : isCreator ? (
            <div
              style={{
                background: 'var(--cds-layer-01)',
                padding: '16px',
                position: 'sticky',
                top: '64px',
              }}
            >
              <h2 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 16px' }}>
                Decision
              </h2>
              <PermissionNotice
                message="You cannot decide this case because you created it (separation of duties)."
                type="warning"
              />
            </div>
          ) : hasAnyDecisionActions ? (
            <DecisionPanel
              permittedActions={caseData.permitted_actions}
              onDecisionClick={handleDecisionClick}
              isBlocked={isDecisionBlocked}
              blockReason={blockReason}
            />
          ) : (
            <div
              style={{
                background: 'var(--cds-layer-01)',
                padding: '16px',
                position: 'sticky',
                top: '64px',
              }}
            >
              <h2 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 16px' }}>
                Decision
              </h2>
              <PermissionNotice
                message="No decision actions are available for your role."
                type="info"
              />
            </div>
          )}
        </Column>
      </Grid>

      <RequestInfoDialog
        open={requestInfoOpen}
        onClose={() => setRequestInfoOpen(false)}
        onSubmit={handleRequestInfo}
      />

      <RecordResponseDialog
        open={recordResponseOpen}
        onClose={() => setRecordResponseOpen(false)}
        onSubmit={handleRecordResponse}
      />

      <DecisionDialog
        open={decisionDialogOpen}
        action={selectedAction}
        onClose={() => {
          setDecisionDialogOpen(false);
          setSelectedAction(null);
          setDecisionError(null);
        }}
        onSubmit={handleDecisionSubmit}
        isSubmitting={isSubmittingDecision}
      />
    </div>
  );
}
