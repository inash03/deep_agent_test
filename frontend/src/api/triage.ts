import { apiClient } from './client'
import type { TriageHistoryResponse } from '../types/triage'

export async function getTriageHistory(limit = 20): Promise<TriageHistoryResponse> {
  const { data } = await apiClient.get<TriageHistoryResponse>('/api/v1/triage/history', { params: { limit } })
  return data
}
