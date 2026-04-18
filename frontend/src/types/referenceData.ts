export interface ReferenceData {
  instrument_id: string
  description: string
  asset_class: string
  is_active: boolean
}

export interface ReferenceDataListResponse {
  items: ReferenceData[]
  total: number
}
