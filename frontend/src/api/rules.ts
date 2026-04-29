import { apiClient } from './client'
import type { RuleListResponse } from '../types/rule'

export async function listRules(): Promise<RuleListResponse> {
  const { data } = await apiClient.get<RuleListResponse>('/api/v1/rules')
  return data
}
