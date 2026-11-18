/**
 * TypeScript interfaces for case management
 * Maps to backend case schemas
 */

export interface AlertSummary {
  id: number;
  alert_number: string;
  transaction_id: number;
  risk_score: number;
  priority: string;
  status: string;
}

export interface NoteSummary {
  id: number;
  note_text: string;
  created_by_user_id: number;
  created_at: string;
}

export interface DecisionSummary {
  id: number;
  decision: string;
  reason: string | null;
  comments: string | null;
  decided_by_user_id: number;
  decided_at: string;
}

export interface InformationRequestSummary {
  id: number;
  requested_what: string;
  reason: string;
  due_date: string;
  status: string;
  requested_by_user_id: number;
  created_at: string;
}

export interface CaseDetailResponse {
  id: number;
  case_number: string;
  title: string;
  customer_id: number;
  state: string;
  priority: string;
  created_by_user_id: number;
  assigned_to_user_id: number | null;
  closure_reason: string | null;
  created_at: string;
  updated_at: string;
  version: number;
  linked_alerts: AlertSummary[];
  notes: NoteSummary[];
  decisions: DecisionSummary[];
  information_requests: InformationRequestSummary[];
  permitted_actions: string[];
}

export interface CaseCreateRequest {
  title: string;
  alert_ids: number[];
}

export interface RequestInfoRequest {
  requested_what: string;
  reason: string;
  due_date: string;
}

export interface RecordResponseRequest {
  response_text: string;
  evidence_reference?: string;
}
