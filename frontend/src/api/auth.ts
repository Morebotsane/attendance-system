import api from './client';
import type { LoginResponse, User } from '../types/api';

export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const { data } = await api.post<LoginResponse>('/auth/login', {
      employee_number: username,
      password,
    });
    return data;
  },

  logout: async () => {
    await api.post('/auth/logout');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  },

  me: async (): Promise<User> => {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },

  changePassword: async (old_password: string, new_password: string) => {
    const { data } = await api.post('/auth/change-password', { old_password, new_password });
    return data;
  },
};
