import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../api/admin';
import { SeverityBadge } from '../components/common/Badges';
import { Modal } from '../components/common/Modal';
import { PageLoader, Spinner } from '../components/common/Loading';
import { formatDate, toast, extractApiError } from '../utils/helpers';

type Tab = 'flags' | 'audit';

const FLAG_TYPE_LABELS: Record<string, string> = {
  GEOFENCE_VIOLATION: 'Geofence Violation',
  DUPLICATE_CHECKIN: 'Duplicate Check-in',
  LATE_ARRIVAL: 'Late Arrival',
  EARLY_DEPARTURE: 'Early Departure',
  SUSPICIOUS_PATTERN: 'Suspicious Pattern',
};

export function AdminPage() {
  const [tab, setTab] = useState<Tab>('flags');
  const [showResolved, setShowResolved] = useState(false);
  const [resolving, setResolving] = useState<string | null>(null);
  const [notes, setNotes] = useState('');
  const qc = useQueryClient();

  const { data: flags, isLoading: flagsLoading } = useQuery({
    queryKey: ['flags', showResolved],
    queryFn: () => adminApi.flags({ is_resolved: showResolved || undefined, limit: 100 }),
  });

  const { data: auditLog, isLoading: auditLoading } = useQuery({
    queryKey: ['audit-log'],
    queryFn: () => adminApi.auditLog({ limit: 100 }),
    enabled: tab === 'audit',
  });

  const resolveMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) => adminApi.resolveFlag(id, notes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['flags'] });
      qc.invalidateQueries({ queryKey: ['admin-stats'] });
      setResolving(null);
      setNotes('');
      toast.success('Flag resolved');
    },
    onError: (err) => toast.error(extractApiError(err)),
  });

  const openFlags = flags?.filter((f) => !f.is_resolved) ?? [];
  const resolvedFlags = flags?.filter((f) => f.is_resolved) ?? [];

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Admin Panel</h1>
        <p className="page-subtitle">System flags, audit trail & configuration</p>
      </div>

      {/* Flags summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Open Flags', value: openFlags.length, color: openFlags.length > 0 ? '#ef4444' : '#6b7280' },
          { label: 'Resolved', value: resolvedFlags.length, color: '#00A550' },
          { label: 'High Severity', value: openFlags.filter((f) => f.severity === 'high').length, color: '#dc2626' },
          { label: 'Geofence Violations', value: openFlags.filter((f) => f.flag_type === 'GEOFENCE_VIOLATION').length, color: '#7c3aed' },
        ].map(({ label, value, color }) => (
          <div key={label} className="card p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
            <p className="text-3xl font-bold font-display" style={{ color }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="card p-1 flex gap-1 mb-6 max-w-xs">
        {([['flags', 'Flags'], ['audit', 'Audit Log']] as [Tab, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex-1 py-2 px-3 rounded-xl text-sm font-medium transition-all ${
              tab === key ? 'bg-[#002395] text-white' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {label}
            {key === 'flags' && openFlags.length > 0 && (
              <span className="ml-1.5 inline-flex items-center justify-center w-4 h-4 bg-red-500 text-white text-[10px] rounded-full">
                {openFlags.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* FLAGS TAB */}
      {tab === 'flags' && (
        <div className="animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900 font-display">
              {showResolved ? 'All Flags' : 'Open Flags'}
            </h3>
            <button
              onClick={() => setShowResolved((v) => !v)}
              className="text-sm text-[#002395] hover:underline font-medium"
            >
              {showResolved ? 'Show open only' : 'Show resolved too'}
            </button>
          </div>

          {flagsLoading ? <PageLoader /> : (
            <div className="card overflow-hidden">
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Type</th>
                      <th>Description</th>
                      <th>Severity</th>
                      <th>Created</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(flags ?? []).map((flag) => (
                      <tr key={flag.id}>
                        <td>
                          <span className="text-sm font-medium text-gray-800">
                            {FLAG_TYPE_LABELS[flag.flag_type] ?? flag.flag_type}
                          </span>
                        </td>
                        <td className="text-sm text-gray-500 max-w-xs truncate">{flag.description}</td>
                        <td><SeverityBadge severity={flag.severity} /></td>
                        <td className="text-sm text-gray-500">{formatDate(flag.created_at)}</td>
                        <td>
                          {flag.is_resolved
                            ? <span className="badge-success badge">Resolved</span>
                            : <span className="badge-danger badge">Open</span>}
                        </td>
                        <td>
                          {!flag.is_resolved && (
                            <button
                              onClick={() => { setResolving(flag.id); setNotes(''); }}
                              className="text-sm text-[#002395] hover:underline font-medium"
                            >
                              Resolve
                            </button>
                          )}
                          {flag.is_resolved && flag.resolution_notes && (
                            <span className="text-xs text-gray-400 truncate max-w-32 block" title={flag.resolution_notes}>
                              {flag.resolution_notes}
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                    {(flags ?? []).length === 0 && (
                      <tr><td colSpan={6} className="text-center py-12 text-gray-400">
                        {showResolved ? 'No flags found.' : '🎉 No open flags — all clear!'}
                      </td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* AUDIT LOG TAB */}
      {tab === 'audit' && (
        <div className="animate-fade-in">
          {auditLoading ? <PageLoader /> : (
            <div className="card overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100">
                <h3 className="font-bold text-gray-900 font-display">System Audit Trail</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>Employee</th>
                      <th>Action</th>
                      <th>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(auditLog ?? []).map((log) => (
                      <tr key={log.id}>
                        <td className="text-xs text-gray-500 font-mono whitespace-nowrap">
                          {new Date(log.created_at).toLocaleString('en-LS')}
                        </td>
                        <td className="text-sm font-medium text-gray-800">
                          {log.employee?.first_name} {log.employee?.last_name}
                        </td>
                        <td>
                          <span className="badge-info badge font-mono text-xs">{log.action}</span>
                        </td>
                        <td className="text-sm text-gray-500 max-w-xs truncate">{log.details}</td>
                      </tr>
                    ))}
                    {(auditLog ?? []).length === 0 && (
                      <tr><td colSpan={4} className="text-center py-12 text-gray-400">No audit records yet.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Resolve modal */}
      <Modal
        isOpen={!!resolving}
        onClose={() => setResolving(null)}
        title="Resolve Flag"
        footer={
          <>
            <button onClick={() => setResolving(null)} className="btn-outline text-sm py-2">Cancel</button>
            <button
              onClick={() => resolveMutation.mutate({ id: resolving!, notes })}
              disabled={!notes.trim() || resolveMutation.isPending}
              className="btn-primary text-sm py-2 flex items-center gap-2"
            >
              {resolveMutation.isPending ? <><Spinner size="sm" color="white" /> Saving…</> : 'Resolve Flag'}
            </button>
          </>
        }
      >
        <div>
          <p className="text-sm text-gray-500 mb-4">
            Add resolution notes to close this flag. This action is recorded in the audit log.
          </p>
          <label className="input-label">Resolution Notes *</label>
          <textarea
            className="input-field resize-none"
            rows={4}
            placeholder="Describe how this was resolved…"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>
      </Modal>
    </div>
  );
}
