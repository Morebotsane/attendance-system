import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { ProtectedRoute } from './components/layout/ProtectedRoute';
import { ToastContainer } from './components/common/Toast';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { CheckInPage } from './pages/CheckInPage';
import { EmployeesPage } from './pages/EmployeesPage';
import { DepartmentsPage } from './pages/DepartmentsPage';
import { ReportsPage } from './pages/ReportsPage';
import { AdminPage } from './pages/AdminPage';
import { KioskPage } from './pages/KioskPage';
import { detectDevice } from './utils/helpers';
import { useAuthStore } from './store/authStore';

// ─── Smart root redirect ───────────────────────────────────────────────────────
// Phone  → /login (employee check-in flow)
// Tablet → /kiosk (ministry kiosk display)
// Desktop → /login (admin/manager/employee portal)
function RootRedirect() {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuthStore();

  useEffect(() => {
    const device = detectDevice();

    if (device === 'tablet') {
      // Tablets go straight to kiosk
      navigate('/kiosk', { replace: true });
      return;
    }

    if (isAuthenticated && user) {
      // Already logged in — send to correct destination
      if (device === 'phone') {
        navigate('/check-in', { replace: true });
      } else {
        // Desktop — role-based
        const dest = user.role === 'employee' ? '/check-in' : '/dashboard';
        navigate(dest, { replace: true });
      }
      return;
    }

    // Not authenticated — go to login
    navigate('/login', { replace: true });
  }, [navigate, isAuthenticated, user]);

  // Brief loading while detecting
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f0f2f7]">
      <div className="w-8 h-8 border-4 border-[#002395]/20 border-t-[#002395] rounded-full animate-spin" />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* ── Smart root redirect ── */}
        <Route path="/" element={<RootRedirect />} />

        {/* ── Public routes ── */}
        <Route path="/login" element={<LoginPage />} />

        {/* ── Kiosk — PIN protected internally ── */}
        <Route path="/kiosk" element={<KioskPage />} />

        {/* ── Authenticated routes ── */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/check-in"  element={<CheckInPage />} />

            {/* Admin + Manager only */}
            <Route element={<ProtectedRoute roles={['admin', 'manager']} />}>
              <Route path="/employees"   element={<EmployeesPage />} />
              <Route path="/departments" element={<DepartmentsPage />} />
              <Route path="/reports"     element={<ReportsPage />} />
            </Route>

            {/* Admin only */}
            <Route element={<ProtectedRoute roles={['admin']} />}>
              <Route path="/admin" element={<AdminPage />} />
            </Route>
          </Route>
        </Route>

        {/* ── Catch all ── */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>

      <ToastContainer />
    </BrowserRouter>
  );
}
