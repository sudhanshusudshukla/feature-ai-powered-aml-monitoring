/**
 * Audit timeline component placeholder
 * Full audit integration deferred to later tasks
 */

interface AuditTimelineProps {
  correlationId: string;
}

export function AuditTimeline({ correlationId }: AuditTimelineProps) {
  return (
    <div style={{ marginTop: '32px', paddingTop: '24px', borderTop: '1px solid #c6c6c6' }}>
      <h2 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 16px' }}>
        Audit timeline
      </h2>
      <p style={{ fontSize: '12px', lineHeight: '16px', color: '#525252' }}>
        Correlation ID: <span style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{correlationId}</span>
      </p>
      <p style={{ color: '#525252', margin: '8px 0 0' }}>
        Audit event display deferred to administration phase.
      </p>
    </div>
  );
}
