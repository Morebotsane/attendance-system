import api from './client';
import type { Employee, CreateEmployeePayload } from '../types/api';

export const employeesApi = {
  list: async (params?: { skip?: number; limit?: number; search?: string; department_id?: string; is_active?: boolean }) => {
    const { data } = await api.get<Employee[]>('/employees/', { params });
    return data;
  },

  create: async (payload: CreateEmployeePayload): Promise<Employee> => {
    const { data } = await api.post<Employee>('/employees/', payload);
    return data;
  },

  get: async (id: string): Promise<Employee> => {
    const { data } = await api.get<Employee>(`/employees/${id}`);
    return data;
  },

  update: async (id: string, payload: Partial<Employee>): Promise<Employee> => {
    const { data } = await api.put<Employee>(`/employees/${id}`, payload);
    return data;
  },

  delete: async (id: string) => {
    const { data } = await api.delete(`/employees/${id}`);
    return data;
  },

  setActive: async (id: string, is_active: boolean): Promise<Employee> => {
    const { data } = await api.post<Employee>(`/employees/${id}/activate`, { is_active });
    return data;
  },

  count: async (): Promise<{ count: number }> => {
    const { data } = await api.get<{ count: number }>('/employees/count');
    return data;
  },

  regenerateQr: async (id: string): Promise<{ qr_code_data: string; message: string }> => {
    const { data } = await api.post(`/employees/${id}/regenerate-qr`);
    return data;
  },
};
