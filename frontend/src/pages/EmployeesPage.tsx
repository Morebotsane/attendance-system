import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { employeesApi } from '../api/employees';
import { departmentsApi } from '../api/departments';
import { adminApi } from '../api/admin';
import { Avatar, RoleBadge, ActiveBadge } from '../components/common/Badges';
import { Modal } from '../components/common/Modal';
import { PageLoader, Spinner } from '../components/common/Loading';
import { toast, extractApiError } from '../utils/helpers';
import type { Employee, Role, CreateEmployeePayload } from '../types/api';
import { useAuthStore } from '../store/authStore';

function EmployeeForm({
  initial,
  onSubmit,
  loading,
  departments,
}: {
  initial?: Partial<Employee>;
  onSubmit: (data: CreateEmployeePayload & { id?: string }) => void;
  loading: boolean;
  departments: Array<{ id: string; name: string }>;
}) {
  const [form, setForm] = useState({
    employee_number: initial?.employee_number ?? '',
    first_name: initial?.first_name ?? '',
    last_name: initial?.last_name ?? '',
    email: initial?.email ?? '',
    phone: initial?.phone ?? '',
    position: initial?.position ?? '',
    department_id: initial?.department_id ?? '',
    role: (initial?.role ?? 'employee') as Role,
    password: '',
  });

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({ ...form, id: initial?.id });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="input-label">First Name *</label>
          <input className="input-field" value={form.first_name} onChange={(e) => set('first_name', e.target.value)} required />
        </div>
        <div>
          <label className="input-label">Last Name *</label>
          <input className="input-field" value={form.last_name} onChange={(e) => set('last_name', e.target.value)} required />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="input-label">Employee # *</label>
          <input className="input-field font-mono" value={form.employee_number} onChange={(e) => set('employee_number', e.target.value)} required placeholder="EMP001" />
        </div>
        <div>
          <label className="input-label">Role *</label>
          <select className="input-field" value={form.role} onChange={(e) => set('role', e.target.value)}>
            <option value="employee">Employee</option>
            <option value="manager">Manager</option>
            <option value="admin">Admin</option>
          </select>
        </div>
      </div>
      <div>
        <label className="input-label">Email *</label>
        <input className="input-field" type="email" value={form.email} onChange={(e) => set('email', e.target.value)} required />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="input-label">Phone</label>
          <input className="input-field" type="tel" value={form.phone} onChange={(e) => set('phone', e.target.value)} placeholder="+266XXXXXXXX" />
        </div>
        <div>
          <label className="input-label">Position *</label>
          <input className="input-field" value={form.position} onChange={(e) => set('position', e.target.value)} required />
        </div>
      </div>
      <div>
        <label className="input-label">Department</label>
        <select className="input-field" value={form.department_id} onChange={(e) => set('department_id', e.target.value)}>
          <option value="">— No department —</option>
          {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </div>
      {!initial?.id && (
        <div>
          <label className="input-label">Password *</label>
          <input className="input-field" type="password" value={form.password} onChange={(e) => set('password', e.target.value)} required={!initial?.id} placeholder="Set initial password" />
        </div>
      )}
      <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
        {loading ? <><Spinner size="sm" color="white" /> Saving…</> : (initial?.id ? 'Update Employee' : 'Add Employee')}
      </button>
    </form>
  );
}

function QrModal({ employee, onClose }: { employee: Employee; onClose: () => void }) {
  const { data, isLoading } = useQuery({
    queryKey: ['qr', employee.id],
    queryFn: () => adminApi.generateQr(employee.id),
  });

  const downloadUrl = adminApi.downloadQr(employee.id);

  return (
    <Modal isOpen onClose={onClose} title="QR Code" size="sm">
      <div className="text-center">
        <div className="flex items-center gap-3 mb-5">
          <Avatar firstName={employee.first_name} lastName={employee.last_name} />
          <div className="text-left">
            <p className="font-semibold text-gray-900">{employee.first_name} {employee.last_name}</p>
            <p className="text-sm text-gray-400">{employee.employee_number}</p>
          </div>
        </div>
        {isLoading ? (
          <div className="h-48 flex items-center justify-center"><Spinner /></div>
        ) : data?.qr_code_image ? (
          <img
            src={`data:image/png;base64,${data.qr_code_image}`}
            alt="QR Code"
            className="w-48 h-48 mx-auto rounded-xl border-4 border-gray-100 mb-4"
          />
        ) : (
          <div className="h-48 flex items-center justify-center text-gray-400 text-sm">QR unavailable</div>
        )}
        <a
          href={downloadUrl}
          download
          className="btn-primary inline-flex items-center gap-2 text-sm"
          target="_blank" rel="noreferrer"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download PNG
        </a>
      </div>
    </Modal>
  );
}

export function EmployeesPage() {
  const { user } = useAuthStore();
  const qc = useQueryClient();
  const [search, setSearch] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<Employee | null>(null);
  const [qrEmployee, setQrEmployee] = useState<Employee | null>(null);

  const { data: employees, isLoading } = useQuery({
    queryKey: ['employees', search],
    queryFn: () => employeesApi.list({ search, limit: 100 }),
  });

  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: departmentsApi.list,
  });

  const createMutation = useMutation({
    mutationFn: (p: CreateEmployeePayload) => employeesApi.create(p),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employees'] });
      setShowAdd(false);
      toast.success('Employee added successfully');
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: Partial<Employee> & { id: string }) => employeesApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['employees'] });
      setEditing(null);
      toast.success('Employee updated');
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) => employeesApi.setActive(id, is_active),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['employees'] }); toast.success('Status updated'); },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const handleForm = (data: CreateEmployeePayload & { id?: string }) => {
    if (data.id) {
      updateMutation.mutate(data as unknown as Employee);
    } else {
      createMutation.mutate(data as CreateEmployeePayload);
    }
  };

  return (
    <div>
      <div className="page-header flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="page-title">Employees</h1>
          <p className="page-subtitle">{employees?.length ?? 0} staff members</p>
        </div>
        {user?.role === 'admin' && (
          <button onClick={() => setShowAdd(true)} className="btn-primary flex items-center gap-2 shrink-0">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Employee
          </button>
        )}
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <svg className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
          fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          className="input-field pl-10"
          placeholder="Search by name, email, employee number…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {isLoading ? <PageLoader /> : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Employee</th>
                  <th className="hidden md:table-cell">Department</th>
                  <th className="hidden lg:table-cell">Contact</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {(employees ?? []).map((emp) => (
                  <tr key={emp.id}>
                    <td>
                      <div className="flex items-center gap-3">
                        <Avatar firstName={emp.first_name} lastName={emp.last_name} size="sm" />
                        <div>
                          <p className="font-medium text-gray-900">{emp.first_name} {emp.last_name}</p>
                          <p className="text-xs text-gray-400 font-mono">{emp.employee_number}</p>
                        </div>
                      </div>
                    </td>
                    <td className="hidden md:table-cell text-sm text-gray-500">
                      {emp.department?.name ?? <span className="text-gray-300">—</span>}
                    </td>
                    <td className="hidden lg:table-cell">
                      <p className="text-sm text-gray-600">{emp.email}</p>
                      <p className="text-xs text-gray-400">{emp.phone}</p>
                    </td>
                    <td><RoleBadge role={emp.role} /></td>
                    <td><ActiveBadge active={emp.is_active} /></td>
                    <td>
                      <div className="flex items-center gap-1">
                        <button
                          title="View QR"
                          onClick={() => setQrEmployee(emp)}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-[#002395] hover:bg-blue-50 transition-colors"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4" />
                          </svg>
                        </button>
                        {user?.role === 'admin' && (
                          <>
                            <button
                              title="Edit"
                              onClick={() => setEditing(emp)}
                              className="p-1.5 rounded-lg text-gray-400 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                            </button>
                            <button
                              title={emp.is_active ? 'Deactivate' : 'Activate'}
                              onClick={() => toggleActive.mutate({ id: emp.id, is_active: !emp.is_active })}
                              className={`p-1.5 rounded-lg transition-colors ${
                                emp.is_active
                                  ? 'text-gray-400 hover:text-red-600 hover:bg-red-50'
                                  : 'text-gray-400 hover:text-emerald-600 hover:bg-emerald-50'
                              }`}
                            >
                              {emp.is_active ? (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                                </svg>
                              ) : (
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                              )}
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {(employees ?? []).length === 0 && (
                  <tr><td colSpan={6} className="text-center py-12 text-gray-400">
                    {search ? 'No employees match your search.' : 'No employees yet.'}
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add modal */}
      <Modal isOpen={showAdd} onClose={() => setShowAdd(false)} title="Add Employee" size="lg">
        <EmployeeForm departments={departments} onSubmit={handleForm} loading={createMutation.isPending} />
      </Modal>

      {/* Edit modal */}
      {editing && (
        <Modal isOpen onClose={() => setEditing(null)} title="Edit Employee" size="lg">
          <EmployeeForm initial={editing} departments={departments} onSubmit={handleForm} loading={updateMutation.isPending} />
        </Modal>
      )}

      {/* QR modal */}
      {qrEmployee && <QrModal employee={qrEmployee} onClose={() => setQrEmployee(null)} />}
    </div>
  );
}
