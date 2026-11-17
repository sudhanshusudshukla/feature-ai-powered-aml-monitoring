/**
 * Tests for ExplanationCallout component
 */
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ExplanationCallout } from '../ExplanationCallout';
import type { RuleEvaluationSummary } from '../../../types/alert';

describe('ExplanationCallout', () => {
  const mockHighSeverityRule: RuleEvaluationSummary = {
    rule_code: 'AML-001',
    rule_name: 'High Value Transaction',
    rule_version: 1,
    outcome: 'MATCH',
    severity: 'HIGH',
    score: 30,
    explanation: 'Transaction amount exceeds threshold',
    evidence_snapshot: {},
  };

  const mockMediumSeverityRule: RuleEvaluationSummary = {
    rule_code: 'AML-003',
    rule_name: 'Velocity Amount',
    rule_version: 1,
    outcome: 'MATCH',
    severity: 'MEDIUM',
    score: 16,
    explanation: 'Total exceeds velocity limit',
    evidence_snapshot: {},
  };

  it('renders HIGH severity rule as error notification', () => {
    render(<ExplanationCallout rule={mockHighSeverityRule} />);
    
    expect(screen.getByText(/AML-001 High Value Transaction/)).toBeInTheDocument();
    expect(screen.getByText(/Transaction amount exceeds threshold/)).toBeInTheDocument();
  });

  it('renders MEDIUM severity rule as warning notification', () => {
    render(<ExplanationCallout rule={mockMediumSeverityRule} />);
    
    expect(screen.getByText(/AML-003 Velocity Amount/)).toBeInTheDocument();
    expect(screen.getByText(/Total exceeds velocity limit/)).toBeInTheDocument();
  });

  it('includes rule code in data-testid', () => {
    const { container } = render(<ExplanationCallout rule={mockHighSeverityRule} />);
    const notification = container.querySelector('[data-testid="explanation-AML-001"]');
    expect(notification).toBeInTheDocument();
  });

  it('displays severity level in title', () => {
    render(<ExplanationCallout rule={mockHighSeverityRule} />);
    expect(screen.getByText(/HIGH/)).toBeInTheDocument();
  });
});
