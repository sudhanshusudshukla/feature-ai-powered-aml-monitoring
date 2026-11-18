/**
 * Alert summary panel showing key alert details
 */
import { Tag } from '@carbon/react';
import { RiskScoreMeter } from '../status/RiskScoreMeter';
import type { AlertDetail } from '../../types/alert';

interface AlertSummaryProps {
  alert: AlertDetail;
}

export function AlertSummary({ alert }: AlertSummaryProps) {
  const statusTypeMap = {
    NEW: 'cool-gray',
    ASSIGNED: 'blue',
    UNDER_REVIEW: 'purple',
    CLOSED: 'gray',
  } as const;

  return (
    <div style={{ background: '#f4f4f4', padding: '24px' }}>
      <h2 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 16px' }}>
        Alert summary
      </h2>
      
      <RiskScoreMeter score={alert.risk_score} priority={alert.priority} />
      
      <dl style={{
        gridTemplateColumns: '200px 1fr',
        margin: '16px 0 0',
        display: 'grid',
        borderTop: '1px solid #c6c6c6'
      }}>
        <dt style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', color: '#525252' }}>
          Alert number
        </dt>
        <dd style={{
          margin: 0,
          padding: '8px 0',
          borderBottom: '1px solid #c6c6c6',
          fontFamily: 'IBM Plex Mono, monospace',
          textAlign: 'left'
        }}>
          {alert.alert_number}
        </dd>
        
        <dt style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', color: '#525252' }}>
          Alert ID
        </dt>
        <dd style={{
          margin: 0,
          padding: '8px 0',
          borderBottom: '1px solid #c6c6c6',
          fontFamily: 'IBM Plex Mono, monospace',
          textAlign: 'left'
        }}>
          {alert.id}
        </dd>
        
        <dt style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', color: '#525252' }}>
          Status
        </dt>
        <dd style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', textAlign: 'left' }}>
          <Tag type={statusTypeMap[alert.status as keyof typeof statusTypeMap] || 'gray'}>
            {alert.status}
          </Tag>
        </dd>
        
        <dt style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', color: '#525252' }}>
          Created
        </dt>
        <dd style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', textAlign: 'left' }}>
          {new Date(alert.created_at).toLocaleString('en-GB', {
            day: '2-digit',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          })}
        </dd>
        
        <dt style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', color: '#525252' }}>
          Transaction
        </dt>
        <dd style={{ margin: 0, padding: '8px 0', borderBottom: '1px solid #c6c6c6', textAlign: 'left' }}>
          <a
            href={`/transactions/${alert.transaction_id}`}
            style={{ fontFamily: 'IBM Plex Mono, monospace' }}
          >
            {alert.transaction.transaction_reference}
          </a>
        </dd>
      </dl>
    </div>
  );
}
