import type { ReactElement } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { useAuthStore } from '../store/authStore';
import { adminApi } from '../api/admin';
import { attendanceApi } from '../api/attendance';
import { reportsApi } from '../api/reports';
import { StatusBadge, Avatar } from '../components/common/Badges';
import { StatCardSkeleton } from '../components/common/Loading';
import { formatTime, formatDate } from '../utils/helpers';

function StatCard({ label, value, sub, color, icon }: {
  label: string; value: string | number; sub?: string;
  color: string; icon: ReactElement;
}) {
  return (
    <div className="card p-5 flex items-start gap-4 animate-slide-up">
      <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0"
        style={{ backgroundColor: color + '15' }}>
        <div style={{ color }}>{icon}</div>
      </div>
      <div className="min-w-0">
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-1">{label}</p>
        <p className="text-2xl font-bold text-gray-900 font-display leading-none">{value}</p>
        {sub && <p className="text-sm text-gray-400 mt-1">{sub}</p>}
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { user } = useAuthStore();
  const isAdmin = user?.role === 'admin';
  const isManager = user?.role === 'manager';
  const canViewAdmin = isAdmin || isManager;

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: adminApi.stats,
    enabled: canViewAdmin,
    refetchInterval: 30000,
  });

  const { data: todayRecords } = useQuery({
    queryKey: ['today-attendance'],
    queryFn: attendanceApi.today,
    enabled: canViewAdmin,
    refetchInterval: 30000,
  });

  const currentYear = new Date().getFullYear();
  const currentMonth = new Date().getMonth() + 1;
  const { data: monthlyReport } = useQuery({
    queryKey: ['monthly-report', currentYear, currentMonth],
    queryFn: () => reportsApi.monthly(currentYear, currentMonth),
    enabled: canViewAdmin,
  });

  const chartData = monthlyReport?.by_day?.slice(-14).map((d: { date: string; checked_in: number; total_employees: number }) => ({
    date: new Date(d.date).toLocaleDateString('en', { day: 'numeric', month: 'short' }),
    'Checked In': d.checked_in,
    Total: d.total_employees,
  })) ?? [];

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <h1 className="page-title">
          Good {getGreeting()},{' '}
          <span style={{ color: '#002395' }}>{user?.first_name}</span>
        </h1>
        <p className="page-subtitle">{formatDate(new Date().toISOString())} · {user?.role} view</p>
      </div>

      {/* Admin/Manager Stats */}
      {canViewAdmin && (
        <>
          {statsLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
              {Array(6).fill(0).map((_, i) => <StatCardSkeleton key={i} />)}
            </div>
          ) : stats && (
            <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4 mb-6">
              <StatCard label="Total Staff" value={stats.total_employees} color="#002395"
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" /></svg>}
              />
              <StatCard label="Active Staff" value={stats.active_employees} color="#00A550"
                sub="Registered & active"
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
              />
              <StatCard label="On Site Today" value={stats.checked_in_today} color="#7c3aed"
                sub="Currently checked in"
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" /></svg>}
              />
              <StatCard label="Attendance Rate" value={`${Math.round(stats.attendance_rate_today)}%`}
                color={stats.attendance_rate_today >= 80 ? '#00A550' : '#f59e0b'}
                sub="Today"
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>}
              />
              <StatCard label="Departments" value={stats.total_departments} color="#0891b2"
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>}
              />
              <StatCard label="Open Flags" value={stats.open_flags}
                color={stats.open_flags > 0 ? '#ef4444' : '#6b7280'}
                sub={stats.open_flags > 0 ? 'Needs review' : 'All clear'}
                icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6H8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" /></svg>}
              />
            </div>
          )}

          {/* Chart + Recent activity */}
          <div className="grid lg:grid-cols-3 gap-6 mb-6">
            {/* Trend chart */}
            <div className="lg:col-span-2 card p-6">
              <h3 className="font-bold text-gray-900 font-display mb-4">14-Day Attendance Trend</h3>
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={chartData} barGap={2}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                    <XAxis dataKey="date" tick={{ fontSize: 11, fontFamily: 'DM Sans' }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 11, fontFamily: 'DM Sans' }} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{ borderRadius: 12, border: 'none', boxShadow: '0 4px 24px rgba(0,0,0,0.12)', fontFamily: 'DM Sans', fontSize: 12 }}
                    />
                    <Bar dataKey="Checked In" fill="#002395" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Total" fill="#e5e7eb" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
                  No data yet for this month
                </div>
              )}
            </div>

            {/* Quick actions */}
            <div className="card p-6">
              <h3 className="font-bold text-gray-900 font-display mb-4">Quick Actions</h3>
              <div className="space-y-2">
                {[
                  { to: '/check-in', label: 'Check In / Out', color: '#00A550', desc: 'QR scan + GPS' },
                  { to: '/employees', label: 'Manage Employees', color: '#002395', desc: 'Add, edit, QR codes' },
                  { to: '/reports', label: 'View Reports', color: '#7c3aed', desc: 'Daily & monthly' },
                  ...(isAdmin ? [{ to: '/admin', label: 'Admin Panel', color: '#ef4444', desc: 'Flags & audit log' }] : []),
                ].map(({ to, label, color, desc }) => (
                  <Link
                    key={to}
                    to={to}
                    className="flex items-center gap-3 p-3 rounded-xl hover:bg-gray-50 transition-colors group"
                  >
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: color }} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 group-hover:text-gray-900">{label}</p>
                      <p className="text-xs text-gray-400">{desc}</p>
                    </div>
                    <svg className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </Link>
                ))}
              </div>
            </div>
          </div>

          {/* Today's check-ins */}
          {todayRecords && todayRecords.length > 0 && (
            <div className="card overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
                <h3 className="font-bold text-gray-900 font-display">Today's Attendance</h3>
                <span className="badge-info badge">{todayRecords.length} records</span>
              </div>
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Employee</th>
                      <th>Check In</th>
                      <th>Check Out</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {todayRecords.slice(0, 10).map((rec) => (
                      <tr key={rec.id}>
                        <td>
                          <div className="flex items-center gap-3">
                            {rec.employee && (
                              <Avatar
                                firstName={rec.employee.first_name}
                                lastName={rec.employee.last_name}
                                size="sm"
                              />
                            )}
                            <div>
                              <p className="font-medium text-gray-900 text-sm">
                                {rec.employee?.first_name} {rec.employee?.last_name}
                              </p>
                              <p className="text-xs text-gray-400">{rec.employee?.position}</p>
                            </div>
                          </div>
                        </td>
                        <td className="text-sm">{formatTime(rec.check_in_time)}</td>
                        <td className="text-sm">
                          {rec.check_out_time ? formatTime(rec.check_out_time) : <span className="text-gray-300">—</span>}
                        </td>
                        <td><StatusBadge status={rec.status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {todayRecords.length > 10 && (
                <div className="px-6 py-3 border-t border-gray-50">
                  <Link to="/reports" className="text-sm text-[#002395] hover:underline font-medium">
                    View all {todayRecords.length} records →
                  </Link>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* Employee view */}
      {user?.role === 'employee' && (
        <div className="max-w-lg">
          <div className="card p-8 text-center mb-4">
            <div className="w-16 h-16 rounded-2xl bg-[#002395]/10 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-[#002395]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 font-display mb-2">
              Welcome, {user.first_name}!
            </h2>
            <p className="text-gray-500 text-sm mb-6">
              Use the QR scanner to record your attendance today.
            </p>
            <Link to="/check-in" className="btn-success inline-flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01" />
              </svg>
              Scan QR to Check In
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'morning';
  if (h < 17) return 'afternoon';
  return 'evening';
}
