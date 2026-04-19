import { apiClient } from './client'
import type { CheckResultsResponse, Trade, TradeListResponse } from '../types/trade'
import type { TriageResponse } from '../types/triage'

export interface TradeListParams {
  trade_id?: string
  stp_status?: string
  workflow_status?: string
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

export async function runFoCheck(tradeId: string): Promise<CheckResultsResponse> {
  const { data } = await apiClient.post<CheckResultsResponse>(`/api/v1/trades/${tradeId}/fo-check`)
  return data
}

export async function runBoCheck(tradeId: string): Promise<CheckResultsResponse> {
  const { data } = await apiClient.post<CheckResultsResponse>(`/api/v1/trades/${tradeId}/bo-check`)
  return data
}

export async function startFoTriage(tradeId: string, errorMessage = ''): Promise<TriageResponse> {
  const { data } = await apiClient.post<TriageResponse>(`/api/v1/trades/${tradeId}/fo-triage`, {
    trade_id: tradeId,
    error_message: errorMessage,
  })
  return data
}

export async function resumeFoTriage(tradeId: string, runId: string, approved: boolean): Promise<TriageResponse> {
  const { data } = await apiClient.post<TriageResponse>(
    `/api/v1/trades/${tradeId}/fo-triage/${runId}/resume`,
    { approved },
  )
  return data
}

export async function startBoTriage(tradeId: string, errorMessage = ''): Promise<TriageResponse> {
  const { data } = await apiClient.post<TriageResponse>(`/api/v1/trades/${tradeId}/bo-triage`, {
    trade_id: tradeId,
    error_message: errorMessage,
  })
  return data
}

export async function resumeBoTriage(tradeId: string, runId: string, approved: boolean): Promise<TriageResponse> {
  const { data } = await apiClient.post<TriageResponse>(
    `/api/v1/trades/${tradeId}/bo-triage/${runId}/resume`,
    { approved },
  )
  return data
}

export interface TradeCreateRequest {
  trade_id: string
  trade_date: string   // YYYY-MM-DD
  value_date: string   // YYYY-MM-DD
  counterparty_lei: string
  instrument_id: string
  currency: string
  amount: number
}

export async function createTrade(body: TradeCreateRequest): Promise<Trade> {
  const { data } = await apiClient.post<Trade>('/api/v1/trades', body)
  return data
}
