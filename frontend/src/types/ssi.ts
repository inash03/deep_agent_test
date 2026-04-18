export interface Ssi {
  id: string
  lei: string
  currency: string
  bic: string
  account: string
  iban: string | null
  is_external: boolean
  updated_at: string
}

export interface SsiListResponse {
  items: Ssi[]
  total: number
}

export interface SsiUpdateRequest {
  bic?: string
  account?: string
  iban?: string
}
