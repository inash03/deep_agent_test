import { apiClient } from './client'
import type { Counterparty, CounterpartyListResponse, CounterpartyUpdateRequest } from '../types/counterparty'

export interface CounterpartyListParams {
  lei?: string
  name?: string
  limit?: number
  offset?: number
}

export async function listCounterparties(params: CounterpartyListParams = {}): Promise<CounterpartyListResponse> {
  const { data } = await apiClient.get<CounterpartyListResponse>('/api/v1/counterparties', { params })
  return data
}

export async function getCounterparty(lei: string): Promise<Counterparty> {
  const { data } = await apiClient.get<Counterparty>(`/api/v1/counterparties/${lei}`)
  return data
}

export async function updateCounterparty(lei: string, body: CounterpartyUpdateRequest): Promise<Counterparty> {
  const { data } = await apiClient.patch<Counterparty>(`/api/v1/counterparties/${lei}`, body)
  return data
}
