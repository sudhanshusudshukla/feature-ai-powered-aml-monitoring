/**
 * LinkedAlertsPanel component
 * Displays linked alerts table for case workspace
 * Follows design spec from wireframe_06
 */

import {
  DataTable,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
} from '@carbon/react';
import { Link } from 'react-router-dom';
import { AlertSummary } from '../../types/case';
import { PriorityTag } from '../status/PriorityTag';

interface LinkedAlertsPanelProps {
  alerts: AlertSummary[];
}

const headers = [
  { key: 'alert_number', header: 'Alert' },
  { key: 'priority', header: 'Priority' },
  { key: 'risk_score', header: 'Risk score' },
  { key: 'transaction_id', header: 'Transaction' },
  { key: 'status', header: 'Status' },
];

export function LinkedAlertsPanel({ alerts }: LinkedAlertsPanelProps) {
  const rows = alerts.map(alert => ({
    id: String(alert.id),
    alert_number: alert.alert_number,
    priority: alert.priority,
    risk_score: alert.risk_score,
    transaction_id: alert.transaction_id,
    status: alert.status,
  }));

  return (
    <div style={{ marginBottom: '24px' }}>
      <h2 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 400, margin: '0 0 16px' }}>
        Linked alerts
      </h2>
      <DataTable rows={rows} headers={headers} size="lg">
        {({ rows, headers, getTableProps, getHeaderProps, getRowProps }) => (
          <Table {...getTableProps()} aria-label="Linked alerts">
            <TableHead>
              <TableRow>
                {headers.map(header => (
                  <TableHeader
                    {...getHeaderProps({ header })}
                    key={header.key}
                    className={header.key === 'risk_score' ? 'num' : ''}
                  >
                    {header.header}
                  </TableHeader>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map(row => {
                const alert = alerts.find(a => String(a.id) === row.id);
                if (!alert) return null;

                return (
                  <TableRow {...getRowProps({ row })} key={row.id}>
                    <TableCell>
                      <Link
                        to={`/alerts/${alert.id}`}
                        style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '14px' }}
                      >
                        {alert.alert_number}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <PriorityTag priority={alert.priority as 'HIGH' | 'LOW' | 'MEDIUM' | 'CRITICAL'} />
                    </TableCell>
                    <TableCell className="num">{alert.risk_score}</TableCell>
                    <TableCell>
                      <Link
                        to={`/transactions/${alert.transaction_id}`}
                        style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: '14px' }}
                      >
                        TXN-{String(alert.transaction_id).padStart(10, '0')}
                      </Link>
                    </TableCell>
                    <TableCell>{alert.status}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </DataTable>
    </div>
  );
}
