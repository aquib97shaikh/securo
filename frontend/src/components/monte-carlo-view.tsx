import { useState, useMemo, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import {
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  Play,
  Plus,
  Trash2,
  DollarSign,
  PieChart,
  Calendar,
  ArrowUpRight,
} from 'lucide-react'
import {
  AreaChart,
  Area,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

import { planning as planningApi, accounts as accountsApi } from '@/lib/api'
import { usePrivacyMode } from '@/hooks/use-privacy-mode'
import { useAuth } from '@/contexts/auth-context'
import { useDisplayLocale } from '@/hooks/use-display-locale'
import { formatCurrency } from '@/lib/format'
import { SectionCard, SectionHeader } from '@/components/section-card'
import { usePageInfo } from '@/contexts/page-info-context'
import type {
  MonteCarloRequest,
  InvestmentPot,
  SpendingPhase,
  Account,
} from '@/types'

const ASSET_PRESETS: Record<string, { expected_return: number; volatility: number; label: string }> = {
  aggressive: { expected_return: 10.0, volatility: 16.0, label: 'Aggressive (100% Equity)' },
  growth: { expected_return: 8.8, volatility: 13.5, label: 'Growth (80/20 Stocks/Bonds)' },
  balanced: { expected_return: 7.5, volatility: 11.0, label: 'Balanced (60/40 Stocks/Bonds)' },
  conservative: { expected_return: 6.0, volatility: 8.0, label: 'Conservative (40/60)' },
  cash: { expected_return: 3.5, volatility: 2.0, label: 'Cash & Short-Term Reserves' },
  custom: { expected_return: 7.0, volatility: 10.0, label: 'Custom Parameters' },
}

export function MonteCarloView() {
  const { mask } = usePrivacyMode()
  const { user } = useAuth()
  const locale = useDisplayLocale()
  const userCurrency = user?.preferences?.currency_display ?? 'USD'

  // Publish detailed guidance & concepts to the Info Panel while this view is active
  usePageInfo(
    useMemo(
      () => ({
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
            definition:
              'The middle scenario: exactly 50% of simulated market futures performed better, and 50% performed worse.',
          },
          {
            term: 'P10 (Stress-Test / Conservative)',
            definition:
              'Severe downside scenario where 90% of simulations performed better. Critical for confirming whether your retirement or emergency buffer survives bear markets.',
          },
          {
            term: 'P90 (Bull Market Tailwinds)',
            definition:
              'Top 10% optimistic outcome representing strong compounding and favorable market conditions.',
          },
          {
            term: 'Ruin Probability',
            definition:
              'The percentage of simulated futures that depleted cash before reaching the end of your horizon. Aim to keep this below 5% for essential lifestyle needs.',
          },
        ],
        tips: [
          'Keep at least 2–3 years of living costs in cash or short-term reserves to protect against sequence-of-returns risk in early retirement.',
          'If ruin probability is higher than desired, test reducing discretionary spending or extending contributions by 1–2 years.',
          'Use the Conservative or Balanced preset for funds needed within the next 3 to 7 years.',
        ],
      }),
      [],
    ),
  )

  // Fetch accounts to enable linking pots to actual account balances
  const { data: accountsList } = useQuery({
    queryKey: ['accounts', 'all'],
    queryFn: () => accountsApi.list(false),
  })

  // Fetch initial default config from backend
  const { data: defaultConfig, isLoading: isLoadingDefault } = useQuery({
    queryKey: ['planning', 'monte-carlo', 'default-config'],
    queryFn: () => planningApi.getMonteCarloDefaultConfig(),
    staleTime: Infinity,
  })

  // Local state for configuration form
  const [config, setConfig] = useState<MonteCarloRequest | null>(null)
  const [activeTab, setActiveTab] = useState<'horizon' | 'pots' | 'contributions' | 'spending'>('horizon')

  // Initialize config once default config is loaded
  useEffect(() => {
    if (defaultConfig && !config) {
      setConfig(defaultConfig)
    }
  }, [defaultConfig, config])

  // Mutation to execute Monte Carlo simulation
  const {
    mutate: runSimulation,
    data: simulationResult,
    isPending: isRunningSimulation,
  } = useMutation({
    mutationFn: (req: MonteCarloRequest) => planningApi.runMonteCarlo(req),
  })

  // Auto-run simulation when config is first initialized
  useEffect(() => {
    if (config && !simulationResult && !isRunningSimulation) {
      runSimulation(config)
    }
  }, [config, simulationResult, isRunningSimulation, runSimulation])

  const handlePresetChange = (potIndex: number, presetKey: string) => {
    if (!config) return
    const preset = ASSET_PRESETS[presetKey]
    const updatedPots = [...config.pots]
    updatedPots[potIndex] = {
      ...updatedPots[potIndex],
      asset_class: presetKey as any,
      expected_return: preset ? preset.expected_return : updatedPots[potIndex].expected_return,
      volatility: preset ? preset.volatility : updatedPots[potIndex].volatility,
    }
    setConfig({ ...config, pots: updatedPots })
  }

  const handleAccountLink = (potIndex: number, accountIdStr: string) => {
    if (!config) return
    const updatedPots = [...config.pots]
    if (!accountIdStr) {
      updatedPots[potIndex] = { ...updatedPots[potIndex], account_id: null }
    } else {
      const selectedAcc = accountsList?.find((a: Account) => a.id === accountIdStr)
      updatedPots[potIndex] = {
        ...updatedPots[potIndex],
        account_id: accountIdStr,
        starting_balance: selectedAcc ? Math.max(0, selectedAcc.current_balance) : updatedPots[potIndex].starting_balance,
        name: selectedAcc ? selectedAcc.name : updatedPots[potIndex].name,
      }
    }
    setConfig({ ...config, pots: updatedPots })
  }

  const addPot = () => {
    if (!config) return
    const newPot: InvestmentPot = {
      id: crypto.randomUUID(),
      name: 'New Investment Pot',
      starting_balance: 25000,
      asset_class: 'balanced',
      expected_return: 7.5,
      volatility: 11.0,
      tax_rate: 0,
      fee_annual_percent: 0.15,
    }
    setConfig({ ...config, pots: [...config.pots, newPot] })
  }

  const removePot = (index: number) => {
    if (!config || config.pots.length <= 1) return
    const updatedPots = config.pots.filter((_, idx) => idx !== index)
    setConfig({ ...config, pots: updatedPots })
  }

  const addSpendingPhase = () => {
    if (!config) return
    const newPhase: SpendingPhase = {
      id: crypto.randomUUID(),
      name: 'Phase ' + (config.spending_phases.length + 1),
      start_age: 65,
      amount_annual: 36000,
    }
    setConfig({ ...config, spending_phases: [...config.spending_phases, newPhase] })
  }

  const removeSpendingPhase = (index: number) => {
    if (!config || config.spending_phases.length <= 1) return
    const updated = config.spending_phases.filter((_, idx) => idx !== index)
    setConfig({ ...config, spending_phases: updated })
  }

  // Pre-formatted chart data for the Fan Percentile Chart
  const fanChartData = useMemo(() => {
    if (!simulationResult) return []
    return simulationResult.percentiles.map(p => ({
      age: p.age,
      // Bands for stacked/composed confidence interval
      p10: Math.round(p.p10),
      p25: Math.round(p.p25),
      p50: Math.round(p.p50), // Median line
      p75: Math.round(p.p75),
      p90: Math.round(p.p90),
      // Interval slices for visualization
      band80_bottom: Math.round(p.p10),
      band80_span: Math.round(p.p90 - p.p10),
      band50_bottom: Math.round(p.p25),
      band50_span: Math.round(p.p75 - p.p25),
    }))
  }, [simulationResult])

  if (isLoadingDefault || !config) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-28 bg-card rounded-xl border border-border animate-pulse" />
          ))}
        </div>
        <div className="h-96 bg-card rounded-xl border border-border animate-pulse" />
      </div>
    )
  }

  const successRate = simulationResult?.success_rate ?? 0
  const isHighSuccess = successRate >= 85
  const isMediumSuccess = successRate >= 70 && successRate < 85

  return (
    <div className="space-y-6">
      {/* Simulation Headline KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Success Rate */}
        <SectionCard>
          <div className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-medium">Plan Success Rate</p>
              <div className="flex items-baseline gap-2 mt-1">
                <p
                  className={`text-xl sm:text-2xl font-bold tabular-nums ${
                    isHighSuccess
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : isMediumSuccess
                      ? 'text-amber-600 dark:text-amber-400'
                      : 'text-rose-600 dark:text-rose-400'
                  }`}
                >
                  {simulationResult ? `${simulationResult.success_rate}%` : '—'}
                </p>
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                    isHighSuccess
                      ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                      : isMediumSuccess
                      ? 'bg-amber-500/10 text-amber-600 dark:text-amber-400'
                      : 'bg-rose-500/10 text-rose-600 dark:text-rose-400'
                  }`}
                >
                  {isHighSuccess ? 'Resilient' : isMediumSuccess ? 'Moderate' : 'At Risk'}
                </span>
              </div>
              <p className="text-[11px] text-muted-foreground mt-1">
                Across {simulationResult?.total_simulations.toLocaleString() || 1000} market futures
              </p>
            </div>
            <div
              className={`p-2.5 rounded-lg ${
                isHighSuccess
                  ? 'bg-emerald-500/10 text-emerald-500'
                  : isMediumSuccess
                  ? 'bg-amber-500/10 text-amber-500'
                  : 'bg-rose-500/10 text-rose-500'
              }`}
            >
              <ShieldCheck size={22} />
            </div>
          </div>
        </SectionCard>

        {/* Median Ending Balance */}
        <SectionCard>
          <div className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-medium">Median Ending Balance</p>
              <p className="text-xl sm:text-2xl font-bold text-foreground mt-1 tabular-nums">
                {simulationResult
                  ? mask(formatCurrency(simulationResult.median_ending_balance, userCurrency, locale))
                  : '—'}
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">At age {config.target_age}</p>
            </div>
            <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-500">
              <TrendingUp size={22} />
            </div>
          </div>
        </SectionCard>

        {/* Median Total Withdrawn */}
        <SectionCard>
          <div className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-medium">Median Total Withdrawn</p>
              <p className="text-xl sm:text-2xl font-bold text-foreground mt-1 tabular-nums">
                {simulationResult
                  ? mask(formatCurrency(simulationResult.median_total_withdrawn, userCurrency, locale))
                  : '—'}
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">Lifetime income delivered</p>
            </div>
            <div className="p-2.5 rounded-lg bg-primary/10 text-primary">
              <DollarSign size={22} />
            </div>
          </div>
        </SectionCard>

        {/* Depletion Risk & Failure Age */}
        <SectionCard>
          <div className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground font-medium">Risk of Depletion</p>
              <p
                className={`text-xl sm:text-2xl font-bold mt-1 tabular-nums ${
                  (simulationResult?.chance_of_running_out || 0) > 15
                    ? 'text-rose-600 dark:text-rose-400'
                    : 'text-foreground'
                }`}
              >
                {simulationResult ? `${simulationResult.chance_of_running_out}%` : '—'}
              </p>
              <p className="text-[11px] text-muted-foreground mt-1">
                {simulationResult?.typical_failure_age
                  ? `Typical depletion at age ${simulationResult.typical_failure_age}`
                  : 'No depletion observed'}
              </p>
            </div>
            <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-500">
              <AlertTriangle size={22} />
            </div>
          </div>
        </SectionCard>
      </div>

      {/* Main Fan Chart: Portfolio Performance Confidence Bands */}
      <SectionCard>
        <SectionHeader
          title="Portfolio Performance Trajectory (Confidence Bands)"
          subtitle="Simulates market volatility, crashes, and compounding to reveal 80% and 50% outcome ranges"
          action={
            <div className="flex items-center gap-3 text-xs">
              <span className="flex items-center gap-1 text-muted-foreground">
                <span className="w-3 h-3 rounded bg-blue-500/20 border border-blue-500/40 inline-block" /> 80% Range
                (10th–90th)
              </span>
              <span className="flex items-center gap-1 text-muted-foreground">
                <span className="w-3 h-3 rounded bg-blue-500/40 border border-blue-500/60 inline-block" /> 50% Range
                (25th–75th)
              </span>
              <span className="flex items-center gap-1 font-medium text-foreground">
                <span className="w-3 h-0.5 bg-blue-600 inline-block" /> Median (50th)
              </span>
            </div>
          }
        />
        <div className="p-4 sm:p-6">
          <div className="h-80 sm:h-96 w-full">
            {fanChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={fanChartData} margin={{ top: 10, right: 10, left: 20, bottom: 20 }}>
                  <defs>
                    <linearGradient id="band80" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.05} />
                    </linearGradient>
                    <linearGradient id="band50" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.45} />
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.2} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-border" />
                  <XAxis
                    dataKey="age"
                    tick={{ fontSize: 11, fill: 'currentColor' }}
                    className="text-muted-foreground"
                    unit=" yrs"
                  />
                  <YAxis
                    tick={{ fontSize: 11, fill: 'currentColor' }}
                    className="text-muted-foreground"
                    tickFormatter={val => formatCurrency(val, userCurrency, locale)}
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null
                      const d = payload[0].payload
                      return (
                        <div className="bg-popover border border-border p-3 rounded-lg shadow-lg text-xs space-y-1.5 min-w-[200px]">
                          <p className="font-semibold text-foreground border-b border-border pb-1">
                            Age {d.age} (Year {d.age - config.current_age})
                          </p>
                          <div className="space-y-1 tabular-nums">
                            <div className="flex justify-between text-muted-foreground">
                              <span>Optimistic (90th):</span>
                              <span className="font-medium text-foreground">
                                {mask(formatCurrency(d.p90, userCurrency, locale))}
                              </span>
                            </div>
                            <div className="flex justify-between text-muted-foreground">
                              <span>75th Percentile:</span>
                              <span className="font-medium text-foreground">
                                {mask(formatCurrency(d.p75, userCurrency, locale))}
                              </span>
                            </div>
                            <div className="flex justify-between text-primary font-bold">
                              <span>Median (50th):</span>
                              <span>{mask(formatCurrency(d.p50, userCurrency, locale))}</span>
                            </div>
                            <div className="flex justify-between text-muted-foreground">
                              <span>25th Percentile:</span>
                              <span className="font-medium text-foreground">
                                {mask(formatCurrency(d.p25, userCurrency, locale))}
                              </span>
                            </div>
                            <div className="flex justify-between text-muted-foreground">
                              <span>Pessimistic (10th):</span>
                              <span className="font-medium text-foreground">
                                {mask(formatCurrency(d.p10, userCurrency, locale))}
                              </span>
                            </div>
                          </div>
                        </div>
                      )
                    }}
                  />
                  {/* 80% confidence interval band */}
                  <Area dataKey="p90" stroke="none" fill="url(#band80)" />
                  {/* 50% confidence interval band */}
                  <Area dataKey="p75" stroke="none" fill="url(#band50)" />
                  {/* Median Line */}
                  <Line
                    type="monotone"
                    dataKey="p50"
                    stroke="#2563EB"
                    strokeWidth={2.5}
                    dot={false}
                    activeDot={{ r: 5 }}
                  />
                  {/* Pessimistic Boundary Line */}
                  <Line type="monotone" dataKey="p10" stroke="#94A3B8" strokeWidth={1} strokeDasharray="3 3" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                Run simulation to generate confidence trajectory
              </div>
            )}
          </div>
        </div>
      </SectionCard>

      {/* Failure Distribution Histogram (if any runs failed) */}
      {simulationResult && simulationResult.failure_histogram.length > 0 && (
        <SectionCard>
          <SectionHeader
            title="When Did Money Run Out? (Depletion Distribution)"
            subtitle="Breakdown of the specific ages when capital depleted across the failed simulation runs"
          />
          <div className="p-4 sm:p-6">
            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={simulationResult.failure_histogram} margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-border" />
                  <XAxis dataKey="age" tick={{ fontSize: 11 }} unit=" yrs" />
                  <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null
                      const d = payload[0].payload
                      return (
                        <div className="bg-popover border border-border p-2.5 rounded-lg shadow text-xs">
                          <p className="font-semibold text-foreground">Depleted at Age {d.age}</p>
                          <p className="text-rose-500 font-medium mt-0.5">
                            {d.count} replays ({d.percentage}% of all runs)
                          </p>
                        </div>
                      )
                    }}
                  />
                  <Bar dataKey="count" fill="#F43F5E" radius={[4, 4, 0, 0]} maxBarSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </SectionCard>
      )}

      {/* Simulation Setup & Parameters Panel */}
      <SectionCard>
        <div className="border-b border-border px-4 sm:px-6 flex items-center justify-between flex-wrap gap-3 py-3">
          {/* Sub-Tabs */}
          <div className="flex items-center gap-1 bg-muted/50 p-1 rounded-lg border border-border text-xs">
            <button
              onClick={() => setActiveTab('horizon')}
              className={`px-3 py-1.5 font-medium rounded-md transition-colors flex items-center gap-1.5 ${
                activeTab === 'horizon' ? 'bg-card text-foreground shadow-sm font-semibold' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <Calendar size={13} />
              Plan & Horizon
            </button>
            <button
              onClick={() => setActiveTab('pots')}
              className={`px-3 py-1.5 font-medium rounded-md transition-colors flex items-center gap-1.5 ${
                activeTab === 'pots' ? 'bg-card text-foreground shadow-sm font-semibold' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <PieChart size={13} />
              Investment Pots ({config.pots.length})
            </button>
            <button
              onClick={() => setActiveTab('contributions')}
              className={`px-3 py-1.5 font-medium rounded-md transition-colors flex items-center gap-1.5 ${
                activeTab === 'contributions' ? 'bg-card text-foreground shadow-sm font-semibold' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <ArrowUpRight size={13} />
              Contributions ({config.contributions.length})
            </button>
            <button
              onClick={() => setActiveTab('spending')}
              className={`px-3 py-1.5 font-medium rounded-md transition-colors flex items-center gap-1.5 ${
                activeTab === 'spending' ? 'bg-card text-foreground shadow-sm font-semibold' : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              <DollarSign size={13} />
              Spending & Withdrawals
            </button>
          </div>

          {/* Run / Recalculate Simulation Button */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => runSimulation(config)}
              disabled={isRunningSimulation}
              className="inline-flex items-center gap-1.5 bg-primary text-primary-foreground font-medium text-xs px-4 py-2 rounded-lg shadow-sm hover:opacity-90 transition-opacity disabled:opacity-50"
            >
              <Play size={13} />
              {isRunningSimulation ? 'Simulating...' : 'Run Simulation'}
            </button>
          </div>
        </div>

        {/* Tab 1: Horizon & Model Settings */}
        {activeTab === 'horizon' && (
          <div className="p-4 sm:p-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 text-xs">
            <div className="space-y-1.5">
              <label className="font-medium text-foreground">Current Age</label>
              <input
                type="number"
                min="18"
                max="90"
                value={config.current_age}
                onChange={e => setConfig({ ...config, current_age: Number(e.target.value) || 35 })}
                className="w-full bg-muted/40 border border-border rounded-lg px-3 py-1.5 text-foreground font-medium focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <p className="text-[11px] text-muted-foreground">Starting year of simulation</p>
            </div>

            <div className="space-y-1.5">
              <label className="font-medium text-foreground">Pot Must Last Until Age</label>
              <input
                type="number"
                min={config.current_age + 5}
                max="110"
                value={config.target_age}
                onChange={e => setConfig({ ...config, target_age: Number(e.target.value) || 90 })}
                className="w-full bg-muted/40 border border-border rounded-lg px-3 py-1.5 text-foreground font-medium focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <p className="text-[11px] text-muted-foreground">
                Testing {config.target_age - config.current_age} years horizon
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="font-medium text-foreground">Number of Replays</label>
              <select
                value={config.num_simulations}
                onChange={e => setConfig({ ...config, num_simulations: Number(e.target.value) || 1000 })}
                className="w-full bg-muted/40 border border-border rounded-lg px-3 py-1.5 text-foreground font-medium focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value={1000}>1,000 Replays (Fast)</option>
                <option value={2500}>2,500 Replays (Standard)</option>
                <option value={5000}>5,000 Replays (High Precision)</option>
              </select>
              <p className="text-[11px] text-muted-foreground">More runs increase precision</p>
            </div>

            <div className="space-y-1.5">
              <label className="font-medium text-foreground">Inflation Mean (%)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="15"
                value={config.inflation_mean}
                onChange={e => setConfig({ ...config, inflation_mean: Number(e.target.value) || 2.5 })}
                className="w-full bg-muted/40 border border-border rounded-lg px-3 py-1.5 text-foreground font-medium focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <p className="text-[11px] text-muted-foreground">Expected annual rise in prices</p>
            </div>
          </div>
        )}

        {/* Tab 2: Investment Pots */}
        {activeTab === 'pots' && (
          <div className="p-4 sm:p-6 space-y-4 text-xs">
            <div className="flex justify-between items-center">
              <p className="text-muted-foreground text-xs">
                Model individual investment accounts, pensions, or cash reserves with custom return and volatility assumptions
              </p>
              <button
                onClick={addPot}
                className="inline-flex items-center gap-1 bg-muted px-2.5 py-1.5 rounded-lg text-foreground font-medium hover:bg-muted/80 transition-colors"
              >
                <Plus size={13} /> Add Pot
              </button>
            </div>

            <div className="space-y-3">
              {config.pots.map((pot, idx) => (
                <div key={pot.id} className="bg-card border border-border rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <input
                      type="text"
                      value={pot.name}
                      onChange={e => {
                        const updated = [...config.pots]
                        updated[idx].name = e.target.value
                        setConfig({ ...config, pots: updated })
                      }}
                      className="font-semibold text-sm bg-transparent border-b border-border/50 focus:border-primary focus:outline-none px-1 py-0.5"
                    />
                    <div className="flex items-center gap-2">
                      <select
                        value={pot.account_id || ''}
                        onChange={e => handleAccountLink(idx, e.target.value)}
                        className="bg-muted/40 border border-border rounded px-2 py-1 text-[11px] text-muted-foreground"
                      >
                        <option value="">Unlinked (Manual)</option>
                        {accountsList?.map((acc: Account) => (
                          <option key={acc.id} value={acc.id}>
                            Link: {acc.name}
                          </option>
                        ))}
                      </select>
                      {config.pots.length > 1 && (
                        <button
                          onClick={() => removePot(idx)}
                          className="text-muted-foreground hover:text-rose-500 p-1 transition-colors"
                        >
                          <Trash2 size={14} />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-1">
                    <div>
                      <label className="text-[11px] text-muted-foreground block mb-1">Starting Balance</label>
                      <input
                        type="number"
                        min="0"
                        value={pot.starting_balance}
                        onChange={e => {
                          const updated = [...config.pots]
                          updated[idx].starting_balance = Math.max(0, Number(e.target.value) || 0)
                          setConfig({ ...config, pots: updated })
                        }}
                        className="w-full bg-muted/40 border border-border rounded px-2.5 py-1 text-foreground font-medium"
                      />
                    </div>

                    <div>
                      <label className="text-[11px] text-muted-foreground block mb-1">Portfolio Allocation</label>
                      <select
                        value={pot.asset_class}
                        onChange={e => handlePresetChange(idx, e.target.value)}
                        className="w-full bg-muted/40 border border-border rounded px-2 py-1 text-foreground font-medium"
                      >
                        {Object.entries(ASSET_PRESETS).map(([key, item]) => (
                          <option key={key} value={key}>
                            {item.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="text-[11px] text-muted-foreground block mb-1">Expected Return (%)</label>
                      <input
                        type="number"
                        step="0.1"
                        value={pot.expected_return}
                        onChange={e => {
                          const updated = [...config.pots]
                          updated[idx].expected_return = Number(e.target.value) || 0
                          updated[idx].asset_class = 'custom'
                          setConfig({ ...config, pots: updated })
                        }}
                        className="w-full bg-muted/40 border border-border rounded px-2.5 py-1 text-foreground font-medium"
                      />
                    </div>

                    <div>
                      <label className="text-[11px] text-muted-foreground block mb-1">Volatility Std Dev (%)</label>
                      <input
                        type="number"
                        step="0.1"
                        min="0.1"
                        value={pot.volatility}
                        onChange={e => {
                          const updated = [...config.pots]
                          updated[idx].volatility = Math.max(0.1, Number(e.target.value) || 0)
                          updated[idx].asset_class = 'custom'
                          setConfig({ ...config, pots: updated })
                        }}
                        className="w-full bg-muted/40 border border-border rounded px-2.5 py-1 text-foreground font-medium"
                      />
                    </div>

                    <div>
                      <label className="text-[11px] text-muted-foreground block mb-1">Access Age (Locked until)</label>
                      <input
                        type="number"
                        placeholder="None (Immediate)"
                        value={pot.access_age || ''}
                        onChange={e => {
                          const updated = [...config.pots]
                          updated[idx].access_age = e.target.value ? Number(e.target.value) : null
                          setConfig({ ...config, pots: updated })
                        }}
                        className="w-full bg-muted/40 border border-border rounded px-2.5 py-1 text-foreground font-medium"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 3: Contributions */}
        {activeTab === 'contributions' && (
          <div className="p-4 sm:p-6 space-y-4 text-xs">
            <p className="text-muted-foreground text-xs">
              Annual savings and deposits made into your investment pots during your accumulation / working years
            </p>

            <div className="space-y-3">
              {config.contributions.map((contrib, idx) => (
                <div key={contrib.id} className="bg-card border border-border rounded-xl p-4 grid grid-cols-1 sm:grid-cols-4 gap-3">
                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Contribution Name</label>
                    <input
                      type="text"
                      value={contrib.name}
                      onChange={e => {
                        const updated = [...config.contributions]
                        updated[idx].name = e.target.value
                        setConfig({ ...config, contributions: updated })
                      }}
                      className="w-full bg-muted/40 border border-border rounded px-2.5 py-1 text-foreground font-medium"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Annual Amount</label>
                    <input
                      type="number"
                      min="0"
                      value={contrib.amount_annual}
                      onChange={e => {
                        const updated = [...config.contributions]
                        updated[idx].amount_annual = Math.max(0, Number(e.target.value) || 0)
                        setConfig({ ...config, contributions: updated })
                      }}
                      className="w-full bg-muted/40 border border-border rounded px-2.5 py-1 text-foreground font-medium"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] text-muted-foreground block mb-1">Target Pot</label>
                    <select
                      value={contrib.pot_id}
                      onChange={e => {
                        const updated = [...config.contributions]
                        updated[idx].pot_id = e.target.value
                        setConfig({ ...config, contributions: updated })
                      }}
                      className="w-full bg-muted/40 border border-border rounded px-2 py-1 text-foreground font-medium"
                    >
                      {config.pots.map(p => (
                        <option key={p.id} value={p.id}>
                          {p.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex items-center justify-between pt-4">
                    <label className="flex items-center gap-1.5 cursor-pointer text-muted-foreground">
                      <input
                        type="checkbox"
                        checked={contrib.adjust_for_inflation}
                        onChange={e => {
                          const updated = [...config.contributions]
                          updated[idx].adjust_for_inflation = e.target.checked
                          setConfig({ ...config, contributions: updated })
                        }}
                        className="rounded border-border"
                      />
                      Grow with Inflation
                    </label>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab 4: Spending & Withdrawals */}
        {activeTab === 'spending' && (
          <div className="p-4 sm:p-6 space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pb-2 border-b border-border">
              <div>
                <label className="font-medium text-foreground block mb-1">Withdrawal Strategy across Pots</label>
                <select
                  value={config.withdrawal_strategy}
                  onChange={e => setConfig({ ...config, withdrawal_strategy: e.target.value as any })}
                  className="w-full bg-muted/40 border border-border rounded-lg px-3 py-1.5 text-foreground font-medium focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option value="proportional">Split Proportionally across Accessible Pots</option>
                  <option value="drain_order">Drain Pots in Order (Empty Pot 1 then Pot 2)</option>
                  <option value="best_performer">Spend from Best Performer First (Bucket Strategy)</option>
                </select>
                <p className="text-[11px] text-muted-foreground mt-1">Controls how funds are drawn when multiple pots exist</p>
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1">Minimum Annual Withdrawal Floor</label>
                <input
                  type="number"
                  min="0"
                  value={config.min_annual_withdrawal}
                  onChange={e => setConfig({ ...config, min_annual_withdrawal: Math.max(0, Number(e.target.value) || 0) })}
                  className="w-full bg-muted/40 border border-border rounded-lg px-3 py-1.5 text-foreground font-medium focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <p className="text-[11px] text-muted-foreground mt-1">Guarantees an essential spending floor</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <p className="font-medium text-foreground">Retirement Spending Phases</p>
                <button
                  onClick={addSpendingPhase}
                  className="inline-flex items-center gap-1 bg-muted px-2.5 py-1 rounded text-foreground font-medium hover:bg-muted/80 transition-colors"
                >
                  <Plus size={12} /> Add Phase
                </button>
              </div>

              {config.spending_phases.map((phase, idx) => (
                <div key={phase.id} className="bg-card border border-border rounded-xl p-3.5 flex items-center gap-4">
                  <div className="flex-1">
                    <label className="text-[10px] text-muted-foreground block">Phase Label</label>
                    <input
                      type="text"
                      value={phase.name}
                      onChange={e => {
                        const updated = [...config.spending_phases]
                        updated[idx].name = e.target.value
                        setConfig({ ...config, spending_phases: updated })
                      }}
                      className="w-full bg-transparent border-b border-border/50 text-foreground font-medium px-1 py-0.5"
                    />
                  </div>

                  <div className="w-32">
                    <label className="text-[10px] text-muted-foreground block">Starting at Age</label>
                    <input
                      type="number"
                      min={config.current_age}
                      value={phase.start_age}
                      onChange={e => {
                        const updated = [...config.spending_phases]
                        updated[idx].start_age = Number(e.target.value) || 65
                        setConfig({ ...config, spending_phases: updated })
                      }}
                      className="w-full bg-muted/40 border border-border rounded px-2.5 py-1 text-foreground font-medium"
                    />
                  </div>

                  <div className="w-40">
                    <label className="text-[10px] text-muted-foreground block">Annual Living Spend</label>
                    <input
                      type="number"
                      min="0"
                      step="1000"
                      value={phase.amount_annual}
                      onChange={e => {
                        const updated = [...config.spending_phases]
                        updated[idx].amount_annual = Math.max(0, Number(e.target.value) || 0)
                        setConfig({ ...config, spending_phases: updated })
                      }}
                      className="w-full bg-muted/40 border border-border rounded px-2.5 py-1 text-foreground font-medium"
                    />
                  </div>

                  {config.spending_phases.length > 1 && (
                    <button
                      onClick={() => removeSpendingPhase(idx)}
                      className="text-muted-foreground hover:text-rose-500 p-1 transition-colors mt-3"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </SectionCard>
    </div>
  )
}
