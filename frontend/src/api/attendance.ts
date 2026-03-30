import api from './client';
import type { AttendanceRecord } from '../types/api';

interface CheckInPayload {
  qr_code_data: string;
  latitude: number;
  longitude: number;
  device_id: string;
  photo: Blob;
}

export const attendanceApi = {
  checkIn: async (payload: CheckInPayload): Promise<AttendanceRecord> => {
    const formData = new FormData();
    formData.append('qr_code_data', payload.qr_code_data);
    formData.append('latitude', String(payload.latitude));
    formData.append('longitude', String(payload.longitude));
    formData.append('device_id', payload.device_id);
    formData.append('photo', payload.photo, 'checkin.jpg');

    const { data } = await api.post<AttendanceRecord>('/attendance/check-in', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  checkOut: async (payload: CheckInPayload): Promise<AttendanceRecord> => {
    const formData = new FormData();
    formData.append('qr_code_data', payload.qr_code_data);
    formData.append('latitude', String(payload.latitude));
    formData.append('longitude', String(payload.longitude));
    formData.append('device_id', payload.device_id);
    formData.append('photo', payload.photo, 'checkout.jpg');

    const { data } = await api.post<AttendanceRecord>('/attendance/check-out', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  today: async (): Promise<AttendanceRecord[]> => {
    const { data } = await api.get<AttendanceRecord[]>('/attendance/today');
    return data;
  },
};
