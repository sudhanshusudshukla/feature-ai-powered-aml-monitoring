/**
 * Severity badge/tag component for rule results
 */
import { Tag } from '@carbon/react';

interface SeverityTagProps {
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
}

export function SeverityTag({ severity }: SeverityTagProps) {
  const typeMap = {
    CRITICAL: 'red',
    HIGH: 'magenta',
    MEDIUM: 'warm-gray',
    LOW: 'gray',
  } as const;

  return <Tag type={typeMap[severity]}>{severity}</Tag>;
}
