import { apiClient } from './client'
import type { ResumeRequest, TriageRequest, TriageResponse } from '../types/triage'

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
