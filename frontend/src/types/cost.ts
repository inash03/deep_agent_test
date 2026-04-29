export interface LlmCostLog {
  id: string
  run_id: string | null
  trade_id: string | null
  agent_type: string
  node: string
  model: string
  input_tokens: number
  output_tokens: number
  cost_usd: number
  reason: string | null
  created_at: string
}

export interface AgentCostBreakdown {
  agent_type: string
  cost_usd: number
  run_count: number
  call_count: number
}

export interface ModelCostBreakdown {
  model: string
  cost_usd: number
  call_count: number
}

export interface DailyCost {
  date: string
  cost_usd: number
  run_count: number
  call_count: number
}

export interface CostSummary {
  total_cost_usd: number
  total_input_tokens: number
  total_output_tokens: number
  total_calls: number
  total_runs: number
  by_agent: AgentCostBreakdown[]
  by_model: ModelCostBreakdown[]
  daily_costs: DailyCost[]
}

export interface CostLogListResponse {
  items: LlmCostLog[]
  total: number
}
