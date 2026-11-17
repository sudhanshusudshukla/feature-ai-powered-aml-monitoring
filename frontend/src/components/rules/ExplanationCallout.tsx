/**
 * Rule explanation callout component for matched rules
 * Uses InlineNotification pattern for HIGH→error, MEDIUM→warning
 */
import { InlineNotification } from '@carbon/react';
import type { RuleEvaluationSummary } from '../../types/alert';

interface ExplanationCalloutProps {
  rule: RuleEvaluationSummary;
}

export function ExplanationCallout({ rule }: ExplanationCalloutProps) {
  // Map severity to notification kind: HIGH/CRITICAL→error, MEDIUM→warning
  const kind = rule.severity === 'HIGH' || rule.severity === 'CRITICAL' ? 'error' : 'warning';

  return (
    <InlineNotification
      kind={kind}
      lowContrast
      hideCloseButton
      title={`${rule.rule_code} ${rule.rule_name} · ${rule.severity}`}
      subtitle={rule.explanation}
      style={{ marginBottom: '8px' }}
      data-testid={`explanation-${rule.rule_code}`}
    />
  );
}
