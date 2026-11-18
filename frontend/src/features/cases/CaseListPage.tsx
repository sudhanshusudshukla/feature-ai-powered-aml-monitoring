/**
 * CaseListPage component
 * List view of all cases
 */

import { Link } from 'react-router-dom';

export function CaseListPage() {
  return (
    <div style={{ padding: '32px' }}>
      <h1 style={{ fontSize: '28px', lineHeight: '36px', fontWeight: 400, margin: '0 0 24px' }}>
        Cases
      </h1>
      <p style={{ color: 'var(--cds-text-secondary)', marginBottom: '24px' }}>
        Case management workspace (implementation pending)
      </p>
      <div style={{ background: 'var(--cds-layer-01)', padding: '24px' }}>
        <p style={{ margin: 0 }}>
          Case list functionality to be implemented. For now, navigate directly to a case workspace using its ID.
        </p>
      </div>
    </div>
  );
}
