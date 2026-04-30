export type TriageStatus = 'COMPLETED' | 'PENDING_APPROVAL'

export type RootCause =
  | 'MISSING_SSI'
  | 'BIC_FORMAT_ERROR'
  | 'IBAN_FORMAT_ERROR'
  | 'INVALID_VALUE_DATE'
  | 'INSTRUMENT_NOT_FOUND'
  | 'COUNTERPARTY_NOT_FOUND'
  | 'SWIFT_AC01'
  | 'SWIFT_AG01'
  | 'COMPOUND_FAILURE'
  | 'UNKNOWN'

export type PendingActionType =
  | 'register_ssi'
  | 'reactivate_counterparty'
  | 'update_ssi'
  | 'escalate'

export interface StepOut {
  step_type: 'tool_call' | 'hitl_prompt' | 'hitl_response'
  name: string
  input: Record<string, unknown>
  output: Record<string, unknown> | null
}

export interface TriageResponse {
  trade_id: string
  status: TriageStatus
  run_id: string | null
  pending_action_type: PendingActionType | null
  pending_action_description: string | null
  diagnosis: string | null
  root_cause: RootCause | null
  recommended_action: string | null
  action_taken: boolean
  agent_type?: string
  steps: StepOut[]
}

export interface TriageRequest {
  trade_id: string
  error_message: string
}

export interface ResumeRequest {
  approved: boolean
}

export interface TriageHistoryResponse {
  items: TriageResponse[]
  total: number
}
