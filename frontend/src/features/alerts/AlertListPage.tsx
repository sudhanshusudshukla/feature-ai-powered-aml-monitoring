/**
 * Alert list page placeholder
 * This is a minimal page to support navigation from alert detail breadcrumb
 */
import { Link } from 'react-router-dom';

export function AlertListPage() {
  return (
    <div style={{ padding: '32px' }}>
      <h1 style={{ fontSize: '28px', lineHeight: '36px', fontWeight: 400, margin: '0 0 24px' }}>
        Alerts
      </h1>
      <p>
        Alert list view will be implemented in a future task.
      </p>
      <p style={{ marginTop: '16px' }}>
        <Link to="/dashboard">Return to Dashboard</Link>
      </p>
    </div>
  );
}
