export interface Trade {
  trade_id: string
  counterparty_lei: string
  instrument_id: string
  currency: string
  amount: string
  value_date: string
  trade_date: string
  settlement_currency: string
  stp_status: string
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
