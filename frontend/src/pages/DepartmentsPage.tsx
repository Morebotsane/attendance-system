import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { departmentsApi } from '../api/departments';
import { Modal } from '../components/common/Modal';
import { PageLoader, Spinner } from '../components/common/Loading';
import { toast, extractApiError } from '../utils/helpers';
import type { Department } from '../types/api';

function DeptForm({
  initial,
  onSubmit,
  loading,
}: {
  initial?: Partial<Department>;
  onSubmit: (d: Partial<Department>) => void;
  loading: boolean;
}) {
  const [form, setForm] = useState({
    name: initial?.name ?? '',
    code: initial?.code ?? '',
    description: initial?.description ?? '',
    location: initial?.location ?? '',
    latitude: initial?.latitude ?? '',
    longitude: initial?.longitude ?? '',
    geofence_radius: initial?.geofence_radius ?? 100,
  });
  const set = (k: string, v: string | number) => setForm((f) => ({ ...f, [k]: v }));

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit({ ...form, latitude: Number(form.latitude), longitude: Number(form.longitude) }); }} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="input-label">Name *</label>
          <input className="input-field" value={form.name} onChange={(e) => set('name', e.target.value)} required placeholder="Cardiology" />
        </div>
        <div>
          <label className="input-label">Code *</label>
          <input className="input-field font-mono uppercase" value={form.code} onChange={(e) => set('code', e.target.value.toUpperCase())} required placeholder="CARD" maxLength={10} />
        </div>
      </div>
      <div>
        <label className="input-label">Description</label>
        <input className="input-field" value={form.description} onChange={(e) => set('description', e.target.value)} />
      </div>
      <div>
        <label className="input-label">Physical Location *</label>
        <input className="input-field" value={form.location} onChange={(e) => set('location', e.target.value)} required placeholder="Block A, 2nd Floor, Maseru" />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="input-label">GPS Latitude *</label>
          <input className="input-field font-mono" type="number" step="any" value={form.latitude} onChange={(e) => set('latitude', e.target.value)} required placeholder="-29.3167" />
        </div>
        <div>
          <label className="input-label">GPS Longitude *</label>
          <input className="input-field font-mono" type="number" step="any" value={form.longitude} onChange={(e) => set('longitude', e.target.value)} required placeholder="27.4833" />
        </div>
      </div>
      <div>
        <label className="input-label">Geofence Radius: {form.geofence_radius}m</label>
        <input
          type="range" min="25" max="500" step="25"
          value={form.geofence_radius}
          onChange={(e) => set('geofence_radius', Number(e.target.value))}
          className="w-full accent-[#002395]"
        />
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>25m (tight)</span><span>250m</span><span>500m (wide)</span>
        </div>
      </div>
      <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2">
        {loading ? <><Spinner size="sm" color="white" />Saving…</> : (initial?.id ? 'Update' : 'Add Department')}
      </button>
    </form>
  );
}

export function DepartmentsPage() {
  const qc = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<Department | null>(null);

  const { data: departments, isLoading } = useQuery({
    queryKey: ['departments'],
    queryFn: departmentsApi.list,
  });

  const createMutation = useMutation({
    mutationFn: (d: Partial<Department>) => departmentsApi.create(d as Parameters<typeof departmentsApi.create>[0]),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['departments'] }); setShowAdd(false); toast.success('Department created'); },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }: Partial<Department> & { id: string }) => departmentsApi.update(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['departments'] }); setEditing(null); toast.success('Department updated'); },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => departmentsApi.delete(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['departments'] }); toast.success('Department removed'); },
    onError: (err) => toast.error(extractApiError(err)),
  });

  return (
    <div>
      <div className="page-header flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="page-title">Departments</h1>
          <p className="page-subtitle">{departments?.length ?? 0} departments configured</p>
        </div>
        <button onClick={() => setShowAdd(true)} className="btn-primary flex items-center gap-2 shrink-0">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Department
        </button>
      </div>

      {isLoading ? <PageLoader /> : (
        <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
          {(departments ?? []).map((dept) => (
            <div key={dept.id} className="card p-5 hover:shadow-card-hover transition-shadow duration-200">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[#002395]/8 flex items-center justify-center">
                    <svg className="w-5 h-5 text-[#002395]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  </div>
                  <div>
                    <p className="font-bold text-gray-900 font-display">{dept.name}</p>
                    <p className="text-xs text-gray-400 font-mono">{dept.code}</p>
                  </div>
                </div>
                <div className="flex gap-1">
                  <button onClick={() => setEditing(dept)} className="p-1.5 rounded-lg text-gray-400 hover:text-amber-600 hover:bg-amber-50 transition-colors">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                  </button>
                  <button onClick={() => { if (confirm(`Delete ${dept.name}?`)) deleteMutation.mutate(dept.id); }} className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </div>
              </div>

              {dept.description && (
                <p className="text-sm text-gray-500 mb-3">{dept.description}</p>
              )}

              <div className="space-y-1.5 text-sm">
                <div className="flex items-center gap-2 text-gray-500">
                  <svg className="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  </svg>
                  <span className="truncate">{dept.location}</span>
                </div>
                <div className="flex items-center gap-2 text-gray-500">
                  <svg className="w-3.5 h-3.5 shrink-0 text-[#002395]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                  </svg>
                  <span className="font-mono text-xs">{dept.latitude.toFixed(4)}, {dept.longitude.toFixed(4)}</span>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-gray-50 flex items-center justify-between">
                <span className="text-xs text-gray-400">Geofence radius</span>
                <span className="text-sm font-semibold text-[#002395]">{dept.geofence_radius}m</span>
              </div>
            </div>
          ))}

          {(departments ?? []).length === 0 && (
            <div className="col-span-full card p-12 text-center text-gray-400">
              No departments configured yet.
            </div>
          )}
        </div>
      )}

      <Modal isOpen={showAdd} onClose={() => setShowAdd(false)} title="Add Department" size="lg">
        <DeptForm onSubmit={(d) => createMutation.mutate(d)} loading={createMutation.isPending} />
      </Modal>

      {editing && (
        <Modal isOpen onClose={() => setEditing(null)} title="Edit Department" size="lg">
          <DeptForm
            initial={editing}
            onSubmit={(d) => updateMutation.mutate({ ...d, id: editing.id })}
            loading={updateMutation.isPending}
          />
        </Modal>
      )}
    </div>
  );
}
