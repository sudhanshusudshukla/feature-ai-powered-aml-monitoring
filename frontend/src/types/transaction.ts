/**
 * Transaction-related type definitions
 */

export interface TransactionIngestRequest {
  transaction_reference: string;
  account_id: number;
  amount: string;
  currency?: string;
  transaction_type: 'TRANSFER' | 'DEPOSIT' | 'WITHDRAWAL' | 'PAYMENT';
  origin_country: string;
  destination_country: string;
  counterparty_name?: string;
  counterparty_account?: string;
  timestamp: string;
}

export interface RuleEvaluationItem {
  rule_code: string;
  rule_name: string;
  rule_version: number;
  outcome: 'PASS' | 'MATCH';
  severity: string;
  score: number;
  explanation: string;
  evidence_snapshot: Record<string, unknown>;
}

export interface TransactionIngestResponse {
  id: number;
  transaction_reference: string;
  account_id: number;
  amount: string;
  currency: string;
  transaction_type: string;
  origin_country: string;
  destination_country: string;
  counterparty_name?: string;
  counterparty_account?: string;
  timestamp: string;
  matched_rules_count: number;
  alert_raised: boolean;
  alert_id: number | null;
  correlation_id: string;
  evaluation_results: RuleEvaluationItem[];
}

export interface TransactionDetailResponse {
  id: number;
  transaction_reference: string;
  account_id: number;
  amount: string;
  currency: string;
  transaction_type: string;
  origin_country: string;
  destination_country: string;
  counterparty_name?: string;
  counterparty_account?: string;
  timestamp: string;
  matched_rules_count: number;
  alert_raised: boolean;
  alert_id: number | null;
  correlation_id: string;
  evaluation_results: RuleEvaluationItem[];
  account_number?: string;
  customer_name?: string;
  customer_risk?: string;
  pep_status?: boolean;
  account_status?: string;
}
