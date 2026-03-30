import type { AttendanceStatus, Severity, Role } from '../../types/api';
import { getInitials } from '../../utils/helpers';

export function StatusBadge({ status }: { status: AttendanceStatus }) {
  const map = {
    ACTIVE: { label: 'On Site', cls: 'badge-success' },
    COMPLETED: { label: 'Checked Out', cls: 'badge-gray' },
    FLAGGED: { label: 'Flagged', cls: 'badge-danger' },
  };
  const { label, cls } = map[status];
  return <span className={cls + ' badge'}>{label}</span>;
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  const map = {
    low: 'badge-info',
    medium: 'badge-warning',
    high: 'badge-danger',
  };
  return <span className={map[severity] + ' badge capitalize'}>{severity}</span>;
}

export function RoleBadge({ role }: { role: Role }) {
  const map = {
    admin: 'badge-danger',
    manager: 'badge-warning',
    employee: 'badge-info',
  };
  return <span className={map[role] + ' badge capitalize'}>{role}</span>;
}

export function ActiveBadge({ active }: { active: boolean }) {
  return active
    ? <span className="badge-success badge">Active</span>
    : <span className="badge-gray badge">Inactive</span>;
}

interface AvatarProps {
  firstName: string;
  lastName: string;
  size?: 'sm' | 'md' | 'lg';
  color?: string;
}

const avatarColors = [
  '#002395', '#00A550', '#7c3aed', '#db2777', '#ea580c',
  '#0891b2', '#65a30d', '#7c3aed', '#be123c',
];

function hashColor(str: string) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (h * 31 + str.charCodeAt(i)) & 0xffffffff;
  return avatarColors[Math.abs(h) % avatarColors.length];
}

export function Avatar({ firstName, lastName, size = 'md' }: AvatarProps) {
  const s = { sm: 'w-8 h-8 text-xs', md: 'w-10 h-10 text-sm', lg: 'w-14 h-14 text-lg' }[size];
  const bg = hashColor(firstName + lastName);
  return (
    <div
      className={`${s} rounded-full flex items-center justify-center font-semibold text-white font-display shrink-0`}
      style={{ backgroundColor: bg }}
    >
      {getInitials(firstName, lastName)}
    </div>
  );
}
