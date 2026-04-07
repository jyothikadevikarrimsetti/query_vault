import React from 'react';
import {
  Stethoscope,
  HeartPulse,
  Receipt,
  Users,
  Monitor,
  ShieldCheck,
  Microscope,
  UserX,
  Building2,
  FlaskConical,
  Hospital,
  UserCog,
} from 'lucide-react';

export const CATEGORY_ORDER = [
  'Physician',
  'Nurse',
  'Billing',
  'HR',
  'IT',
  'Compliance',
  'Research',
  'Terminated',
];

export const CATEGORY_ICON: Record<string, React.FC<{ className?: string }>> = {
  Physician: Stethoscope,
  Nurse: HeartPulse,
  Billing: Receipt,
  HR: Users,
  IT: Monitor,
  Compliance: ShieldCheck,
  Research: Microscope,
  Terminated: UserX,
};

export const CATEGORY_COLOR: Record<string, string> = {
  Physician: 'text-blue-600 dark:text-blue-400',
  Nurse: 'text-pink-600 dark:text-pink-400',
  Billing: 'text-emerald-600 dark:text-emerald-400',
  HR: 'text-purple-600 dark:text-purple-400',
  IT: 'text-orange-600 dark:text-orange-400',
  Compliance: 'text-teal-600 dark:text-teal-400',
  Research: 'text-indigo-600 dark:text-indigo-400',
  Terminated: 'text-red-600 dark:text-red-400',
};

// ── Domain grouping (for role-based views) ──────────────────

export const DOMAIN_GROUP_ORDER = ['CLINICAL', 'HIS', 'FINANCIAL', 'ADMINISTRATIVE', 'HR', 'RESEARCH', 'COMPLIANCE', 'IT_OPERATIONS'];

export const DOMAIN_GROUP_LABELS: Record<string, string> = {
  CLINICAL: 'Clinical',
  HIS: 'Hospital Information System',
  FINANCIAL: 'Financial',
  ADMINISTRATIVE: 'Administrative',
  HR: 'Human Resources',
  RESEARCH: 'Research',
  COMPLIANCE: 'Compliance',
  IT_OPERATIONS: 'IT Operations',
  '': 'Unconfigured',
};

export const DOMAIN_GROUP_COLORS: Record<string, string> = {
  CLINICAL: 'border-blue-200 dark:border-blue-800',
  HIS: 'border-cyan-200 dark:border-cyan-800',
  FINANCIAL: 'border-emerald-200 dark:border-emerald-800',
  ADMINISTRATIVE: 'border-purple-200 dark:border-purple-800',
  HR: 'border-pink-200 dark:border-pink-800',
  RESEARCH: 'border-indigo-200 dark:border-indigo-800',
  COMPLIANCE: 'border-teal-200 dark:border-teal-800',
  IT_OPERATIONS: 'border-orange-200 dark:border-orange-800',
  '': 'border-gray-200 dark:border-gray-700',
};

export const DOMAIN_GROUP_TEXT_COLORS: Record<string, string> = {
  CLINICAL: 'text-blue-600 dark:text-blue-400',
  HIS: 'text-cyan-600 dark:text-cyan-400',
  FINANCIAL: 'text-emerald-600 dark:text-emerald-400',
  ADMINISTRATIVE: 'text-purple-600 dark:text-purple-400',
  HR: 'text-pink-600 dark:text-pink-400',
  RESEARCH: 'text-indigo-600 dark:text-indigo-400',
  COMPLIANCE: 'text-teal-600 dark:text-teal-400',
  IT_OPERATIONS: 'text-orange-600 dark:text-orange-400',
  '': 'text-gray-500 dark:text-gray-400',
};

export const DOMAIN_ICON: Record<string, React.FC<{ className?: string }>> = {
  CLINICAL: Stethoscope,
  HIS: Hospital,
  FINANCIAL: Receipt,
  ADMINISTRATIVE: Building2,
  HR: UserCog,
  RESEARCH: FlaskConical,
  COMPLIANCE: ShieldCheck,
  IT_OPERATIONS: Monitor,
};

// ── Clearance badges ─────────────────────────────────────────

export const CLEARANCE_BADGE: Record<number, { label: string; color: string }> = {
  1: { label: 'L1 Public',        color: 'bg-gray-100 text-gray-600' },
  2: { label: 'L2 Internal',      color: 'bg-blue-50 text-blue-600' },
  3: { label: 'L3 Restricted',    color: 'bg-yellow-50 text-yellow-700' },
  4: { label: 'L4 Highly Conf.',  color: 'bg-blue-100 text-blue-700' },
  5: { label: 'L5 Top Secret',    color: 'bg-red-100 text-red-700' },
};
