/**
 * Alert list page with DataTable
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  DataTable,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  Pagination,
  Loading,
  Tag,
} from '@carbon/react';

interface AlertListItem {
  id: number;
  alert_number: string;
  customer_name: string;
  risk_score: number;
  priority: string;
  status: string;
  created_at: string;
}

export function AlertListPage() {
  const [alerts, setAlerts] = useState<AlertListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true);
        // TODO: Replace with actual API call
        // const response = await fetch(`/api/v1/alerts?page=${page}&page_size=${pageSize}`);
        // const data = await response.json();
        // setAlerts(data.items);
        // setTotal(data.total);
        setAlerts([]);
        setTotal(0);
      } catch (error) {
        console.error('Failed to fetch alerts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
  }, [page, pageSize]);

  const headers = [
    { key: 'alert_number', header: 'Alert Number' },
    { key: 'customer_name', header: 'Customer' },
    { key: 'risk_score', header: 'Risk Score' },
    { key: 'priority', header: 'Priority' },
    { key: 'status', header: 'Status' },
    { key: 'created_at', header: 'Created' },
  ];

  const getPriorityTagType = (priority: string) => {
    switch (priority) {
      case 'CRITICAL':
        return 'red';
      case 'HIGH':
        return 'magenta';
      case 'MEDIUM':
        return 'purple';
      case 'LOW':
        return 'cyan';
      default:
        return 'gray';
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '32px' }}>
        <Loading description="Loading alerts..." withOverlay={false} />
      </div>
    );
  }

  return (
    <div style={{ padding: '32px' }}>
      <h1 style={{ fontSize: '28px', lineHeight: '36px', fontWeight: 400, margin: '0 0 24px' }}>
        Alerts
      </h1>

      <DataTable rows={alerts.map(a => ({ ...a, id: String(a.id) }))} headers={headers}>
        {({ rows, headers, getHeaderProps, getTableProps }) => (
          <>
            <Table {...getTableProps()}>
              <TableHead>
                <TableRow>
                  {headers.map((header) => (
                    <TableHeader {...getHeaderProps({ header })} key={header.key}>
                      {header.header}
                    </TableHeader>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((row) => (
                  <TableRow key={row.id}>
                    {row.cells.map((cell) => (
                      <TableCell key={cell.id}>
                        {cell.info.header === 'alert_number' ? (
                          <Link to={`/alerts/${row.id}`}>{cell.value}</Link>
                        ) : cell.info.header === 'priority' ? (
                          <Tag type={getPriorityTagType(cell.value as string)}>
                            {cell.value}
                          </Tag>
                        ) : (
                          cell.value
                        )}
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            <Pagination
              page={page}
              pageSize={pageSize}
              pageSizes={[10, 20, 50, 100]}
              totalItems={total}
              onChange={({ page, pageSize }) => {
                setPage(page);
                setPageSize(pageSize);
              }}
            />
          </>
        )}
      </DataTable>
    </div>
  );
}
