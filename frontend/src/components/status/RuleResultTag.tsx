/**
 * RuleResultTag - Tag showing rule evaluation outcome
 */
import { Tag } from '@carbon/react';

interface RuleResultTagProps {
  outcome: 'PASS' | 'MATCH';
}

export function RuleResultTag({ outcome }: RuleResultTagProps) {
  return (
    <Tag type={outcome === 'MATCH' ? 'red' : 'gray'}>
      {outcome}
    </Tag>
  );
}
