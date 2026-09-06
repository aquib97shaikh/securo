export type GuidanceSeverity = 'urgent' | 'action_needed' | 'watch' | 'informational'

export type GuidanceFamily =
  | 'budget_control'
  | 'recurring_optimization'
  | 'cash_flow_safety'
  | 'goal_recovery'
  | 'habit_correction'

export interface ScoreBreakdown {
  impact: number
  urgency: number
  persistence: number
  confidence: number
  relevance: number
  total_score: number
}

export interface EvidenceTransaction {
  id: string
  date: string
  description: string
  amount: number
  category_name?: string | null
  account_name?: string | null
}

export interface EvidenceBudget {
  category_id: string
  category_name: string
  budget_amount: number
  actual_amount: number
  variance: number
  pct_used: number
}

export interface EvidenceGoal {
  goal_id: string
  name: string
  target_amount: number
  current_amount: number
  target_date?: string | null
  on_track: string
  monthly_needed: number
}

export interface EvidenceRecurring {
  recurring_id: string
  name: string
  amount: number
  frequency: string
  next_date?: string | null
  previous_amount?: number | null
  increase_pct?: number | null
}

export interface EvidenceForecastPoint {
  date: string
  projected_balance: number
  net_change: number
  events: string[]
  has_shortfall: boolean
}

export interface EvidenceData {
  transactions: EvidenceTransaction[]
  budget?: EvidenceBudget | null
  goal?: EvidenceGoal | null
  recurring?: EvidenceRecurring | null
  forecast_points: EvidenceForecastPoint[]
  metrics: Record<string, any>
}

export interface RecommendedAction {
  type: string
  label: string
  url?: string | null
  payload?: Record<string, any> | null
}

export interface GuidanceInsight {
  id: string
  signal_type: string
  family: GuidanceFamily
  severity: GuidanceSeverity
  score: number
  score_breakdown: ScoreBreakdown
  title: string
  one_line_explanation: string
  impact_amount?: number | null
  currency: string
  what_happened: string
  why_it_matters: string
  how_calculated: string
  next_action: string
  action: RecommendedAction
  evidence: EvidenceData
  created_at: string
}

export interface GuidanceSummaryStats {
  total_active: number
  urgent_count: number
  action_needed_count: number
  watch_count: number
  informational_count: number
  total_at_risk_amount: number
}

export interface CashFlowForecastStripItem {
  date: string
  day_label: string
  projected_balance: number
  net_change: number
  inflows: number
  outflows: number
  has_shortfall: boolean
  events: string[]
}

export interface MonthAtRiskItem {
  id: string
  type: 'category_overspend' | 'upcoming_bill' | 'missed_payment' | 'goal_behind' | 'cash_shortfall'
  name: string
  amount: number
  severity: 'urgent' | 'action_needed' | 'watch'
  status_label: string
  url?: string | null
}

export interface SpendingChangeItem {
  category_id: string
  category_name: string
  category_icon?: string | null
  category_color?: string | null
  current_amount: number
  baseline_amount: number
  change_pct: number
  direction: 'increase' | 'decrease'
}

export interface GuidanceResponse {
  insights: GuidanceInsight[]
  summary: GuidanceSummaryStats
  cashflow_strip: CashFlowForecastStripItem[]
  month_at_risk: MonthAtRiskItem[]
  spending_changes: SpendingChangeItem[]
  currency: string
  as_of: string
}

export interface GuidanceFeedbackPayload {
  status?: 'active' | 'snoozed' | 'dismissed'
  snooze_days?: number
  is_helpful?: boolean | null
  action_taken?: string | null
  feedback_notes?: string | null
}

export interface GuidanceHistoryItem {
  id: string
  insight_id: string
  title: string
  severity: string
  status: string
  snoozed_until?: string | null
  is_helpful?: boolean | null
  action_taken?: string | null
  created_at: string
  updated_at: string
}
