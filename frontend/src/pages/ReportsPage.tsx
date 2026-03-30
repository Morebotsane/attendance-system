import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts';
import { reportsApi } from '../api/reports';
import { departmentsApi } from '../api/departments';
import { employeesApi } from '../api/employees';
import { StatusBadge } from '../components/common/Badges';
import { PageLoader } from '../components/common/Loading';
import { formatTime, formatDate, formatHours } from '../utils/helpers';

type Tab = 'daily' | 'monthly' | 'employee';

export function ReportsPage() {
  const [tab, setTab] = useState<Tab>('daily');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [year, setYear] = useState(new Date().getFullYear());
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [deptId, setDeptId] = useState('');
  const [empId, setEmpId] = useState('');
  const [startDate, setStartDate] = useState(() => {
    const d = new Date(); d.setDate(1); return d.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);

  const { data: departments = [] } = useQuery({ queryKey: ['departments'], queryFn: departmentsApi.list });
  const { data: employees = [] } = useQuery({ queryKey: ['employees-list'], queryFn: () => employeesApi.list({ limit: 200 }) });

  const { data: daily, isLoading: dailyLoading } = useQuery({
    queryKey: ['report-daily', date, deptId],
    queryFn: () => reportsApi.daily(date, deptId || undefined),
    enabled: tab === 'daily',
  });

  const { data: monthly, isLoading: monthlyLoading } = useQuery({
    queryKey: ['report-monthly', year, month, deptId],
    queryFn: () => reportsApi.monthly(year, month, deptId || undefined),
    enabled: tab === 'monthly',
  });

  const { data: empReport, isLoading: empLoading } = useQuery({
    queryKey: ['report-employee', empId, startDate, endDate],
    queryFn: () => reportsApi.employee(empId, startDate, endDate),
    enabled: tab === 'employee' && !!empId,
  });

  const tabs: { key: Tab; label: string }[] = [
    { key: 'daily', label: 'Daily Report' },
    { key: 'monthly', label: 'Monthly Trend' },
    { key: 'employee', label: 'Employee Report' },
  ];

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Reports & Analytics</h1>
        <p className="page-subtitle">Attendance insights across all departments</p>
      </div>

      {/* Tab bar */}
      <div className="card p-1 flex gap-1 mb-6 max-w-md">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex-1 py-2 px-3 rounded-xl text-sm font-medium transition-all duration-200 ${
              tab === t.key ? 'bg-[#002395] text-white' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* DAILY */}
      {tab === 'daily' && (
        <div className="space-y-6 animate-fade-in">
          <div className="flex flex-wrap gap-3">
            <input type="date" className="input-field w-auto" value={date} onChange={(e) => setDate(e.target.value)} />
            <select className="input-field w-auto" value={deptId} onChange={(e) => setDeptId(e.target.value)}>
              <option value="">All Departments</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>

          {dailyLoading ? <PageLoader /> : daily && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Total Staff', value: daily.total_employees, color: '#002395' },
                  { label: 'Checked In', value: daily.checked_in, color: '#00A550' },
                  { label: 'Still On Site', value: daily.still_active, color: '#7c3aed' },
                  { label: 'Attendance Rate', value: `${Math.round(daily.attendance_rate)}%`, color: '#0891b2' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="card p-5">
                    <p className="text-xs text-gray-400 uppercase tracking-wide font-medium mb-1">{label}</p>
                    <p className="text-3xl font-bold font-display" style={{ color }}>{value}</p>
                  </div>
                ))}
              </div>

              {daily.by_department?.length > 0 && (
                <div className="card p-6">
                  <h3 className="font-bold text-gray-900 font-display mb-4">By Department</h3>
                  <div className="space-y-3">
                    {daily.by_department.map((d: { department_name: string; checked_in: number; total: number }) => {
                      const pct = d.total > 0 ? Math.round((d.checked_in / d.total) * 100) : 0;
                      return (
                        <div key={d.department_name}>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="font-medium text-gray-700">{d.department_name}</span>
                            <span className="text-gray-500">{d.checked_in}/{d.total} · {pct}%</span>
                          </div>
                          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all duration-500"
                              style={{ width: `${pct}%`, backgroundColor: pct >= 80 ? '#00A550' : pct >= 50 ? '#f59e0b' : '#ef4444' }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* MONTHLY */}
      {tab === 'monthly' && (
        <div className="space-y-6 animate-fade-in">
          <div className="flex flex-wrap gap-3">
            <select className="input-field w-auto" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
              {Array.from({ length: 12 }, (_, i) => (
                <option key={i + 1} value={i + 1}>
                  {new Date(2024, i).toLocaleString('en', { month: 'long' })}
                </option>
              ))}
            </select>
            <select className="input-field w-auto" value={year} onChange={(e) => setYear(Number(e.target.value))}>
              {[2024, 2025, 2026].map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
            <select className="input-field w-auto" value={deptId} onChange={(e) => setDeptId(e.target.value)}>
              <option value="">All Departments</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>

          {monthlyLoading ? <PageLoader /> : monthly && (
            <>
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: 'Avg Attendance', value: `${Math.round(monthly.average_attendance_rate)}%`, color: '#002395' },
                  { label: 'Total Hours', value: `${Math.round(monthly.total_hours_worked)}h`, color: '#00A550' },
                  { label: 'Working Days', value: monthly.total_days, color: '#7c3aed' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="card p-5">
                    <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
                    <p className="text-3xl font-bold font-display" style={{ color }}>{value}</p>
                  </div>
                ))}
              </div>

              <div className="card p-6">
                <h3 className="font-bold text-gray-900 font-display mb-4">Daily Attendance Trend</h3>
                <ResponsiveContainer width="100%" height={240}>
                  <LineChart data={monthly.by_day.map((d: { date: string; checked_in: number; total_employees: number }) => ({
                    day: new Date(d.date).getDate(),
                    checked_in: d.checked_in,
                    total: d.total_employees,
                    rate: d.total_employees > 0 ? Math.round((d.checked_in / d.total_employees) * 100) : 0,
                  }))}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                    <XAxis dataKey="day" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} unit="%" />
                    <Tooltip
                      contentStyle={{ borderRadius: 12, border: 'none', boxShadow: '0 4px 24px rgba(0,0,0,0.12)', fontFamily: 'DM Sans', fontSize: 12 }}
                      formatter={(v) => [`${v ?? 0}%`, 'Attendance Rate']}
                    />
                    <Line dataKey="rate" stroke="#002395" strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </div>
      )}

      {/* EMPLOYEE */}
      {tab === 'employee' && (
        <div className="space-y-6 animate-fade-in">
          <div className="flex flex-wrap gap-3">
            <select
              className="input-field w-auto min-w-48"
              value={empId}
              onChange={(e) => setEmpId(e.target.value)}
            >
              <option value="">Select Employee…</option>
              {employees.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.first_name} {e.last_name} ({e.employee_number})
                </option>
              ))}
            </select>
            <input type="date" className="input-field w-auto" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            <input type="date" className="input-field w-auto" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>

          {!empId && (
            <div className="card p-12 text-center text-gray-400">
              <svg className="w-12 h-12 mx-auto mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
              Select an employee to view their report
            </div>
          )}

          {empLoading && empId && <PageLoader />}

          {empReport && (
            <>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Days Attended', value: `${empReport.days_attended}/${empReport.total_days}`, color: '#002395' },
                  { label: 'Attendance Rate', value: `${Math.round(empReport.attendance_rate)}%`, color: '#00A550' },
                  { label: 'Total Hours', value: `${Math.round(empReport.total_hours)}h`, color: '#7c3aed' },
                  { label: 'Avg Hours/Day', value: `${empReport.average_hours_per_day.toFixed(1)}h`, color: '#0891b2' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="card p-5">
                    <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
                    <p className="text-3xl font-bold font-display" style={{ color }}>{value}</p>
                  </div>
                ))}
              </div>

              <div className="card overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-100">
                  <h3 className="font-bold text-gray-900 font-display">Attendance Records</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Check In</th>
                        <th>Check Out</th>
                        <th>Hours</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {empReport.records.map((rec) => (
                        <tr key={rec.id}>
                          <td className="text-sm font-medium">{formatDate(rec.check_in_time)}</td>
                          <td className="text-sm">{formatTime(rec.check_in_time)}</td>
                          <td className="text-sm">{rec.check_out_time ? formatTime(rec.check_out_time) : <span className="text-gray-300">—</span>}</td>
                          <td className="text-sm font-medium text-[#002395]">
                            {formatHours(rec.check_in_time, rec.check_out_time)}
                          </td>
                          <td><StatusBadge status={rec.status} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
