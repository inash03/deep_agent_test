import { apiClient } from './client'
import type { StpException, StpExceptionCreateRequest, StpExceptionListResponse } from '../types/stpException'

export interface StpExceptionListParams {
  status?: string
  trade_id?: string
  limit?: number
  offset?: number
}

export async function listStpExceptions(params: StpExceptionListParams = {}): Promise<StpExceptionListResponse> {
  const { data } = await apiClient.get<StpExceptionListResponse>('/api/v1/stp-exceptions', { params })
  return data
}

export async function getStpException(id: string): Promise<StpException> {
  const { data } = await apiClient.get<StpException>(`/api/v1/stp-exceptions/${id}`)
  return data
}

export async function createStpException(body: StpExceptionCreateRequest): Promise<StpException> {
  const { data } = await apiClient.post<StpException>('/api/v1/stp-exceptions', body)
  return data
}

export async function updateStpExceptionStatus(id: string, status: string): Promise<StpException> {
  const { data } = await apiClient.patch<StpException>(`/api/v1/stp-exceptions/${id}`, { status })
  return data
}
