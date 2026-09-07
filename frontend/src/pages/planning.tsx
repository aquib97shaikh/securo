import { useState, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useQuery } from '@tanstack/react-query'
import {
  Bar,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from 'recharts'
import {
  CalendarRange,
  TrendingUp,
  PiggyBank,
  ChevronDown,
  ChevronRight,
  RotateCcw,
  Target,
  Repeat,
  AlertTriangle,
  Wallet,
  ShieldAlert,
  SlidersHorizontal,
  CheckCircle2,
} from 'lucide-react'
import { planning as planningApi, accounts as accountsApi } from '@/lib/api'
import { PageHeader } from '@/components/page-header'
import { CategoryIcon } from '@/components/category-icon'
import { MonteCarloView } from '@/components/monte-carlo-view'
import { usePrivacyMode } from '@/hooks/use-privacy-mode'
import { useAuth } from '@/contexts/auth-context'
import { useDisplayLocale } from '@/hooks/use-display-locale'
import { formatCurrency, formatCompactCurrency } from '@/lib/format'
import { monthLabel } from '@/lib/month-utils'
import { SectionCard, SectionHeader } from '@/components/section-card'
import { usePageInfo } from '@/contexts/page-info-context'
import type { Account } from '@/types'

export default function PlanningPage() {
  const { t, i18n } = useTranslation()
  const { mask } = usePrivacyMode()
  const { user } = useAuth()
  const locale = useDisplayLocale()
  const userCurrency = user?.preferences?.currency_display ?? 'USD'
  const uiLocale = i18n.resolvedLanguage ?? i18n.language

  const [searchParams, setSearchParams] = useSearchParams()
  const tabParam = searchParams.get('tab')

  const forecastEnabled = user?.preferences?.planning_cashflow_forecast !== false
  const monteCarloEnabled = user?.preferences?.planning_monte_carlo !== false

  const initialTab =
    tabParam === 'monte_carlo' && monteCarloEnabled
      ? 'monte_carlo'
      : tabParam === 'forecast' && forecastEnabled
      ? 'forecast'
      : !forecastEnabled && monteCarloEnabled
      ? 'monte_carlo'
      : 'forecast'

  const [activeTab, setActiveTab] = useState<'forecast' | 'monte_carlo'>(initialTab)

  const handleTabChange = (tab: 'forecast' | 'monte_carlo') => {
    setActiveTab(tab)
    const newParams = new URLSearchParams(searchParams)
    newParams.set('tab', tab)
    setSearchParams(newParams, { replace: true })
  }

  // Publish guidance for Balance Forecast when this tab is active
  usePageInfo(
    useMemo(
      () =>
        activeTab === 'forecast'
          ? {
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
                  definition:
                    'A designated cash reserve floor you aim to never breach.',
                },
                {
                  term: 'Recurring Stream',
                  definition:
                    'Fixed obligations (rent, payroll, subscriptions) projected on their exact due dates.',
                },
                {
                  term: 'What-If Sliders',
                  definition:
                    'Immediate stress-test multipliers that test income or expense shocks without altering ledger records.',
                },
              ],
              tips: [
                'Maintain at least 1 month of fixed recurring obligations as your safety buffer.',
                'If a deficit is flagged, adjust category caps or reschedule discretionary bills before the shortfall date.',
              ],
            }
          : null,
      [activeTab],
    ),
  )

  const [horizonMonths, setHorizonMonths] = useState(6)
  const [selectedAccountId, setSelectedAccountId] = useState<string>('')
  const [forecastMode, setForecastMode] = useState<'all' | 'recurring_only' | 'budget_only'>('all')
  const [safetyBuffer, setSafetyBuffer] = useState<number>(0)
  const [expandedMonths, setExpandedMonths] = useState<Set<string>>(new Set())

  // Scenario / What-If sliders
  const [incomeMultiplier, setIncomeMultiplier] = useState(100)
  const [expenseMultiplier, setExpenseMultiplier] = useState(100)
  const [extraMonthlySavings, setExtraMonthlySavings] = useState(0)

  // Fetch accounts for account selector
  const { data: accountsList } = useQuery({
    queryKey: ['accounts-list'],
    queryFn: () => accountsApi.list(),
  })

  // Fetch expense plan and balance forecast
  const { data: plan, isLoading } = useQuery({
    queryKey: ['expense-plan', horizonMonths, selectedAccountId, forecastMode, safetyBuffer],
    queryFn: () =>
      planningApi.getExpensePlan({
        months: horizonMonths,
        account_id: selectedAccountId || undefined,
        forecast_mode: forecastMode,
        safety_buffer: safetyBuffer,
      }),
  })

  const resetScenario = () => {
    setIncomeMultiplier(100)
    setExpenseMultiplier(100)
    setExtraMonthlySavings(0)
  }

  const isScenarioActive =
    incomeMultiplier !== 100 || expenseMultiplier !== 100 || extraMonthlySavings !== 0

  // Adjusted projections based on what-if controls
  const adjustedPlan = useMemo(() => {
    if (!plan) return null

    const incFactor = (Number(incomeMultiplier) || 100) / 100
    const expFactor = (Number(expenseMultiplier) || 100) / 100
    const startBal = Number(plan.starting_balance) || 0
    const extraSavings = Number(extraMonthlySavings) || 0

    let runningSavings = 0
    let lowestBalance = startBal
    let lowestBalanceMonth: string | null = null

    const months = plan.months.map(m => {
      const adjIncome = (Number(m.projected_income) || 0) * incFactor
      const adjExpenses = (Number(m.projected_expenses) || 0) * expFactor + extraSavings
      const adjSavings = adjIncome - adjExpenses
      runningSavings += adjSavings
      const adjRunningBalance = startBal + runningSavings

      if (adjRunningBalance < lowestBalance || lowestBalanceMonth === null) {
        lowestBalance = adjRunningBalance
        lowestBalanceMonth = m.month
      }

      return {
        ...m,
        adjIncome,
        adjExpenses,
        adjSavings,
        adjCumulativeSavings: runningSavings,
        adjProjectedBalance: adjRunningBalance,
      }
    })

    const totalIncome = months.reduce((sum, m) => sum + m.adjIncome, 0)
    const totalExpenses = months.reduce((sum, m) => sum + m.adjExpenses, 0)
    const totalSavings = totalIncome - totalExpenses
    const count = Math.max(months.length, 1)
    const endingBalance = months.length > 0 ? months[months.length - 1].adjProjectedBalance : startBal

    const hasShortfall = lowestBalance < safetyBuffer
    const shortfallAmount = hasShortfall ? safetyBuffer - lowestBalance : 0

    return {
      startingBalance: startBal,
      months,
      summary: {
        startingBalance: startBal,
        endingBalance,
        lowestBalance,
        lowestBalanceMonth,
        hasShortfall,
        shortfallAmount,
        safetyBuffer,
        totalIncome,
        totalExpenses,
        totalSavings,
        avgMonthlyIncome: totalIncome / count,
        avgMonthlyExpenses: totalExpenses / count,
        avgMonthlySavings: totalSavings / count,
      },
    }
  }, [plan, incomeMultiplier, expenseMultiplier, extraMonthlySavings, safetyBuffer])

  const toggleMonthExpand = (monthKey: string) => {
    setExpandedMonths(prev => {
      const next = new Set(prev)
      if (next.has(monthKey)) next.delete(monthKey)
      else next.add(monthKey)
      return next
    })
  }

  // Prepare chart data combining Inflows, Outflows, and Running Balance
  const chartData = useMemo(() => {
    if (!adjustedPlan) return []
    return adjustedPlan.months.map(m => ({
      name: monthLabel(m.month, uiLocale),
      'Income (Inflow)': Math.round(m.adjIncome),
      'Expenses (Outflow)': Math.round(m.adjExpenses),
      'Projected Balance': Math.round(m.adjProjectedBalance),
      'Net Cash Flow': Math.round(m.adjSavings),
    }))
  }, [adjustedPlan, uiLocale])

  return (
    <div className="space-y-6">
      <PageHeader
        section={t('planning.title', 'Future Expense Planning')}
        title={
          activeTab === 'forecast'
            ? t('planning.subtitle', 'Balance Forecast & Scenario Modeling')
            : t('planning.monte_carlo_subtitle', 'Monte Carlo Retirement & Wealth Simulation')
        }
        action={
          <div className="flex items-center gap-2">
            {forecastEnabled && monteCarloEnabled && (
              <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-lg border border-border">
                <button
                  onClick={() => handleTabChange('forecast')}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                    activeTab === 'forecast'
                      ? 'bg-card text-foreground shadow-sm font-semibold'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {t('planning.tabs.forecast', 'Balance Forecast')}
                </button>
                <button
                  onClick={() => handleTabChange('monte_carlo')}
                  className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${
                    activeTab === 'monte_carlo'
                      ? 'bg-card text-foreground shadow-sm font-semibold'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {t('planning.tabs.monte_carlo', 'Monte Carlo Analysis')}
                </button>
              </div>
            )}

            {activeTab === 'forecast' && forecastEnabled && (
              <div className="hidden sm:flex items-center gap-1 bg-muted/60 p-1 rounded-lg border border-border">
                {[3, 6, 12, 24].map(m => (
                  <button
                    key={m}
                    onClick={() => setHorizonMonths(m)}
                    className={`px-2.5 py-1 text-xs font-medium rounded-md transition-all ${
                      horizonMonths === m
                        ? 'bg-card text-foreground shadow-sm font-semibold'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {m}M
                  </button>
                ))}
              </div>
            )}
          </div>
        }
      />

      {!forecastEnabled && !monteCarloEnabled ? (
        <div className="rounded-xl border border-dashed p-10 text-center space-y-3 bg-card">
          <p className="text-sm font-medium text-foreground">All planning sub-features are currently turned off.</p>
          <p className="text-xs text-muted-foreground max-w-sm mx-auto">
            Enable Balance Runway Forecasts or Monte Carlo Analysis in your Workspace Settings to view projections.
          </p>
        </div>
      ) : activeTab === 'monte_carlo' || !forecastEnabled ? (
        <MonteCarloView />
      ) : (
        <>
          {/* Forecast Scope & Filter Bar (Inspired by Actual Budget) */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Account Scope */}
        <div className="bg-card rounded-xl border border-border p-3.5 flex flex-col justify-between">
          <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5 mb-1.5">
            <Wallet size={14} className="text-primary" />
            Account Scope
          </label>
          <select
            value={selectedAccountId}
            onChange={e => setSelectedAccountId(e.target.value)}
            className="w-full bg-muted/40 border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground font-medium focus:outline-none focus:ring-1 focus:ring-primary"
          >
            <option value="">All Liquid Accounts (Checking & Savings)</option>
            {accountsList?.map((acc: Account) => (
              <option key={acc.id} value={acc.id}>
                {acc.name} ({acc.type})
              </option>
            ))}
          </select>
        </div>

        {/* Forecast Source Mode */}
        <div className="bg-card rounded-xl border border-border p-3.5 flex flex-col justify-between">
          <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5 mb-1.5">
            <SlidersHorizontal size={14} className="text-primary" />
            Forecast Source
          </label>
          <div className="flex bg-muted/40 p-0.5 rounded-lg border border-border">
            <button
              onClick={() => setForecastMode('all')}
              className={`flex-1 py-1 text-[11px] font-medium rounded transition-colors ${
                forecastMode === 'all'
                  ? 'bg-card text-foreground shadow-sm font-semibold'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              All Sources
            </button>
            <button
              onClick={() => setForecastMode('recurring_only')}
              className={`flex-1 py-1 text-[11px] font-medium rounded transition-colors ${
                forecastMode === 'recurring_only'
                  ? 'bg-card text-foreground shadow-sm font-semibold'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Schedules Only
            </button>
            <button
              onClick={() => setForecastMode('budget_only')}
              className={`flex-1 py-1 text-[11px] font-medium rounded transition-colors ${
                forecastMode === 'budget_only'
                  ? 'bg-card text-foreground shadow-sm font-semibold'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Budgets Only
            </button>
          </div>
        </div>

        {/* Safety Reserve Floor */}
        <div className="bg-card rounded-xl border border-border p-3.5 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-1.5">
            <label className="text-xs font-medium text-muted-foreground flex items-center gap-1.5">
              <ShieldAlert size={14} className="text-amber-500" />
              Safety Buffer Threshold
            </label>
            <span className="text-xs font-semibold tabular-nums text-foreground">
              {formatCurrency(safetyBuffer, userCurrency, locale)}
            </span>
          </div>
          <input
            type="number"
            min="0"
            step="100"
            value={safetyBuffer || ''}
            placeholder="0 (Minimum balance floor)"
            onChange={e => setSafetyBuffer(Math.max(0, Number(e.target.value) || 0))}
            className="w-full bg-muted/40 border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground font-medium focus:outline-none focus:ring-1 focus:ring-primary"
          />
        </div>
      </div>

      {/* Shortfall Alert Banner (Actual Budget feature) */}
      {adjustedPlan && adjustedPlan.summary.hasShortfall && (
        <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 dark:bg-amber-500/15 p-4 flex items-start gap-3">
          <AlertTriangle className="text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" size={18} />
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-amber-900 dark:text-amber-200">
              Potential Cash Shortfall Projected
            </h4>
            <p className="text-xs text-amber-800/90 dark:text-amber-300/90 mt-0.5 leading-relaxed">
              Your projected balance is expected to dip below your safety threshold in{' '}
              <strong className="underline">
                {adjustedPlan.summary.lowestBalanceMonth
                  ? monthLabel(adjustedPlan.summary.lowestBalanceMonth, uiLocale)
                  : 'the forecast period'}
              </strong>
              , reaching a low of{' '}
              <strong>{mask(formatCurrency(adjustedPlan.summary.lowestBalance, userCurrency, locale))}</strong> (
              deficit of {mask(formatCurrency(adjustedPlan.summary.shortfallAmount, userCurrency, locale))} below safety
              buffer).
            </p>
          </div>
        </div>
      )}

      {/* Scenario / What-If Controls Bar */}
      <SectionCard>
        <SectionHeader
          title="Scenario Controls (What-If Analysis)"
          subtitle="Adjust income or spending assumptions to model future financial scenarios and stress-test your balance"
          action={
            isScenarioActive ? (
              <button
                onClick={resetScenario}
                className="inline-flex items-center gap-1 text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                <RotateCcw size={13} /> Reset to Baseline
              </button>
            ) : undefined
          }
        />
        <div className="p-4 sm:p-5 grid grid-cols-1 sm:grid-cols-3 gap-6 bg-muted/20">
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <label className="font-medium text-foreground">Income Assumption</label>
              <span className="font-semibold text-primary">{incomeMultiplier}%</span>
            </div>
            <input
              type="range"
              min="50"
              max="150"
              step="5"
              value={incomeMultiplier}
              onChange={e => setIncomeMultiplier(Number(e.target.value))}
              className="w-full h-1.5 bg-border rounded-lg appearance-none cursor-pointer accent-primary"
            />
            <p className="text-[11px] text-muted-foreground">Scale projected income</p>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <label className="font-medium text-foreground">Expense Assumption</label>
              <span className="font-semibold text-rose-500">{expenseMultiplier}%</span>
            </div>
            <input
              type="range"
              min="50"
              max="150"
              step="5"
              value={expenseMultiplier}
              onChange={e => setExpenseMultiplier(Number(e.target.value))}
              className="w-full h-1.5 bg-border rounded-lg appearance-none cursor-pointer accent-rose-500"
            />
            <p className="text-[11px] text-muted-foreground">Scale projected expenses</p>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <label className="font-medium text-foreground">Extra Monthly Savings / Expense</label>
              <span className="font-semibold text-foreground">
                {formatCurrency(extraMonthlySavings, userCurrency, locale)}
              </span>
            </div>
            <input
              type="number"
              value={extraMonthlySavings || ''}
              placeholder="0"
              onChange={e => setExtraMonthlySavings(Number(e.target.value) || 0)}
              className="w-full border border-border rounded-lg px-3 py-1 text-xs bg-card text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
            />
            <p className="text-[11px] text-muted-foreground">Fixed amount added per month</p>
          </div>
        </div>
      </SectionCard>

      {/* Balance Forecast KPI Cards (Actual Budget Style) */}
      {isLoading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-24 bg-card rounded-xl border border-border animate-pulse" />
          ))}
        </div>
      ) : adjustedPlan ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Starting Balance */}
          <SectionCard>
            <div className="p-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-medium">Starting Balance</p>
                <p className="text-lg sm:text-xl font-bold text-foreground mt-1 tabular-nums">
                  {mask(formatCurrency(adjustedPlan.summary.startingBalance, userCurrency, locale))}
                </p>
                <p className="text-[11px] text-muted-foreground mt-0.5">Current liquid baseline</p>
              </div>
              <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-500">
                <Wallet size={20} />
              </div>
            </div>
          </SectionCard>

          {/* Projected Ending Balance */}
          <SectionCard>
            <div className="p-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-medium">Projected Ending Balance</p>
                <p
                  className={`text-lg sm:text-xl font-bold mt-1 tabular-nums ${
                    adjustedPlan.summary.endingBalance >= adjustedPlan.summary.startingBalance
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-foreground'
                  }`}
                >
                  {mask(formatCurrency(adjustedPlan.summary.endingBalance, userCurrency, locale))}
                </p>
                <p className="text-[11px] text-muted-foreground mt-0.5">At month {horizonMonths}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
                <PiggyBank size={20} />
              </div>
            </div>
          </SectionCard>

          {/* Lowest Projected Balance */}
          <SectionCard>
            <div className="p-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-medium">Lowest Point</p>
                <p
                  className={`text-lg sm:text-xl font-bold mt-1 tabular-nums ${
                    adjustedPlan.summary.lowestBalance < safetyBuffer
                      ? 'text-rose-600 dark:text-rose-400'
                      : 'text-emerald-600 dark:text-emerald-400'
                  }`}
                >
                  {mask(formatCurrency(adjustedPlan.summary.lowestBalance, userCurrency, locale))}
                </p>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  {adjustedPlan.summary.lowestBalanceMonth
                    ? monthLabel(adjustedPlan.summary.lowestBalanceMonth, uiLocale)
                    : 'Safe buffer'}
                </p>
              </div>
              <div
                className={`p-2.5 rounded-lg ${
                  adjustedPlan.summary.lowestBalance < safetyBuffer
                    ? 'bg-rose-500/10 text-rose-500'
                    : 'bg-emerald-500/10 text-emerald-500'
                }`}
              >
                {adjustedPlan.summary.lowestBalance < safetyBuffer ? (
                  <AlertTriangle size={20} />
                ) : (
                  <CheckCircle2 size={20} />
                )}
              </div>
            </div>
          </SectionCard>

          {/* Projected Net Cash Flow */}
          <SectionCard>
            <div className="p-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground font-medium">Net Cash Flow</p>
                <p
                  className={`text-lg sm:text-xl font-bold mt-1 tabular-nums ${
                    adjustedPlan.summary.totalSavings >= 0
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : 'text-rose-600 dark:text-rose-400'
                  }`}
                >
                  {adjustedPlan.summary.totalSavings >= 0 ? '+' : ''}
                  {mask(formatCurrency(adjustedPlan.summary.totalSavings, userCurrency, locale))}
                </p>
                <p className="text-[11px] text-muted-foreground mt-0.5">
                  ~{mask(formatCurrency(adjustedPlan.summary.avgMonthlySavings, userCurrency, locale))}/mo
                </p>
              </div>
              <div className="p-2.5 rounded-lg bg-emerald-500/10 text-emerald-500">
                <TrendingUp size={20} />
              </div>
            </div>
          </SectionCard>
        </div>
      ) : null}

      {/* Balance Forecast Timeline Chart */}
      <SectionCard>
        <SectionHeader
          title="Balance Forecast & Cash Flow Trajectory"
          subtitle={`Running account balance combined with monthly inflows and outflows over ${horizonMonths} months`}
        />
        <div className="p-4 sm:p-5 h-80">
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} margin={{ top: 10, right: 15, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-border" />
                <XAxis dataKey="name" tickLine={false} axisLine={false} className="text-[11px] fill-muted-foreground" />
                <YAxis
                  yAxisId="balance"
                  orientation="left"
                  tickLine={false}
                  axisLine={false}
                  className="text-[11px] fill-muted-foreground"
                  tickFormatter={val => formatCompactCurrency(val, userCurrency, locale)}
                />
                <YAxis
                  yAxisId="flow"
                  orientation="right"
                  tickLine={false}
                  axisLine={false}
                  className="text-[11px] fill-muted-foreground"
                  tickFormatter={val => formatCompactCurrency(val, userCurrency, locale)}
                />
                <Tooltip
                  formatter={(val: any, name: any) => [
                    mask(formatCurrency(Number(val ?? 0), userCurrency, locale)),
                    String(name ?? ''),
                  ]}
                  contentStyle={{
                    backgroundColor: 'var(--card)',
                    borderColor: 'var(--border)',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                />
                <Legend wrapperStyle={{ paddingTop: '10px', fontSize: '12px' }} />
                {safetyBuffer > 0 && (
                  <ReferenceLine
                    yAxisId="balance"
                    y={safetyBuffer}
                    stroke="#F59E0B"
                    strokeDasharray="4 4"
                    label={{
                      value: `Safety Buffer (${formatCompactCurrency(safetyBuffer, userCurrency, locale)})`,
                      fill: '#F59E0B',
                      fontSize: 10,
                      position: 'insideBottomRight',
                    }}
                  />
                )}
                <Bar yAxisId="flow" dataKey="Income (Inflow)" fill="#10B981" radius={[4, 4, 0, 0]} maxBarSize={28} />
                <Bar yAxisId="flow" dataKey="Expenses (Outflow)" fill="#F43F5E" radius={[4, 4, 0, 0]} maxBarSize={28} />
                <Line
                  yAxisId="balance"
                  type="monotone"
                  dataKey="Projected Balance"
                  stroke="#3B82F6"
                  strokeWidth={3}
                  dot={{ r: 4, strokeWidth: 2, fill: '#3B82F6' }}
                  activeDot={{ r: 6 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
              No projection data available
            </div>
          )}
        </div>
      </SectionCard>

      {/* Month-by-Month Expandable Table */}
      <SectionCard>
        <SectionHeader
          title="Monthly Schedule & Allocation Breakdown"
          subtitle="Click a month to inspect scheduled bills, category budget allocations, and goal contributions"
        />
        {adjustedPlan && adjustedPlan.months.length > 0 ? (
          <div className="divide-y divide-border">
            {adjustedPlan.months.map(m => {
              const isExpanded = expandedMonths.has(m.month)
              const titleMonth = monthLabel(m.month, uiLocale).replace(/^\w/, c => c.toUpperCase())

              return (
                <div key={m.month} className="transition-colors">
                  {/* Summary Row */}
                  <button
                    onClick={() => toggleMonthExpand(m.month)}
                    className="w-full px-4 sm:px-5 py-3.5 flex items-center justify-between hover:bg-muted/40 transition-colors text-left"
                  >
                    <div className="flex items-center gap-3">
                      {isExpanded ? (
                        <ChevronDown size={16} className="text-muted-foreground" />
                      ) : (
                        <ChevronRight size={16} className="text-muted-foreground" />
                      )}
                      <div>
                        <span className="text-sm font-semibold text-foreground">{titleMonth}</span>
                        <div className="flex items-center gap-3 text-xs text-muted-foreground mt-0.5">
                          <span>{m.recurring_items.length} recurring</span>
                          <span>•</span>
                          <span>{m.goal_contributions.length} goals</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-6 text-right tabular-nums text-xs">
                      <div className="hidden sm:block">
                        <span className="text-muted-foreground block text-[10px]">Inflow / Outflow</span>
                        <span className="font-medium text-foreground">
                          <span className="text-emerald-600 dark:text-emerald-400">
                            +{mask(formatCurrency(m.adjIncome, userCurrency, locale))}
                          </span>{' '}
                          /{' '}
                          <span className="text-rose-600 dark:text-rose-400">
                            -{mask(formatCurrency(m.adjExpenses, userCurrency, locale))}
                          </span>
                        </span>
                      </div>
                      <div className="hidden sm:block">
                        <span className="text-muted-foreground block text-[10px]">Net Cash Flow</span>
                        <span
                          className={`font-semibold ${
                            m.adjSavings >= 0
                              ? 'text-emerald-600 dark:text-emerald-400'
                              : 'text-rose-600 dark:text-rose-400'
                          }`}
                        >
                          {m.adjSavings >= 0 ? '+' : ''}
                          {mask(formatCurrency(m.adjSavings, userCurrency, locale))}
                        </span>
                      </div>
                      <div>
                        <span className="text-muted-foreground block text-[10px]">Running Balance</span>
                        <span
                          className={`font-bold ${
                            m.adjProjectedBalance < safetyBuffer
                              ? 'text-rose-600 dark:text-rose-400'
                              : 'text-foreground'
                          }`}
                        >
                          {mask(formatCurrency(m.adjProjectedBalance, userCurrency, locale))}
                        </span>
                      </div>
                    </div>
                  </button>

                  {/* Expanded Detail Panel */}
                  {isExpanded && (
                    <div className="px-4 sm:px-5 py-4 bg-muted/20 border-t border-border space-y-4 text-xs">
                      {/* Recurring Items */}
                      {m.recurring_items.length > 0 && (
                        <div>
                          <p className="font-semibold text-foreground flex items-center gap-1.5 mb-2">
                            <Repeat size={13} className="text-muted-foreground" />
                            Scheduled Recurring Bills & Incomes
                          </p>
                          <div className="space-y-1.5 bg-card p-3 rounded-lg border border-border">
                            {m.recurring_items.map((rec, idx) => (
                              <div
                                key={idx}
                                className="flex justify-between items-center py-1 border-b border-border/50 last:border-0"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="text-muted-foreground tabular-nums">{rec.date}</span>
                                  <span className="font-medium text-foreground">{rec.description}</span>
                                  {rec.category_name && (
                                    <span className="text-[10px] bg-muted px-1.5 py-0.5 rounded text-muted-foreground">
                                      {rec.category_name}
                                    </span>
                                  )}
                                </div>
                                <span
                                  className={`font-semibold tabular-nums ${
                                    rec.type === 'credit' ? 'text-emerald-500' : 'text-foreground'
                                  }`}
                                >
                                  {rec.type === 'credit' ? '+' : '-'}
                                  {mask(formatCurrency(rec.amount, rec.currency, locale))}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Category Breakdown */}
                      {m.expense_breakdown.length > 0 && (
                        <div>
                          <p className="font-semibold text-foreground flex items-center gap-1.5 mb-2">
                            <CalendarRange size={13} className="text-muted-foreground" />
                            Projected Category Spending
                          </p>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {m.expense_breakdown.map((cat, idx) => (
                              <div
                                key={idx}
                                className="flex items-center justify-between bg-card p-2.5 rounded-lg border border-border"
                              >
                                <div className="flex items-center gap-2">
                                  <CategoryIcon icon={cat.category_icon} color={cat.category_color} size="sm" />
                                  <span className="font-medium text-foreground">{cat.category_name}</span>
                                </div>
                                <span className="font-semibold tabular-nums text-foreground">
                                  {mask(formatCurrency(cat.projected_amount, userCurrency, locale))}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Goal Contributions */}
                      {m.goal_contributions.length > 0 && (
                        <div>
                          <p className="font-semibold text-foreground flex items-center gap-1.5 mb-2">
                            <Target size={13} className="text-muted-foreground" />
                            Required Goal Contributions
                          </p>
                          <div className="space-y-1.5 bg-card p-3 rounded-lg border border-border">
                            {m.goal_contributions.map((goal, idx) => (
                              <div
                                key={idx}
                                className="flex justify-between items-center py-1 border-b border-border/50 last:border-0"
                              >
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-foreground">{goal.goal_name}</span>
                                  {goal.on_track && (
                                    <span
                                      className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                                        goal.on_track === 'ahead' || goal.on_track === 'on_track'
                                          ? 'bg-emerald-500/10 text-emerald-500'
                                          : 'bg-amber-500/10 text-amber-500'
                                      }`}
                                    >
                                      {goal.on_track.replace('_', ' ')}
                                    </span>
                                  )}
                                </div>
                                <span className="font-semibold tabular-nums text-primary">
                                  {mask(formatCurrency(goal.monthly_contribution, goal.currency, locale))}/mo
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground text-center py-10">No projection data available</p>
        )}
      </SectionCard>
        </>
      )}
    </div>
  )
}
