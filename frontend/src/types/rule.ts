export interface Rule {
  rule_name: string
  severity: 'error' | 'warning'
  check_type: 'FO' | 'BO'
  description: string
  is_stub: boolean
}

export interface RuleListResponse {
  fo_rules: Rule[]
  bo_rules: Rule[]
}
