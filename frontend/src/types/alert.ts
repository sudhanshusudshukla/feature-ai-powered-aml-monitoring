/**
 * Alert-related type definitions
 */

export interface RuleEvaluationSummary {
  rule_code: string;
  rule_name: string;
  rule_version: number;
  outcome: 'PASS' | 'MATCH';
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  score: number;
  explanation: string;
  evidence_snapshot: Record<string, unknown>;
}

export interface TransactionSummary {
  id: number;
  transaction_reference: string;
  amount: string;
  currency: string;
  transaction_type: string;
  origin_country: string;
  destination_country: string;
  timestamp: string;
}

export interface CustomerSnapshotData {
  customer_id: number;
  customer_number: string;
  full_name: string;
  residency_country: string;
  pep_status: boolean;
  sanctioned_status: boolean;
  risk_level: string;
  account_number: string;
  account_status: string;
}

export interface AlertDetail {
  id: number;
  alert_number: string;
  transaction_id: number;
  risk_score: number;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: string;
  created_at: string;
  priority_rationale: string;
  assigned_to_user_id: number | null;
  base_score: number;
  customer_risk_adjustment: number;
  geography_adjustment: number;
  transaction: TransactionSummary;
  matched_rules: RuleEvaluationSummary[];
  customer_snapshot: CustomerSnapshotData;
}
