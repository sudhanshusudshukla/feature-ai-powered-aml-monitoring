/**
 * Priority badge/tag component for alerts
 */
import { Tag } from '@carbon/react';

interface PriorityTagProps {
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  'data-testid'?: string;
}

export function PriorityTag({ priority, 'data-testid': testId }: PriorityTagProps) {
  const typeMap = {
    CRITICAL: 'red',
    HIGH: 'magenta',
    MEDIUM: 'warm-gray',
    LOW: 'gray',
  } as const;

  return (
    <Tag type={typeMap[priority]} data-testid={testId}>
      {priority}
    </Tag>
  );
}
