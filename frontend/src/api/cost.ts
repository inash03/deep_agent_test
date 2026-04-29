import { apiClient } from './client'
import type { CostLogListResponse, CostSummary } from '../types/cost'

export async function getCostSummary(days = 30): Promise<CostSummary> {
  const { data } = await apiClient.get<CostSummary>('/api/v1/cost/summary', { params: { days } })
  return data
}

export async function listCostLogs(limit = 100): Promise<CostLogListResponse> {
  const { data } = await apiClient.get<CostLogListResponse>('/api/v1/cost/logs', { params: { limit } })
  return data
}
