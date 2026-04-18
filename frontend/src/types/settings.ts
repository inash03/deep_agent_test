export interface AppSetting {
  key: string
  value: string
  description?: string
}

export interface AppSettingListResponse {
  items: AppSetting[]
}
