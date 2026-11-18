/**
 * RulesPage component with DataTable
 */
import { useState, useEffect } from 'react';
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

interface RuleListItem {
  id: number;
  rule_code: string;
  name: string;
  severity: string;
  description: string;
  is_active: boolean;
  version: number;
}

export default function RulesPage() {
  const [rules, setRules] = useState<RuleListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const fetchRules = async () => {
      try {
        setLoading(true);
        // TODO: Replace with actual API call
        // const response = await fetch(`/api/v1/rules?page=${page}&page_size=${pageSize}`);
        // const data = await response.json();
        // setRules(data.items);
        // setTotal(data.total);
        setRules([]);
        setTotal(0);
      } catch (error) {
        console.error('Failed to fetch rules:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRules();
  }, [page, pageSize]);

  const headers = [
    { key: 'rule_code', header: 'Code' },
    { key: 'name', header: 'Name' },
    { key: 'severity', header: 'Severity' },
    { key: 'is_active', header: 'Status' },
    { key: 'version', header: 'Version' },
  ];

  const getSeverityTagType = (severity: string) => {
    switch (severity) {
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
        <Loading description="Loading rules..." withOverlay={false} />
      </div>
    );
  }

  return (
    <div style={{ padding: '32px' }}>
      <h1 style={{ fontSize: '28px', lineHeight: '36px', fontWeight: 400, margin: '0 0 24px' }}>
        Detection Rules
      </h1>

      <DataTable rows={rules.map(r => ({ ...r, id: String(r.id) }))} headers={headers}>
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
                        {cell.info.header === 'severity' ? (
                          <Tag type={getSeverityTagType(cell.value as string)}>
                            {cell.value}
                          </Tag>
                        ) : cell.info.header === 'is_active' ? (
                          <Tag type={cell.value ? 'green' : 'gray'}>
                            {cell.value ? 'Active' : 'Inactive'}
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
