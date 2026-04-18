import { apiClient } from './client'
import type { ResumeRequest, TriageHistoryResponse, TriageRequest, TriageResponse } from '../types/triage'

export async function startTriage(req: TriageRequest): Promise<TriageResponse> {
  const { data } = await apiClient.post<TriageResponse>('/api/v1/triage', req)
  return data
}

export async function resumeTriage(
  runId: string,
  req: ResumeRequest,
): Promise<TriageResponse> {
  const { data } = await apiClient.post<TriageResponse>(
    `/api/v1/triage/${runId}/resume`,
    req,
  )
  return data
}

export async function getTriageHistory(limit = 20): Promise<TriageHistoryResponse> {
  const { data } = await apiClient.get<TriageHistoryResponse>('/api/v1/triage/history', { params: { limit } })
  return data
}
