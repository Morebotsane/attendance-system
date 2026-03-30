import api from './client';
import type { SystemStats, AttendanceFlag, AuditLog, DailyReport, MonthlyReport, EmployeeReport } from '../types/api';

export const adminApi = {
  stats: async (): Promise<SystemStats> => {
    const { data } = await api.get<SystemStats>('/admin/stats');
    return data;
  },

  generateQr: async (employee_id: string): Promise<{ qr_code_data: string; qr_code_image: string }> => {
    const { data } = await api.post(`/admin/generate-qr/${employee_id}`);
    return data;
  },

  downloadQr: (employee_id: string) => {
    return api.defaults.baseURL + `/admin/qr/${employee_id}/download`;
  },

  bulkQr: async (employee_ids: string[]) => {
    const { data } = await api.post('/admin/bulk-qr-generate', { employee_ids });
    return data;
  },

  flags: async (params?: { skip?: number; limit?: number; is_resolved?: boolean }): Promise<AttendanceFlag[]> => {
    const { data } = await api.get<AttendanceFlag[]>('/admin/flags', { params });
    return data;
  },

  resolveFlag: async (flag_id: string, resolution_notes: string): Promise<AttendanceFlag> => {
    const { data } = await api.put<AttendanceFlag>(`/admin/flags/${flag_id}/resolve`, { resolution_notes });
    return data;
  },

  auditLog: async (params?: { skip?: number; limit?: number; employee_id?: string }): Promise<AuditLog[]> => {
    const { data } = await api.get<AuditLog[]>('/admin/audit-log', { params });
    return data;
  },
};

export const reportsApi = {
  daily: async (date: string, department_id?: string): Promise<DailyReport> => {
    const { data } = await api.post<DailyReport>('/reports/daily', { date, department_id });
    return data;
  },

  monthly: async (year: number, month: number, department_id?: string): Promise<MonthlyReport> => {
    const { data } = await api.get<MonthlyReport>('/reports/monthly', { params: { year, month, department_id } });
    return data;
  },

  employee: async (employee_id: string, start_date: string, end_date: string): Promise<EmployeeReport> => {
    const { data } = await api.get<EmployeeReport>(`/reports/employee/${employee_id}`, {
      params: { start_date, end_date },
    });
    return data;
  },

  summary: async (start_date: string, end_date: string) => {
    const { data } = await api.get('/reports/summary', { params: { start_date, end_date } });
    return data;
  },

  flags: async (params: { start_date?: string; end_date?: string; flag_type?: string }) => {
    const { data } = await api.get('/reports/flags', { params });
    return data;
  },
};
