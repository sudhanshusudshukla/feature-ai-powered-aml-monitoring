/**
 * CaseStatusTag component - displays case workflow status with Carbon tags
 * Maps case states to appropriate Carbon tag types per design spec
 */

import { Tag } from '@carbon/react';

interface CaseStatusTagProps {
  status: string;
  'data-testid'?: string;
}

/**
 * Map case status to Carbon Tag type
 * Follows design spec in §2.2 Case status mapping
 */
function getTagType(status: string): 'cool-gray' | 'blue' | 'teal' | 'purple' | 'magenta' | 'green' | 'red' | 'gray' {
  switch (status) {
    case 'OPEN':
      return 'cool-gray';
    case 'UNDER_INVESTIGATION':
      return 'blue';
    case 'INFORMATION_REQUESTED':
      return 'teal';
    case 'PENDING_DECISION':
      return 'purple';
    case 'ESCALATED':
      return 'magenta';
    case 'APPROVED':
      return 'green';
    case 'REJECTED':
      return 'red';
    case 'CLOSED':
      return 'gray';
    default:
      return 'gray';
  }
}

/**
 * Convert enum to sentence case for display
 */
function formatStatus(status: string): string {
  return status
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
}

export function CaseStatusTag({ status, 'data-testid': testId }: CaseStatusTagProps) {
  return (
    <Tag
      type={getTagType(status)}
      title={status}
      data-testid={testId}
    >
      {formatStatus(status)}
    </Tag>
  );
}
