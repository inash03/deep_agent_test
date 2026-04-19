import { apiClient } from './client'
import type { AppSetting, AppSettingListResponse } from '../types/settings'

export async function listSettings(): Promise<AppSettingListResponse> {
  const { data } = await apiClient.get<AppSettingListResponse>('/api/v1/settings')
  return data
}

export async function updateSetting(key: string, value: string): Promise<AppSetting> {
  const { data } = await apiClient.patch<AppSetting>(`/api/v1/settings/${key}`, { value })
  return data
}
