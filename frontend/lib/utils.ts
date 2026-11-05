import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Salary is stored in million VND / month. */
export function formatSalary(min?: number | null, max?: number | null): string {
  if (!min && !max) return 'Thỏa thuận'
  if (min && max && min !== max) return `${min} - ${max} triệu`
  return `${min || max} triệu`
}

export function formatDate(date?: string | Date | null): string {
  if (!date) return '-'
  const d = typeof date === 'string' ? new Date(date) : date
  return new Intl.DateTimeFormat('vi-VN', { year: 'numeric', month: 'short', day: 'numeric' }).format(d)
}

export const SUPERSET_URL = process.env.NEXT_PUBLIC_SUPERSET_URL || 'http://localhost:8088'
