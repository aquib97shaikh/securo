import { useState, useMemo, useEffect } from 'react'
import { useLocation, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Sparkles,
  X,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  CheckCircle2,
  Zap,
  Info,
  Lightbulb,
  Command,
  Settings,
  BookOpen,
  Compass,
  HelpCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { guidance as guidanceApi } from '@/lib/api'
import { GuidanceCard } from '@/components/guidance/guidance-card'
import { useAuth } from '@/contexts/auth-context'
import { useWorkspace } from '@/contexts/workspace-context'
import { usePageInfoContext, type PageInfoData } from '@/contexts/page-info-context'
import type { GuidanceFamily, GuidanceInsight } from '@/types'

interface ContextualGuidancePanelProps {
  open: boolean
  onClose: () => void
}

interface PageContextConfig extends PageInfoData {
  families?: GuidanceFamily[]
  signalTypes?: string[]
}

const PAGE_CONTEXT_MAP: Record<string, PageContextConfig> = {
  '/': {
    title: 'Dashboard Overview',
    subtitle: 'High-level financial snapshot, liquid accounts, and net movements',
    overview:
      'The Dashboard consolidates your liquid balances, monthly income vs. expenses, category spending distribution, and upcoming bills into a unified command center.',
    howToUse: [
      'Use the Month Picker above to view historical periods or compare against prior months.',
      'Click on any Category in the spending breakdown to drill down into itemized transactions.',
      'Toggle Privacy Mode (Eye icon in sidebar) to blur sensitive currency amounts in public.',
    ],
    keyConcepts: [
      {
        term: 'Liquid Net Worth',
        definition: 'Total immediate cash across checking accounts, savings, and digital wallets.',
      },
      {
        term: 'Savings Rate %',
        definition: 'The percentage of your monthly income retained after covering all expenses.',
      },
    ],
    tips: [
      'Click the Securo logo anytime to quickly return to this dashboard.',
      'Review pace and projected month-end balance early in the month to stay on budget.',
    ],
  },
  '/transactions': {
    title: 'Transactions Ledger',
    subtitle: 'Account movements, categorization, and merchant tracking',
    overview:
      'The central ledger of all money movements. Supports multi-category splits, payee renaming rules, and attachments.',
    howToUse: [
      'Filter transactions by account, category, or date range.',
      'Use split transactions to divide a single purchase across multiple categories or shared groups.',
      'Switch between List and Calendar views using the view buttons in the top right.',
      'Press ⌘K or Ctrl+K to jump to any account or payee instantly.',
    ],
    keyConcepts: [
      {
        term: 'Split Transaction',
        definition: 'Divides a single receipt across multiple categories or shared group members.',
      },
      {
        term: 'Pending vs Cleared',
        definition: 'Pending rows represent authorizations; cleared are verified settled movements.',
      },
    ],
    tips: [
      'Regularly review unassigned categories to keep your reports and budgets accurate.',
      'Set up Automation Rules to categorize recurring merchants automatically.',
    ],
    families: ['habit_correction'],
    signalTypes: ['statistical_spending_anomaly'],
  },
  '/transactions?view=calendar': {
    title: 'Transactions Calendar',
    subtitle: 'Daily net cashflow rhythm and billing clusters',
    overview:
      'Visualizes your spending cadence day by day across the calendar month. Green bubbles denote positive net inflows; red bubbles denote net outflows.',
    howToUse: [
      'Click any calendar date to filter the transactions list specifically for that day.',
      'Scan the calendar to identify peak billing clusters where multiple debits hit together.',
      'Use the month switcher to plan for upcoming heavy expenditure cycles.',
    ],
    keyConcepts: [
      {
        term: 'Daily Net Flow',
        definition: 'Total income received minus total expenses incurred on that specific calendar day.',
      },
    ],
    tips: [
      'Pay special attention to days preceding payroll when account balances are lowest.',
      'Hover over any calendar cell to see daily transaction counts and totals.',
    ],
    families: ['habit_correction'],
    signalTypes: ['statistical_spending_anomaly'],
  },
  '/accounts': {
    title: 'Accounts & Wallets',
    subtitle: 'Liquid balances, bank connections, and account types',
    overview:
      'Manage all liquid depositories: checking, savings, credit cards, and cash wallets.',
    howToUse: [
      'Keep checking and savings accounts reconciled with your bank statements.',
      'Group accounts into Collections for separate personal, business, or household tracking.',
      'Click any account card to view historical balance charts and account-specific transactions.',
    ],
    keyConcepts: [
      {
        term: 'Collections',
        definition: 'Logical account clusters that filter your entire workspace view into business, personal, or joint scopes.',
      },
      {
        term: 'Reconciliation',
        definition: 'Verifying recorded balances against your actual bank statement to ensure zero discrepancy.',
      },
    ],
    tips: [
      'Maintain an operational buffer in checking accounts to absorb automatic debit timing variances.',
    ],
  },
  '/budgets': {
    title: 'Budgets & Spending Limits',
    subtitle: 'Category caps, overspend pacing, and guardrails',
    overview:
      'Establishes guardrails on variable spending categories to prevent end-of-month deficits before they occur.',
    howToUse: [
      'Set monthly caps for flexible categories like Groceries, Dining, and Entertainment.',
      'Monitor the pacing bar: if you spend faster than the current day of the month, the gauge warns you to slow down.',
      'Use 1-click remedies from Smart Insights to reallocate surplus from under-spent categories.',
    ],
    keyConcepts: [
      {
        term: 'Pacing Bar',
        definition: 'Compares your percentage of budget spent against the percentage of the calendar month elapsed.',
      },
      {
        term: 'Rollover Cap',
        definition: 'Carrying forward unused surplus or deficits into the subsequent month.',
      },
    ],
    tips: [
      'Review pace mid-month to prevent end-of-month budget shortfalls.',
      'Recurring budgets carry forward automatically each month.',
    ],
    families: ['budget_control'],
  },
  '/recurring': {
    title: 'Recurring Bills & Subscriptions',
    subtitle: 'Fixed payments, price increases, and upcoming billing clusters',
    overview:
      'Monitors regular recurring bills, streaming subscriptions, utilities, and memberships to identify price increases and prevent overdrafts.',
    howToUse: [
      'Confirm recurring series identified from your transaction history.',
      'Check upcoming renewal clusters to ensure checking accounts have sufficient liquid funds.',
      'Spot price creep alerts flagging when a subscription charges more than its historical average.',
    ],
    keyConcepts: [
      {
        term: 'Price Creep',
        definition: 'Gradual, unannounced price increases on recurring services.',
      },
      {
        term: 'Bill Clustering',
        definition: 'Multiple large recurring charges landing within a narrow 3-day window.',
      },
    ],
    tips: [
      'Cancel neglected subscriptions directly from this view.',
      'Upcoming bill clusters warn you ahead of low-cash periods.',
    ],
    families: ['recurring_optimization', 'cash_flow_safety'],
  },
  '/goals': {
    title: 'Savings & Debt Goals',
    subtitle: 'Target amounts, target dates, and progress pacing',
    overview:
      'Helps you plan and fund long-term financial milestones such as emergency reserves, down payments, or debt payoff.',
    howToUse: [
      'Create a goal with a target amount and target completion date.',
      'Review the required monthly contribution pace calculated automatically.',
      'Link specific accounts to goals to automatically track accumulated funds.',
    ],
    keyConcepts: [
      {
        term: 'Required Monthly Pace',
        definition: 'The exact amount you need to save each month to achieve your milestone on schedule.',
      },
      {
        term: 'Emergency Runway',
        definition: 'A liquid reserve covering 3–6 months of essential living expenses.',
      },
    ],
    tips: [
      'Define a monthly contribution pace to reach targets on schedule.',
      'Reallocate budget surpluses directly toward high-priority savings milestones.',
    ],
    families: ['goal_recovery'],
  },
  '/reports': {
    title: 'Financial Reports & Analytics',
    subtitle: 'Income vs. expense trends, category distribution, and net worth',
    overview:
      'Comprehensive financial analytics illustrating income sources, expense distribution, and historical net worth progression.',
    howToUse: [
      'Inspect the Sankey diagram to trace the flow of funds from gross income through accounts into spending categories.',
      'Examine 90-day spending drift to identify lifestyle creep.',
      'Track total assets versus liabilities over time to confirm net worth growth.',
    ],
    keyConcepts: [
      {
        term: 'Sankey Diagram',
        definition: 'A flow chart visualizing where every dollar goes from earnings into specific expenses.',
      },
      {
        term: 'Net Worth Trajectory',
        definition: 'Total asset valuation minus outstanding debts and credit balances.',
      },
    ],
    tips: [
      'Compare discretionary expenses against fixed recurring obligations.',
      'Use the 12-month trend to smooth out quarterly tax payments and seasonal spikes.',
    ],
    families: ['budget_control', 'goal_recovery'],
  },
  '/planning': {
    title: 'Cash-Flow Runway & Scenarios',
    subtitle: 'Day-by-day liquid account forecasting',
    overview:
      'Projects future cash balances across your checking and savings accounts by combining confirmed recurring bills with active monthly budget caps.',
    howToUse: [
      '1. Select Forecast Horizon: Choose between 3, 6, 12, or 24 months forward.',
      '2. Scope by Account: Inspect a specific liquid account (checking/savings) or view consolidated cash.',
      '3. Test What-If Scenarios: Use the Income, Expense, and Extra Savings sliders to simulate real-world financial shifts.',
      '4. Review Shortfall Alerts: Red badges pinpoint the exact date when balances dip below your safety buffer.',
    ],
    keyConcepts: [
      {
        term: 'Safety Buffer',
        definition: 'A designated cash reserve floor you aim to never breach.',
      },
      {
        term: 'What-If Sliders',
        definition: 'Immediate stress-test multipliers that test income or expense shocks without altering ledger records.',
      },
    ],
    tips: [
      'Maintain at least 1 month of fixed recurring obligations as your safety buffer.',
      'If a deficit is flagged, adjust category caps or reschedule discretionary bills before the shortfall date.',
    ],
    families: ['cash_flow_safety'],
  },
  '/planning?tab=monte_carlo': {
    title: 'Monte Carlo Simulation Guide',
    subtitle: 'Probabilistic wealth & runway modeling',
    overview:
      'Unlike naive linear projections that assume constant investment returns, Monte Carlo simulation generates 1,000 randomized market futures with realistic sequence-of-returns volatility and compounding variations.',
    howToUse: [
      '1. Configure Investment Pots: Set current balances, target returns, and volatility (or select presets such as Aggressive, Growth, Balanced, or Cash Reserves).',
      '2. Set Planning Horizon: Define your timeframe (e.g. 5, 10, 20, or 30 years) and recurring contributions.',
      '3. Add Spending Phases: Model future lifestyle drawdowns (such as retirement living costs or a sabbatical).',
      '4. Run Simulation: Click "Run Simulation" to generate randomized trajectories and inspect the percentile fan chart.',
    ],
    keyConcepts: [
      {
        term: 'P50 (Median Expected)',
        definition: 'The middle scenario: exactly 50% of simulated market futures performed better, and 50% performed worse.',
      },
      {
        term: 'P10 (Stress-Test / Conservative)',
        definition: 'Severe downside scenario where 90% of simulations performed better. Critical for confirming whether your retirement or emergency buffer survives bear markets.',
      },
      {
        term: 'P90 (Bull Market Tailwinds)',
        definition: 'Top 10% optimistic outcome representing strong compounding and favorable market conditions.',
      },
      {
        term: 'Ruin Probability',
        definition: 'The percentage of simulated futures that depleted cash before reaching the end of your horizon. Aim to keep this below 5% for essential lifestyle needs.',
      },
    ],
    tips: [
      'Keep at least 2–3 years of living costs in cash or short-term reserves to protect against sequence-of-returns risk in early retirement.',
      'If ruin probability is higher than desired, test reducing discretionary spending or extending contributions by 1–2 years.',
      'Use the Conservative or Balanced preset for funds needed within the next 3 to 7 years.',
    ],
    families: ['cash_flow_safety'],
  },
  '/assets': {
    title: 'Asset Portfolio',
    subtitle: 'Investments, property, vehicles, and precious metals',
    overview:
      'Tracks non-liquid assets alongside cash accounts to compute true total net worth. Includes real-time gold karat rate calculations and investment balances.',
    howToUse: [
      'Add property, vehicles, or physical gold assets with purchase values and current valuations.',
      'Update valuation baselines periodically to keep net worth charts accurate.',
    ],
    keyConcepts: [
      {
        term: 'Appreciation / Depreciation',
        definition: 'The change in market value of physical or capital assets over time.',
      },
    ],
    tips: [
      'Track net asset value changes alongside liquid cash accounts.',
      'Update valuation baselines periodically for accurate net worth reporting.',
    ],
  },
  '/payees': {
    title: 'Payees & Merchants',
    subtitle: 'Merchant concentration, spending frequencies, and average tickets',
    overview:
      'Analyzes where your funds concentrate across vendors and merchants.',
    howToUse: [
      'Merge duplicate payee records to keep spending analytics clean.',
      'Review merchant concentration to identify dominant household vendors.',
    ],
    tips: [
      'Clean up and merge duplicate payee records for cleaner transaction histories.',
      'Inspect which merchants consume the largest share of your budget.',
    ],
  },
  '/rules': {
    title: 'Automation Rules',
    subtitle: 'Automatic categorization and description renaming',
    overview:
      'Rules automatically clean up imported statements by assigning categories, tags, or clean merchant names based on customizable conditions.',
    howToUse: [
      'Create rules based on description keywords or amount conditions.',
      'Automate repetitive bank statement transaction classification.',
    ],
    tips: [
      'Order rules logically: specific merchant rules before broader keyword matches.',
    ],
  },
  '/import': {
    title: 'Statement Import',
    subtitle: 'Upload CSV, OFX, or QIF bank statements',
    overview:
      'Upload bank statements to import transactions in bulk with automated duplicate detection and column mapping.',
    howToUse: [
      'Map columns carefully during preview to ensure correct date and amount parsing.',
      'Duplicate transactions are automatically detected and flagged.',
    ],
    tips: [
      'Preview before committing to ensure credit and debit signs are mapped accurately.',
    ],
  },
  '/workspace/settings': {
    title: 'Workspace Settings',
    subtitle: 'Workspace details, team members, and feature customization',
    overview:
      'Manage your workspace identity, invite collaborators, and toggle optional features and granular sub-features.',
    howToUse: [
      'Fine-tune sub-features (Monte Carlo, Runway projections, Copilot advice, 1-Click remedies) to keep your interface clean.',
      'Invite team members or household partners with Owner, Editor, or Viewer roles.',
      'Configure default currency, locale, and backup targets.',
    ],
    tips: [
      'Enable or disable optional features like Guidance or Planning to match your workflow.',
      'Invite collaborators with tailored roles (Owner, Editor, Viewer).',
    ],
  },
}

const DEFAULT_CONTEXT: PageContextConfig = {
  title: 'Page Information',
  subtitle: 'Contextual tips, navigation, and keyboard shortcuts',
  overview:
    'Use this information panel to discover key features, workflows, and keyboard shortcuts for any screen.',
  howToUse: [
    'Use the left sidebar to navigate across accounts, budgets, and analysis.',
    'Press ⌘K or Ctrl+K to open the Command Palette from anywhere.',
    'Press ⌘G or Ctrl+G to toggle this information panel on any page.',
  ],
  tips: [
    'Use the left sidebar to navigate across accounts, budgets, and analysis.',
    'Press ⌘K or Ctrl+K to open the Command Palette from anywhere.',
  ],
}

export function ContextualGuidancePanel({ open, onClose }: ContextualGuidancePanelProps) {
  const location = useLocation()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const { hasModule } = useWorkspace()

  // Guidance feature enabled check
  const guidanceEnabled = hasModule('guidance') && user?.preferences?.guidance_copilot_panel !== false

  const [activeTab, setActiveTab] = useState<'guidance' | 'guide'>('guide')
  const [scope, setScope] = useState<'contextual' | 'all'>('contextual')
  const [showSecondary, setShowSecondary] = useState(false)

  const { pageInfo: customPageInfo } = usePageInfoContext()

  // Find best matching context (custom published by visible component, URL query match, or route match)
  const activeContext: PageContextConfig = useMemo(() => {
    if (customPageInfo) {
      return {
        ...customPageInfo,
        families: PAGE_CONTEXT_MAP[location.pathname]?.families,
        signalTypes: PAGE_CONTEXT_MAP[location.pathname]?.signalTypes,
      }
    }

    const searchParams = new URLSearchParams(location.search)
    if (location.pathname === '/planning') {
      const tab = searchParams.get('tab')
      if (tab === 'monte_carlo') {
        return PAGE_CONTEXT_MAP['/planning?tab=monte_carlo'] || PAGE_CONTEXT_MAP['/planning']
      }
    }
    if (location.pathname === '/transactions') {
      const view = searchParams.get('view')
      if (view === 'calendar') {
        return PAGE_CONTEXT_MAP['/transactions?view=calendar'] || PAGE_CONTEXT_MAP['/transactions']
      }
    }

    const directMatch = PAGE_CONTEXT_MAP[location.pathname]
    if (directMatch) return directMatch
    const basePrefix = Object.keys(PAGE_CONTEXT_MAP).find(
      (k) => k !== '/' && location.pathname.startsWith(k)
    )
    return basePrefix ? PAGE_CONTEXT_MAP[basePrefix] : DEFAULT_CONTEXT
  }, [customPageInfo, location.pathname, location.search])

  const { data: guidanceData, isLoading: isGuidanceLoading } = useQuery({
    queryKey: ['guidance-insights'],
    queryFn: () => guidanceApi.getGuidance(),
    staleTime: 1000 * 60 * 3,
    enabled: guidanceEnabled,
  })

  // Feedback mutations (snooze, dismiss, rating)
  const feedbackMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) =>
      guidanceApi.submitFeedback(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guidance-insights'] })
    },
  })

  // 1-Click Action execution mutation
  const actionMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) =>
      guidanceApi.applyAction(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guidance-insights'] })
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['recurring'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] })
    },
  })

  const allInsights = guidanceData?.insights || []

  // Filter insights according to active page context or 'all'
  const contextualInsights = useMemo(() => {
    if (!activeContext || scope === 'all') {
      return allInsights
    }
    return allInsights.filter((ins) => {
      if (activeContext.families && activeContext.families.includes(ins.family)) {
        return true
      }
      if (activeContext.signalTypes && activeContext.signalTypes.includes(ins.signal_type)) {
        return true
      }
      return false
    })
  }, [allInsights, activeContext, scope])

  // Top 1 high conviction action (score >= 60)
  const highConvictionInsights = useMemo(() => {
    return contextualInsights.filter((ins) => ins.score >= 60.0)
  }, [contextualInsights])

  const primaryAction: GuidanceInsight | undefined = highConvictionInsights[0]
  const secondaryInsights = useMemo(() => {
    if (scope === 'all') {
      return allInsights.filter((i) => i.id !== primaryAction?.id)
    }
    return contextualInsights.filter((i) => i.id !== primaryAction?.id)
  }, [allInsights, contextualInsights, primaryAction, scope])

  const hasInsights = guidanceEnabled && contextualInsights.length > 0

  // If there are insights, default to guidance tab; if none, default to page guide and tips
  useEffect(() => {
    if (hasInsights) {
      setActiveTab('guidance')
    } else {
      setActiveTab('guide')
    }
  }, [hasInsights, location.pathname])

  // Reset state on route change
  useEffect(() => {
    if (activeContext) {
      setScope('contextual')
    } else {
      setScope('all')
    }
    setShowSecondary(false)
  }, [location.pathname, activeContext])

  // Esc key dismisses drawer
  useEffect(() => {
    if (!open) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, onClose])

  const handleExecuteAction = async (insight: GuidanceInsight) => {
    const payload = {
      action_type: insight.action?.type || 'executed',
      ...(insight.action?.payload || {}),
    }
    return await actionMutation.mutateAsync({ id: insight.id, payload })
  }

  const handleSnooze = (id: string, days = 30) => {
    feedbackMutation.mutate({
      id,
      payload: { status: 'snoozed', snooze_days: days, is_helpful: true },
    })
  }

  const handleDismiss = (id: string) => {
    feedbackMutation.mutate({
      id,
      payload: { status: 'dismissed', is_helpful: false },
    })
  }

  const isMac =
    typeof navigator !== 'undefined' &&
    /Mac|iPhone|iPad|iPod/.test(navigator.platform)

  if (!open) return null

  return (
    <div className="fixed inset-0 z-40 overflow-hidden pointer-events-none">
      {/* Mobile-only backdrop so phones can tap outside to dismiss; omitted on desktop so main UI remains 100% usable */}
      <div
        className="fixed inset-0 bg-black/20 transition-opacity animate-in fade-in-50 duration-150 sm:hidden pointer-events-auto"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Slide-over Companion panel on the right — pointer-events-auto keeps panel interactive without blocking main UI */}
      <aside
        className="fixed top-0 right-0 bottom-0 w-full sm:w-[420px] bg-sidebar border-l border-sidebar-border shadow-xl flex flex-col z-40 animate-in slide-in-from-right duration-200 pointer-events-auto"
        aria-label="Contextual Information & Guidance Panel"
      >
        {/* Panel Header */}
        <div className="p-4 sm:p-5 border-b border-sidebar-border bg-sidebar shrink-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
                <Info size={17} />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-sidebar-foreground">
                  {activeContext.title}
                </h3>
                <p className="text-xs text-sidebar-muted line-clamp-1">
                  {activeContext.subtitle}
                </p>
              </div>
            </div>

            {/* Right-aligned Close Button */}
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0 text-sidebar-muted hover:text-sidebar-foreground"
              aria-label="Close panel (Esc)"
              title="Close panel (Esc)"
            >
              <X size={18} />
            </Button>
          </div>

          {/* If Guidance is enabled AND there are active insights, show Tab Switcher */}
          {hasInsights ? (
            <div className="flex items-center rounded-lg bg-sidebar-accent/50 p-0.5 mt-3 text-xs">
              <button
                type="button"
                onClick={() => setActiveTab('guidance')}
                className={`flex-1 py-1.5 px-2 rounded-md font-medium transition-all flex items-center justify-center gap-1.5 ${
                  activeTab === 'guidance'
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-sidebar-muted hover:text-sidebar-foreground'
                }`}
              >
                <Sparkles size={13} className={activeTab === 'guidance' ? 'text-primary' : ''} />
                <span>Smart Insights</span>
                <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-primary/10 text-primary font-semibold">
                  {contextualInsights.length}
                </span>
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('guide')}
                className={`flex-1 py-1.5 px-2 rounded-md font-medium transition-all flex items-center justify-center gap-1.5 ${
                  activeTab === 'guide'
                    ? 'bg-card text-foreground shadow-sm'
                    : 'text-sidebar-muted hover:text-sidebar-foreground'
                }`}
              >
                <BookOpen size={13} />
                <span>Page Guide & Tips</span>
              </button>
            </div>
          ) : null}
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-5 space-y-5">
          {/* Tab 1: Smart Guidance (only if hasInsights AND activeTab === 'guidance') */}
          {hasInsights && activeTab === 'guidance' ? (
            <>
              {isGuidanceLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-32 w-full rounded-xl" />
                  <Skeleton className="h-24 w-full rounded-xl" />
                </div>
              ) : primaryAction ? (
                <div className="space-y-4">
                  {/* Single High-Conviction Action Header Badge */}
                  <div className="flex items-center justify-between gap-2 px-1">
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-primary">
                      <Zap size={13} className="fill-primary" />
                      Top Recommended Action
                    </span>
                    <span className="text-[11px] text-muted-foreground">1-Click Execution</span>
                  </div>

                  <GuidanceCard
                    insight={primaryAction}
                    onSnooze={handleSnooze}
                    onDismiss={handleDismiss}
                    onRate={(id, helpful) =>
                      feedbackMutation.mutate({ id, payload: { is_helpful: helpful } })
                    }
                    onExecuteAction={handleExecuteAction}
                  />

                  {/* Secondary observations collapsed */}
                  {secondaryInsights.length > 0 && (
                    <div className="pt-2 border-t border-sidebar-border">
                      <button
                        type="button"
                        onClick={() => setShowSecondary(!showSecondary)}
                        className="w-full flex items-center justify-between p-2.5 rounded-lg bg-sidebar-accent/40 hover:bg-sidebar-accent text-xs font-medium text-sidebar-foreground transition-colors"
                      >
                        <span>Other observations on this page ({secondaryInsights.length})</span>
                        {showSecondary ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </button>

                      {showSecondary && (
                        <div className="mt-3 space-y-3 pl-1 animate-in fade-in-50 duration-150">
                          {secondaryInsights.map((ins) => (
                            <GuidanceCard
                              key={ins.id}
                              insight={ins}
                              compact
                              onSnooze={handleSnooze}
                              onDismiss={handleDismiss}
                              onRate={(id, helpful) =>
                                feedbackMutation.mutate({ id, payload: { is_helpful: helpful } })
                              }
                              onExecuteAction={handleExecuteAction}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 px-3">
                  <div className="h-10 w-10 rounded-full bg-emerald-500/10 text-emerald-600 flex items-center justify-center mx-auto mb-2.5">
                    <CheckCircle2 size={20} />
                  </div>
                  <h4 className="text-xs font-semibold text-sidebar-foreground">All clear on this page!</h4>
                  <p className="text-[11px] text-sidebar-muted mt-1 max-w-xs mx-auto">
                    No urgent actions needed for this view. Spending and pacing are within healthy thresholds.
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setActiveTab('guide')}
                    className="mt-3 text-xs h-7"
                  >
                    View page guide & tips
                  </Button>
                </div>
              )}
            </>
          ) : (
            /* Tab 2: General Page Guide & Tips */
            <div className="space-y-5">
              {/* 1. About this View / Overview */}
              {activeContext.overview && (
                <div className="p-3 rounded-xl bg-sidebar-accent/30 border border-sidebar-border/60 space-y-1.5">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-sidebar-foreground">
                    <Compass size={14} className="text-primary" />
                    <span>About this View</span>
                  </div>
                  <p className="text-xs text-sidebar-muted leading-relaxed">
                    {activeContext.overview}
                  </p>
                </div>
              )}

              {/* 2. How to Use It (Step-by-Step) */}
              {activeContext.howToUse && activeContext.howToUse.length > 0 && (
                <div className="space-y-2.5">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-sidebar-foreground">
                    <BookOpen size={14} className="text-primary" />
                    <span>How to Use It</span>
                  </div>
                  <div className="space-y-2">
                    {activeContext.howToUse.map((step, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg bg-sidebar-accent/40 border border-sidebar-border text-xs text-sidebar-foreground leading-relaxed flex items-start gap-2.5"
                      >
                        <span className="flex items-center justify-center h-4 w-4 rounded-full bg-primary/15 text-primary text-[10px] font-bold shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <span className="flex-1">{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 3. Key Concepts Explained */}
              {activeContext.keyConcepts && activeContext.keyConcepts.length > 0 && (
                <div className="space-y-2.5">
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-sidebar-foreground">
                    <HelpCircle size={14} className="text-blue-500" />
                    <span>Key Concepts</span>
                  </div>
                  <div className="space-y-2">
                    {activeContext.keyConcepts.map((concept, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg bg-sidebar-accent/20 border border-sidebar-border/60 text-xs space-y-1"
                      >
                        <div className="font-semibold text-sidebar-foreground text-[11.5px] flex items-center gap-1.5">
                          <span className="h-1.5 w-1.5 rounded-full bg-blue-500 shrink-0" />
                          {concept.term}
                        </div>
                        <p className="text-[11px] text-sidebar-muted leading-relaxed pl-3">
                          {concept.definition}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 4. Pro Tips for this View */}
              {activeContext.tips && activeContext.tips.length > 0 && (
                <div>
                  <div className="flex items-center gap-1.5 text-xs font-semibold text-sidebar-foreground mb-2.5">
                    <Lightbulb size={14} className="text-amber-500" />
                    <span>Pro Tips</span>
                  </div>
                  <div className="space-y-2">
                    {activeContext.tips.map((tip, idx) => (
                      <div
                        key={idx}
                        className="p-2.5 rounded-lg bg-amber-500/5 border border-amber-500/20 text-xs text-sidebar-foreground leading-relaxed flex items-start gap-2"
                      >
                        <span className="text-amber-500 font-bold text-xs mt-0.5">•</span>
                        <span>{tip}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 5. Keyboard Shortcuts for Speed */}
              <div>
                <div className="flex items-center gap-1.5 text-xs font-semibold text-sidebar-foreground mb-2.5">
                  <Command size={14} className="text-primary" />
                  <span>Essential Shortcuts</span>
                </div>
                <div className="space-y-1.5 text-xs">
                  <div className="flex items-center justify-between p-2 rounded bg-sidebar-accent/30 border border-sidebar-border/50">
                    <span className="text-sidebar-muted text-[11px]">Command Palette & Search</span>
                    <kbd className="px-1.5 py-0.5 rounded bg-muted border border-border text-[10px] font-mono text-foreground font-semibold">
                      {isMac ? '⌘K' : 'Ctrl+K'}
                    </kbd>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded bg-sidebar-accent/30 border border-sidebar-border/50">
                    <span className="text-sidebar-muted text-[11px]">Toggle This Info Panel</span>
                    <kbd className="px-1.5 py-0.5 rounded bg-muted border border-border text-[10px] font-mono text-foreground font-semibold">
                      {isMac ? '⌘G' : 'Ctrl+G'}
                    </kbd>
                  </div>
                  <div className="flex items-center justify-between p-2 rounded bg-sidebar-accent/30 border border-sidebar-border/50">
                    <span className="text-sidebar-muted text-[11px]">Close Drawer</span>
                    <kbd className="px-1.5 py-0.5 rounded bg-muted border border-border text-[10px] font-mono text-foreground font-semibold">
                      Esc
                    </kbd>
                  </div>
                </div>
              </div>

              {/* Feature Settings Shortcut */}
              <div className="p-3 rounded-lg bg-sidebar-accent/20 border border-sidebar-border/60 text-xs">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-semibold text-sidebar-foreground flex items-center gap-1.5">
                    <Settings size={13} className="text-muted-foreground" />
                    Customize Features
                  </span>
                  <Link
                    to="/workspace/settings"
                    onClick={onClose}
                    className="text-primary hover:underline text-[11px] font-medium"
                  >
                    Open Settings →
                  </Link>
                </div>
                <p className="text-[11px] text-sidebar-muted leading-snug">
                  Toggle Guidance, Planning, or automated remedies to tailor Securo to your workflow.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 sm:p-4 border-t border-sidebar-border bg-sidebar shrink-0 flex items-center justify-between text-xs">
          <span className="text-sidebar-muted text-[11px]">Securo Finance • Privacy-first</span>
          {guidanceEnabled && (
            <Link
              to="/guidance"
              onClick={onClose}
              className="font-medium text-primary hover:text-primary/80 inline-flex items-center gap-1 transition-colors text-[11px]"
            >
              Open Guidance Inbox
              <ChevronRight size={13} />
            </Link>
          )}
        </div>
      </aside>
    </div>
  )
}
