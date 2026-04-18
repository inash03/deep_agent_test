import type React from 'react'

export interface TradeEvent {
  id: string
  trade_id: string
  from_version: number
  to_version: number
  event_type: 'AMEND' | 'CANCEL'
  workflow_status: string
  requested_by: string
  reason: string | null
  amended_fields: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface TradeEventListResponse {
  items: TradeEvent[]
  total: number
}

export const EVENT_STATUS_LABELS: Record<string, string> = {
  FoUserToValidate: 'Awaiting FO',
  FoValidated: 'Awaiting BO',
  Done: 'Done',
  Cancelled: 'Cancelled',
}

export const EVENT_STATUS_COLORS: Record<string, React.CSSProperties> = {
  FoUserToValidate: { backgroundColor: '#e0e7ff', color: '#3730a3', border: '1px solid #a5b4fc' },
  FoValidated:      { backgroundColor: '#d1fae5', color: '#065f46', border: '1px solid #6ee7b7' },
  Done:             { backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db' },
  Cancelled:        { backgroundColor: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5' },
}
