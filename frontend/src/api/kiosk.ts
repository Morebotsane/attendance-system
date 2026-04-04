import api from './client';

export interface KioskDepartment {
  id: string;
  name: string;
  code: string;
  location: string;
  latitude: number;
  longitude: number;
  geofence_radius: number;
}

export interface KioskLocationsResponse {
  locations: KioskDepartment[];
  total: number;
}

export interface QueueSession {
  session_id: string;
  queue_position: number;
  status: 'ACTIVE' | 'WAITING' | 'COMPLETED' | 'EXPIRED' | 'CANCELLED';
  your_turn: boolean;
  qr_data: string | null;
  expires_at: string;
  estimated_wait_seconds: number;
  session_type: 'checkin' | 'checkout';
}

export interface KioskCurrentSession {
  session_id: string;
  qr_data: string;
  employee_name: string;
  session_type: 'checkin' | 'checkout';
  expires_at: string;
  queue_position: number;
}

export interface JoinQueuePayload {
  session_type: 'checkin' | 'checkout';
  department_id?: string;
  latitude?: number;
  longitude?: number;
}

export const kioskApi = {
  joinQueue: async (payload: JoinQueuePayload): Promise<QueueSession> => {
    const { data } = await api.post<QueueSession>('/kiosk/queue/join', payload);
    return data;
  },

  getSessionStatus: async (session_id: string): Promise<QueueSession> => {
    const { data } = await api.get<QueueSession>(`/kiosk/queue/status/${session_id}`);
    return data;
  },

  getCurrentSession: async (
    session_type: 'checkin' | 'checkout',
    department_id?: string
  ): Promise<KioskCurrentSession | null> => {
    const { data } = await api.get<KioskCurrentSession | null>(
      '/kiosk/queue/current',
      { params: { session_type, department_id } }
    );
    return data;
  },

  cancelSession: async (session_id: string): Promise<void> => {
    await api.post(`/kiosk/queue/cancel/${session_id}`);
  },

  getLocations: async (): Promise<KioskLocationsResponse> => {
    const { data } = await api.get<KioskLocationsResponse>('/kiosk/locations');
    return data;
  },
};
