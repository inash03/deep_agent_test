export type TriageStatus = 'COMPLETED' | 'PENDING_APPROVAL'

export type RootCause =
  | 'MISSING_SSI'
  | 'BIC_FORMAT_ERROR'
  | 'INVALID_VALUE_DATE'
  | 'INSTRUMENT_NOT_FOUND'
  | 'COUNTERPARTY_NOT_FOUND'
  | 'UNKNOWN'

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
  pending_action_description: string | null
  diagnosis: string | null
  root_cause: RootCause | null
  recommended_action: string | null
  action_taken: boolean
  steps: StepOut[]
}

export interface TriageRequest {
  trade_id: string
  error_message: string
}

export interface ResumeRequest {
  approved: boolean
}
