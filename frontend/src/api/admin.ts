import { apiClient } from './client'

export async function refreshData(): Promise<void> {
  await apiClient.post('/api/v1/admin/refresh')
}

export async function seedData(): Promise<void> {
  await apiClient.post('/api/v1/admin/seed')
}
