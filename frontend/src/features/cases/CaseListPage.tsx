/**
 * CaseListPage component with DataTable
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

interface CaseListItem {
  id: number;
  case_number: string;
  title: string;
  customer_name: string;
  state: string;
  priority: string;
  created_at: string;
  alert_count: number;
}

export function CaseListPage() {
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const fetchCases = async () => {
      try {
        setLoading(true);
        // TODO: Replace with actual API call
        // const response = await fetch(`/api/v1/cases?page=${page}&page_size=${pageSize}`);
        // const data = await response.json();
        // setCases(data.items);
        // setTotal(data.total);
        setCases([]);
        setTotal(0);
      } catch (error) {
        console.error('Failed to fetch cases:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCases();
  }, [page, pageSize]);

  const headers = [
    { key: 'case_number', header: 'Case Number' },
    { key: 'title', header: 'Title' },
    { key: 'customer_name', header: 'Customer' },
    { key: 'state', header: 'State' },
    { key: 'priority', header: 'Priority' },
    { key: 'alert_count', header: 'Alerts' },
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
        <Loading description="Loading cases..." withOverlay={false} />
      </div>
    );
  }

  return (
    <div style={{ padding: '32px' }}>
      <h1 style={{ fontSize: '28px', lineHeight: '36px', fontWeight: 400, margin: '0 0 24px' }}>
        Cases
      </h1>

      <DataTable rows={cases} headers={headers}>
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
                        {cell.info.header === 'case_number' ? (
                          <Link to={`/cases/${row.id}`}>{cell.value}</Link>
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
