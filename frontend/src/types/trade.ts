import type React from 'react'

export interface CheckResult {
  rule_name: string
  passed: boolean
  severity: string
  message: string
}

export interface CheckResultsResponse {
  trade_id: string
  workflow_status: string
  results: CheckResult[]
}

export interface Trade {
  trade_id: string
  version: number
  workflow_status: string
  is_current: boolean
  counterparty_lei: string
  instrument_id: string
  currency: string
  amount: string
  value_date: string
  trade_date: string
  settlement_currency: string
  stp_status: string
  fo_check_results?: CheckResult[]
  bo_check_results?: CheckResult[]
}

export interface TradeListResponse {
  items: Trade[]
  total: number
}

export type TradeStatus = 'NEW' | 'STP_PASSED' | 'STP_FAILED' | 'SETTLED'

export const TRADE_STATUS_LABELS: Record<string, string> = {
  NEW: 'New',
  STP_PASSED: 'STP Passed',
  STP_FAILED: 'STP Failed',
  SETTLED: 'Settled',
}

export const TRADE_STATUS_COLORS: Record<string, React.CSSProperties> = {
  NEW: { backgroundColor: '#e0f2fe', color: '#0369a1', border: '1px solid #7dd3fc' },
  STP_PASSED: { backgroundColor: '#d1fae5', color: '#065f46', border: '1px solid #6ee7b7' },
  STP_FAILED: { backgroundColor: '#fee2e2', color: '#991b1b', border: '1px solid #fca5a5' },
  SETTLED: { backgroundColor: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db' },
}

export const WORKFLOW_STATUS_LABELS: Record<string, string> = {
  Initial: 'Initial',
  FoCheck: 'FO Check',
  FoAgentToCheck: 'FO Agent Check',
  FoUserToValidate: 'FO Review',
  FoValidated: 'FO Validated',
  BoCheck: 'BO Check',
  BoAgentToCheck: 'BO Agent Check',
  BoUserToValidate: 'BO Review',
  BoValidated: 'BO Validated',
  Done: 'Done',
  Cancelled: 'Cancelled',
  EventPending: 'Event Pending',
}

export const WORKFLOW_STATUS_COLORS: Record<string, React.CSSProperties> = {
  Initial:          { backgroundColor: '#f3f4f6', color: '#6b7280',  border: '1px solid #d1d5db' },
  FoCheck:          { backgroundColor: '#e0f2fe', color: '#0369a1',  border: '1px solid #7dd3fc' },
  FoAgentToCheck:   { backgroundColor: '#dbeafe', color: '#1d4ed8',  border: '1px solid #93c5fd' },
  FoUserToValidate: { backgroundColor: '#e0e7ff', color: '#3730a3',  border: '1px solid #a5b4fc' },
  FoValidated:      { backgroundColor: '#ccfbf1', color: '#115e59',  border: '1px solid #5eead4' },
  BoCheck:          { backgroundColor: '#dcfce7', color: '#15803d',  border: '1px solid #86efac' },
  BoAgentToCheck:   { backgroundColor: '#d1fae5', color: '#065f46',  border: '1px solid #6ee7b7' },
  BoUserToValidate: { backgroundColor: '#a7f3d0', color: '#064e3b',  border: '1px solid #34d399' },
  BoValidated:      { backgroundColor: '#99f6e4', color: '#134e4a',  border: '1px solid #2dd4bf' },
  Done:             { backgroundColor: '#f3f4f6', color: '#374151',  border: '1px solid #d1d5db' },
  Cancelled:        { backgroundColor: '#fee2e2', color: '#991b1b',  border: '1px solid #fca5a5' },
  EventPending:     { backgroundColor: '#fef3c7', color: '#92400e',  border: '1px solid #fcd34d' },
}
