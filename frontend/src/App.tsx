/**
 * Main App component with routing
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './lib/auth-context';
import { LoginPage } from './components/auth/LoginPage';
import { RequireAuth } from './components/auth/RequireAuth';
import { Layout } from './components/layout/Layout';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { TransactionListPage } from './features/transactions/TransactionListPage';
import { TransactionSubmitPage } from './features/transactions/TransactionSubmitPage';
import { TransactionDetailPage } from './features/transactions/TransactionDetailPage';
import AlertDetailPage from './features/alerts/AlertDetailPage';
import { AlertListPage } from './features/alerts/AlertListPage';
import { CaseWorkspacePage } from './features/cases/CaseWorkspacePage';
import { CaseListPage } from './features/cases/CaseListPage';
import RulesPage from './features/rules/RulesPage';
import AdminPage from './features/admin/AdminPage';

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          
          <Route
            path="/dashboard"
            element={
              <RequireAuth>
                <Layout>
                  <DashboardPage />
                </Layout>
              </RequireAuth>
            }
          />

          <Route
            path="/transactions"
            element={
              <RequireAuth>
                <Layout>
                  <TransactionListPage />
                </Layout>
              </RequireAuth>
            }
          />

          <Route
            path="/transactions/new"
            element={
              <RequireAuth>
                <Layout>
                  <TransactionSubmitPage />
                </Layout>
              </RequireAuth>
            }
          />

          <Route
            path="/transactions/:id"
            element={
              <RequireAuth>
                <Layout>
                  <TransactionDetailPage />
                </Layout>
              </RequireAuth>
            }
          />

          <Route
            path="/alerts"
            element={
              <RequireAuth>
                <Layout>
                  <AlertListPage />
                </Layout>
              </RequireAuth>
            }
          />

          <Route
            path="/alerts/:alertId"
            element={
              <RequireAuth>
                <Layout>
                  <AlertDetailPage />
                </Layout>
              </RequireAuth>
            }
          />

          <Route
            path="/cases"
            element={
              <RequireAuth>
                <Layout>
                  <CaseListPage />
                </Layout>
              </RequireAuth>
            }
          />

          <Route
            path="/cases/:id"
            element={
              <RequireAuth>
                <Layout>
                  <CaseWorkspacePage />
                </Layout>
              </RequireAuth>
            }
          />

          <Route
            path="/rules"
            element={
              <RequireAuth>
                <Layout>
                  <RulesPage />
                </Layout>
              </RequireAuth>
            }
          />

          <Route
            path="/admin"
            element={
              <RequireAuth>
                <Layout>
                  <AdminPage />
                </Layout>
              </RequireAuth>
            }
          />

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
