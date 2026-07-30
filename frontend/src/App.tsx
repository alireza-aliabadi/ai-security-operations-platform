import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { useAuth } from '@/lib/auth'
import { ApprovalsPage } from '@/pages/ApprovalsPage'
import { ChatPage } from '@/pages/ChatPage'
import { ConnectorsPage } from '@/pages/ConnectorsPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { InvestigationDetailPage } from '@/pages/InvestigationDetailPage'
import { InvestigationsPage } from '@/pages/InvestigationsPage'
import { LoginPage } from '@/pages/LoginPage'
import { ReportsPage } from '@/pages/ReportsPage'

function ProtectedRoute() {
  const { isAuthenticated } = useAuth()
  const location = useLocation()
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  return <Outlet />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="investigations" element={<InvestigationsPage />} />
          <Route path="investigations/:id" element={<InvestigationDetailPage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="connectors" element={<ConnectorsPage />} />
          <Route path="approvals" element={<ApprovalsPage />} />
          <Route path="reports" element={<ReportsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
