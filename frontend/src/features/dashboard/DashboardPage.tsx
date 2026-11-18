/**
 * Dashboard page with KPIs and charts
 */
import { useState, useEffect } from 'react';
import { Tile, Loading } from '@carbon/react';
import { Grid, Column } from '@carbon/react';

interface KPICounts {
  total_alerts: number;
  new_alerts: number;
  open_cases: number;
  high_priority_alerts: number;
  transactions_today: number;
  rules_active: number;
}

export function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [kpis, setKpis] = useState<KPICounts | null>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        // TODO: Replace with actual API call
        // const response = await fetch('/api/v1/dashboard/summary');
        // const data = await response.json();
        // setKpis(data.kpis);
        setKpis({
          total_alerts: 0,
          new_alerts: 0,
          open_cases: 0,
          high_priority_alerts: 0,
          transactions_today: 0,
          rules_active: 0,
        });
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div style={{ padding: '32px' }}>
        <Loading description="Loading dashboard..." withOverlay={false} />
      </div>
    );
  }

  return (
    <div style={{ padding: '32px' }}>
      <h1 style={{ fontSize: '28px', lineHeight: '36px', fontWeight: 400, margin: '0 0 24px' }}>
        Dashboard
      </h1>
      <p style={{ color: 'var(--cds-text-secondary)', marginBottom: '24px' }}>
        Welcome to the AML Transaction Monitoring Platform
      </p>

      <Grid fullWidth narrow>
        <Column sm={4} md={4} lg={4}>
          <Tile>
            <h3 style={{ fontSize: '14px', fontWeight: 400, margin: '0 0 8px' }}>Total Alerts</h3>
            <p style={{ fontSize: '32px', lineHeight: '40px', fontWeight: 300, margin: 0 }}>
              {kpis?.total_alerts || 0}
            </p>
          </Tile>
        </Column>
        <Column sm={4} md={4} lg={4}>
          <Tile>
            <h3 style={{ fontSize: '14px', fontWeight: 400, margin: '0 0 8px' }}>New Alerts</h3>
            <p style={{ fontSize: '32px', lineHeight: '40px', fontWeight: 300, margin: 0 }}>
              {kpis?.new_alerts || 0}
            </p>
          </Tile>
        </Column>
        <Column sm={4} md={4} lg={4}>
          <Tile>
            <h3 style={{ fontSize: '14px', fontWeight: 400, margin: '0 0 8px' }}>Open Cases</h3>
            <p style={{ fontSize: '32px', lineHeight: '40px', fontWeight: 300, margin: 0 }}>
              {kpis?.open_cases || 0}
            </p>
          </Tile>
        </Column>
      </Grid>
    </div>
  );
}
