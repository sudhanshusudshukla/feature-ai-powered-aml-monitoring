/**
 * TransactionOutcomeTag - Tag showing transaction screening outcome
 */
import { Tag } from '@carbon/react';

interface TransactionOutcomeTagProps {
  alertRaised: boolean;
  testId?: string;
}

export function TransactionOutcomeTag({ alertRaised, testId }: TransactionOutcomeTagProps) {
  return (
    <Tag
      type={alertRaised ? 'red' : 'gray'}
      data-testid={testId}
    >
      {alertRaised ? 'Flagged' : 'Clear'}
    </Tag>
  );
}
