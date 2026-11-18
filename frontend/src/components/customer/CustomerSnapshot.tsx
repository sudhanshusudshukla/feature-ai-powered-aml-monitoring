/**
 * Customer snapshot panel for alert detail
 */
import { Tag } from '@carbon/react';
import type { CustomerSnapshotData } from '../../types/alert';

interface CustomerSnapshotProps {
  customer: CustomerSnapshotData;
}

export function CustomerSnapshot({ customer }: CustomerSnapshotProps) {
  const riskTypeMap = {
    VERY_HIGH: 'red',
    HIGH: 'magenta',
    MEDIUM: 'warm-gray',
    LOW: 'gray',
  } as const;

  return (
    <div style={{
      background: '#ffffff',
      padding: '16px',
      border: '1px solid #c6c6c6',
      marginTop: '16px'
    }}>
      <h3 style={{ fontSize: '16px', lineHeight: '24px', fontWeight: 600, margin: '0 0 8px' }}>
        Customer
      </h3>
      <p style={{ margin: '0 0 4px' }}>
        {customer.full_name} · <span style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{customer.customer_number}</span>
      </p>
      <p style={{ margin: '0 0 8px' }}>
        <Tag type={riskTypeMap[customer.risk_level as keyof typeof riskTypeMap] || 'gray'}>
          {customer.risk_level}
        </Tag>{' '}
        <span style={{ fontSize: '12px', lineHeight: '16px', color: '#525252' }}>
          PEP: {customer.pep_status ? 'Yes' : 'No'} · Sanctioned: {customer.sanctioned_status ? 'Yes' : 'No'}
        </span>
      </p>
      <p style={{ fontSize: '12px', lineHeight: '16px', color: '#525252', margin: 0 }}>
        Account <span style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{customer.account_number}</span> · {customer.account_status}
      </p>
    </div>
  );
}
