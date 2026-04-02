import type { AttendanceStatus, Severity, Role } from '../../types/api';
import { getInitials } from '../../utils/helpers';

// StatusBadge — values match backend lowercase enum
export function StatusBadge({ status }: { status: AttendanceStatus }) {
  const map: Record<AttendanceStatus, { label: string; cls: string }> = {
    active:    { label: 'On Site',      cls: 'badge-success' },
    completed: { label: 'Checked Out',  cls: 'badge-gray'    },
    flagged:   { label: 'Flagged',      cls: 'badge-danger'  },
  };
  const { label, cls } = map[status] ?? { label: status, cls: 'badge-gray' };
  return <span className={`${cls} badge`}>{label}</span>;
}

export function SeverityBadge({ severity }: { severity: Severity }) {
  const map: Record<Severity, string> = {
    low:    'badge-info',
    medium: 'badge-warning',
    high:   'badge-danger',
  };
  return (
    <span className={`${map[severity] ?? 'badge-gray'} badge capitalize`}>
      {severity}
    </span>
  );
}

export function RoleBadge({ role }: { role: Role }) {
  const map: Record<Role, string> = {
    admin:    'badge-danger',
    manager:  'badge-warning',
    employee: 'badge-info',
  };
  return (
    <span className={`${map[role] ?? 'badge-gray'} badge capitalize`}>
      {role}
    </span>
  );
}

export function ActiveBadge({ active }: { active: boolean }) {
  return active
    ? <span className="badge-success badge">Active</span>
    : <span className="badge-gray badge">Inactive</span>;
}

// Avatar — generates coloured initials circle
const AVATAR_COLORS = [
  '#002395', '#00A550', '#7c3aed', '#db2777',
  '#ea580c', '#0891b2', '#65a30d', '#be123c',
];

function hashColor(str: string): string {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = (h * 31 + str.charCodeAt(i)) & 0xffffffff;
  }
  return AVATAR_COLORS[Math.abs(h) % AVATAR_COLORS.length];
}

interface AvatarProps {
  firstName: string;
  lastName: string;
  size?: 'sm' | 'md' | 'lg';
}

export function Avatar({ firstName, lastName, size = 'md' }: AvatarProps) {
  const sizeClass = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-14 h-14 text-lg',
  }[size];

  return (
    <div
      className={`${sizeClass} rounded-full flex items-center justify-center
        font-semibold text-white font-display shrink-0`}
      style={{ backgroundColor: hashColor(firstName + lastName) }}
    >
      {getInitials(firstName, lastName)}
    </div>
  );
}
