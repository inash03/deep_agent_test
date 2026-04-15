export interface Counterparty {
  lei: string
  name: string
  bic: string
  is_active: boolean
}

export interface CounterpartyListResponse {
  items: Counterparty[]
  total: number
}

export interface CounterpartyUpdateRequest {
  name?: string
  bic?: string
  is_active?: boolean
}
