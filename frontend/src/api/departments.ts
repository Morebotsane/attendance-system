import api from './client';
import type { Department, DepartmentStats, Employee } from '../types/api';

export const departmentsApi = {
  list: async (): Promise<Department[]> => {
    const { data } = await api.get<Department[]>('/departments/');
    return data;
  },

  create: async (payload: Omit<Department, 'id' | 'created_at' | 'is_active' | 'employees'>): Promise<Department> => {
    const { data } = await api.post<Department>('/departments/', payload);
    return data;
  },

  get: async (id: string): Promise<Department> => {
    const { data } = await api.get<Department>(`/departments/${id}`);
    return data;
  },

  update: async (id: string, payload: Partial<Department>): Promise<Department> => {
    const { data } = await api.put<Department>(`/departments/${id}`, payload);
    return data;
  },

  delete: async (id: string) => {
    const { data } = await api.delete(`/departments/${id}`);
    return data;
  },

  employees: async (id: string): Promise<Employee[]> => {
    const { data } = await api.get<Employee[]>(`/departments/${id}/employees`);
    return data;
  },

  stats: async (id: string): Promise<DepartmentStats> => {
    const { data } = await api.get<DepartmentStats>(`/departments/${id}/stats`);
    return data;
  },
};
