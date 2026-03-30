export type Role = 'admin' | 'manager' | 'employee';
export type AttendanceStatus = 'ACTIVE' | 'COMPLETED' | 'FLAGGED';
export type FlagType = 'GEOFENCE_VIOLATION' | 'DUPLICATE_CHECKIN' | 'LATE_ARRIVAL' | 'EARLY_DEPARTURE' | 'SUSPICIOUS_PATTERN';
export type Severity = 'low' | 'medium' | 'high';

export interface User {
  id: string;
  username: string;
  email: string;
  role: Role;
  employee_number: string;
  first_name: string;
  last_name: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  employee: User;
}

export interface Department {
  id: string;
  name: string;
  code: string;
  description?: string;
  location: string;
  latitude: number;
  longitude: number;
  geofence_radius: number;
  is_active: boolean;
  created_at: string;
  employees?: Employee[];
}

export interface DepartmentStats {
  total_employees: number;
  active_today: number;
  attendance_rate: number;
  average_hours: number;
}

export interface Employee {
  id: string;
  employee_number: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  position: string;
  department_id: string | null;
  qr_code_data: string;
  is_active: boolean;
  role: Role;
  created_at: string;
  updated_at: string;
  department?: Department;
  attendance_records?: AttendanceRecord[];
}

export interface AttendanceRecord {
  id: string;
  employee_id: string;
  check_in_time: string;
  check_in_latitude: number;
  check_in_longitude: number;
  check_in_photo_url: string;
  check_in_device_id: string;
  check_out_time: string | null;
  check_out_latitude: number | null;
  check_out_longitude: number | null;
  check_out_photo_url: string | null;
  check_out_device_id: string | null;
  status: AttendanceStatus;
  validation_metadata: {
    geofence?: { valid: boolean; distance_meters: number; department_radius: number };
    qr_validation?: { valid: boolean; employee_id: string };
  };
  created_at: string;
  updated_at: string;
  employee?: Employee;
  flags?: AttendanceFlag[];
}

export interface AttendanceFlag {
  id: string;
  attendance_record_id: string | null;
  flag_type: FlagType;
  description: string;
  severity: Severity;
  is_resolved: boolean;
  resolved_by: string | null;
  resolved_at: string | null;
  resolution_notes: string | null;
  created_at: string;
}

export interface SystemStats {
  total_employees: number;
  active_employees: number;
  checked_in_today: number;
  attendance_rate_today: number;
  total_departments: number;
  open_flags: number;
}

export interface DailyReport {
  date: string;
  total_employees: number;
  checked_in: number;
  checked_out: number;
  still_active: number;
  attendance_rate: number;
  by_department: Array<{ department_name: string; checked_in: number; total: number }>;
}

export interface MonthlyReport {
  year: number;
  month: number;
  total_days: number;
  average_attendance_rate: number;
  total_hours_worked: number;
  by_day: Array<{ date: string; checked_in: number; total_employees: number }>;
}

export interface EmployeeReport {
  employee: Employee;
  period: { start_date: string; end_date: string };
  total_days: number;
  days_attended: number;
  attendance_rate: number;
  total_hours: number;
  average_hours_per_day: number;
  records: AttendanceRecord[];
}

export interface ApiError {
  detail: string;
}

export interface CreateEmployeePayload {
  employee_number: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  position: string;
  department_id: string;
  role: Role;
  password: string;
}

export interface AuditLog {
  id: string;
  employee_id: string;
  action: string;
  details: string;
  created_at: string;
  employee?: Employee;
}
