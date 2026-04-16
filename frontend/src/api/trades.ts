import { apiClient } from './client'
import type { Trade, TradeListResponse } from '../types/trade'

export interface TradeListParams {
  trade_id?: string
  stp_status?: string
  trade_date?: string
  limit?: number
  offset?: number
}

export async function listTrades(params: TradeListParams = {}): Promise<TradeListResponse> {
  const { data } = await apiClient.get<TradeListResponse>('/api/v1/trades', { params })
  return data
}

export async function getTrade(tradeId: string): Promise<Trade> {
  const { data } = await apiClient.get<Trade>(`/api/v1/trades/${tradeId}`)
  return data
}
