import { apiClient } from './client'
import type { TradeEvent, TradeEventListResponse } from '../types/tradeEvent'

export async function listTradeEvents(tradeId: string): Promise<TradeEventListResponse> {
  const { data } = await apiClient.get<TradeEventListResponse>(`/api/v1/trades/${tradeId}/events`)
  return data
}

export async function createTradeEvent(
  tradeId: string,
  body: {
    event_type: 'AMEND' | 'CANCEL'
    reason: string
    requested_by: string
    amended_fields?: Record<string, unknown>
  },
): Promise<TradeEvent> {
  const { data } = await apiClient.post<TradeEvent>(`/api/v1/trades/${tradeId}/events`, body)
  return data
}

export async function foApproveEvent(eventId: string, approved: boolean): Promise<TradeEvent> {
  const { data } = await apiClient.patch<TradeEvent>(
    `/api/v1/trade-events/${eventId}/fo-approve`,
    { approved },
  )
  return data
}

export async function boApproveEvent(eventId: string, approved: boolean): Promise<TradeEvent> {
  const { data } = await apiClient.patch<TradeEvent>(
    `/api/v1/trade-events/${eventId}/bo-approve`,
    { approved },
  )
  return data
}
