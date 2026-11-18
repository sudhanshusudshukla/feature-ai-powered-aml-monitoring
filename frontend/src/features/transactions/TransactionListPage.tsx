/**
 * Transaction list page with DataTable
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
  Button,
  Loading,
} from '@carbon/react';
import { Add } from '@carbon/icons-react';

interface TransactionListItem {
  id: number;
  transaction_reference: string;
  customer_name: string;
  amount: string;
  currency: string;
  transaction_type: string;
  timestamp: string;
  alert_raised: boolean;
}

export function TransactionListPage() {
  const [transactions, setTransactions] = useState<TransactionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        setLoading(true);
        // TODO: Replace with actual API call
        // const response = await fetch(`/api/v1/transactions?page=${page}&page_size=${pageSize}`);
        // const data = await response.json();
        // setTransactions(data.items);
        // setTotal(data.total);
        setTransactions([]);
        setTotal(0);
      } catch (error) {
        console.error('Failed to fetch transactions:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTransactions();
  }, [page, pageSize]);

  const headers = [
    { key: 'transaction_reference', header: 'Reference' },
    { key: 'customer_name', header: 'Customer' },
    { key: 'amount', header: 'Amount' },
    { key: 'transaction_type', header: 'Type' },
    { key: 'timestamp', header: 'Date' },
    { key: 'alert_raised', header: 'Alert' },
  ];

  if (loading) {
    return (
      <div style={{ padding: '32px' }}>
        <Loading description="Loading transactions..." withOverlay={false} />
      </div>
    );
  }

  return (
    <div style={{ padding: '32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', lineHeight: '36px', fontWeight: 400, margin: 0 }}>
          Transactions
        </h1>
        <Button
          renderIcon={Add}
          as={Link}
          to="/transactions/new"
        >
          New transaction
        </Button>
      </div>

      <DataTable rows={transactions.map(t => ({ ...t, id: String(t.id) }))} headers={headers}>
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
                        {cell.info.header === 'transaction_reference' ? (
                          <Link to={`/transactions/${row.id}`}>{cell.value}</Link>
                        ) : cell.info.header === 'alert_raised' ? (
                          cell.value ? 'Yes' : 'No'
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
