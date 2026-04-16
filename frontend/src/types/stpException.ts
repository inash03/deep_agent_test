import type React from 'react'

export interface StpException {
  id: string
  trade_id: string
  error_message: string
  status: string
  triage_run_id: string | null
  created_at: string
  updated_at: string
}

export interface StpExceptionListResponse {
  items: StpException[]
  total: number
}

export interface StpExceptionCreateRequest {
  trade_id: string
  error_message: string
}

export type StpExceptionStatus = 'OPEN' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED'

export const EXCEPTION_STATUS_LABELS: Record<string, string> = {
  OPEN: 'Open',
  IN_PROGRESS: 'In Progress',
  RESOLVED: 'Resolved',
  CLOSED: 'Closed',
}

export const EXCEPTION_STATUS_COLORS: Record<string, React.CSSProperties> = {
  OPEN: { backgroundColor: '#fef9c3', color: '#854d0e', border: '1px solid #fde047' },
  IN_PROGRESS: { backgroundColor: '#dbeafe', color: '#1e40af', border: '1px solid #93c5fd' },
  RESOLVED: { backgroundColor: '#d1fae5', color: '#065f46', border: '1px solid #6ee7b7' },
  CLOSED: { backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db' },
}
