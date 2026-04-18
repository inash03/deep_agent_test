import { apiClient } from './client'
import type { ReferenceDataListResponse } from '../types/referenceData'

export async function listReferenceData(): Promise<ReferenceDataListResponse> {
  const { data } = await apiClient.get<ReferenceDataListResponse>('/api/v1/reference-data')
  return data
}
