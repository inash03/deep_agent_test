import { apiClient } from './client'
import type { Ssi, SsiListResponse, SsiUpdateRequest } from '../types/ssi'

export async function listSsis(params?: { lei?: string; is_external?: boolean; limit?: number; offset?: number }): Promise<SsiListResponse> {
  const { data } = await apiClient.get<SsiListResponse>('/api/v1/ssis', { params })
  return data
}

export async function getSsi(id: string): Promise<Ssi> {
  const { data } = await apiClient.get<Ssi>(`/api/v1/ssis/${id}`)
  return data
}

export async function updateSsi(id: string, body: SsiUpdateRequest): Promise<Ssi> {
  const { data } = await apiClient.patch<Ssi>(`/api/v1/ssis/${id}`, body)
  return data
}
