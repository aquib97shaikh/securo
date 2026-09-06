import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Sparkles,
  SlidersHorizontal,
  Search,
  History,
  CheckCircle2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { PageHeader } from '@/components/page-header'
import { guidance as guidanceApi } from '@/lib/api'
import { GuidanceCard } from '@/components/guidance/guidance-card'
import { GuidanceSummaryStrip } from '@/components/guidance/guidance-summary-strip'
import { CashFlowForecastStrip } from '@/components/guidance/cash-flow-forecast-strip'
import { MonthAtRiskCard } from '@/components/guidance/month-at-risk-card'
import { AdviceTimeline } from '@/components/guidance/advice-timeline'
import type { GuidanceFamily, GuidanceSeverity } from '@/types'

export default function GuidancePage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'active' | 'timeline'>('active')
  const [selectedSeverity, setSelectedSeverity] = useState<GuidanceSeverity | 'all'>('all')
  const [selectedFamily, setSelectedFamily] = useState<GuidanceFamily | 'all'>('all')
  const [searchQuery, setSearchQuery] = useState('')

  const { data: guidanceData, isLoading } = useQuery({
    queryKey: ['guidance-insights'],
    queryFn: () => guidanceApi.getGuidance(),
    staleTime: 1000 * 60 * 3,
  })

  const { data: historyData } = useQuery({
    queryKey: ['guidance-history'],
    queryFn: () => guidanceApi.getHistory(),
    enabled: activeTab === 'timeline',
  })

  // Feedback mutations (snooze, dismiss, rating)
  const feedbackMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) =>
      guidanceApi.submitFeedback(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guidance-insights'] })
      queryClient.invalidateQueries({ queryKey: ['guidance-history'] })
    },
  })

  // Action execution mutation
  const actionMutation = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: any }) =>
      guidanceApi.applyAction(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['guidance-insights'] })
      queryClient.invalidateQueries({ queryKey: ['guidance-history'] })
      queryClient.invalidateQueries({ queryKey: ['budgets'] })
      queryClient.invalidateQueries({ queryKey: ['goals'] })
      queryClient.invalidateQueries({ queryKey: ['recurring'] })
      queryClient.invalidateQueries({ queryKey: ['accounts'] })
      queryClient.invalidateQueries({ queryKey: ['financial-summary'] })
    },
  })

  const insights = guidanceData?.insights || []

  // Filter insights
  const filteredInsights = useMemo(() => {
    return insights.filter((i) => {
      if (selectedSeverity !== 'all' && i.severity !== selectedSeverity) return false
      if (selectedFamily !== 'all' && i.family !== selectedFamily) return false
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase()
        const matchTitle = i.title.toLowerCase().includes(q)
        const matchExp = i.one_line_explanation.toLowerCase().includes(q)
        const matchWhat = i.what_happened.toLowerCase().includes(q)
        if (!matchTitle && !matchExp && !matchWhat) return false
      }
      return true
    })
  }, [insights, selectedSeverity, selectedFamily, searchQuery])

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <PageHeader
        section="Analysis"
        title="Financial Guidance"
        action={
          <div className="flex items-center gap-2">
            <Button
              variant={activeTab === 'active' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('active')}
              className="text-xs h-8"
            >
              <Sparkles size={14} className="mr-1.5" />
              Active Guidance ({insights.length})
            </Button>
            <Button
              variant={activeTab === 'timeline' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('timeline')}
              className="text-xs h-8"
            >
              <History size={14} className="mr-1.5" />
              Advice History
            </Button>
          </div>
        }
      />

      {activeTab === 'active' ? (
        <>
          {/* Summary Status Strip */}
          <GuidanceSummaryStrip
            summary={guidanceData?.summary}
            currency={guidanceData?.currency}
            selectedSeverity={selectedSeverity}
            onSelectSeverity={(sev) =>
              setSelectedSeverity(selectedSeverity === sev ? 'all' : (sev as GuidanceSeverity))
            }
          />

          {/* Forecast & Month at Risk widgets */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <div className="lg:col-span-2">
              <CashFlowForecastStrip
                strip={guidanceData?.cashflow_strip}
                currency={guidanceData?.currency}
              />
            </div>
            <div>
              <MonthAtRiskCard
                items={guidanceData?.month_at_risk}
                currency={guidanceData?.currency}
              />
            </div>
          </div>

          {/* Filter & Search Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <div className="flex flex-wrap items-center gap-1.5 text-xs">
              <span className="text-muted-foreground font-medium mr-1 flex items-center gap-1">
                <SlidersHorizontal size={13} />
                Family:
              </span>
              <button
                onClick={() => setSelectedFamily('all')}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                  selectedFamily === 'all'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setSelectedFamily('budget_control')}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                  selectedFamily === 'budget_control'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                }`}
              >
                Budget Control
              </button>
              <button
                onClick={() => setSelectedFamily('recurring_optimization')}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                  selectedFamily === 'recurring_optimization'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                }`}
              >
                Recurring & Bills
              </button>
              <button
                onClick={() => setSelectedFamily('cash_flow_safety')}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                  selectedFamily === 'cash_flow_safety'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                }`}
              >
                Cash Flow
              </button>
              <button
                onClick={() => setSelectedFamily('goal_recovery')}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                  selectedFamily === 'goal_recovery'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                }`}
              >
                Goal Recovery
              </button>
              <button
                onClick={() => setSelectedFamily('habit_correction')}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                  selectedFamily === 'habit_correction'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                }`}
              >
                Habits
              </button>
            </div>

            <div className="relative w-full sm:w-64">
              <Search
                size={14}
                className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"
              />
              <Input
                placeholder="Search advice..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 h-8 text-xs"
              />
            </div>
          </div>

          {/* Ranked Insight Cards */}
          <div className="space-y-4 pt-1">
            {isLoading ? (
              <div className="space-y-4">
                <Skeleton className="h-36 w-full rounded-xl" />
                <Skeleton className="h-36 w-full rounded-xl" />
                <Skeleton className="h-36 w-full rounded-xl" />
              </div>
            ) : filteredInsights.length > 0 ? (
              filteredInsights.map((insight) => (
                <GuidanceCard
                  key={insight.id}
                  insight={insight}
                  onSnooze={(id, days) =>
                    feedbackMutation.mutate({ id, payload: { snooze_days: days } })
                  }
                  onDismiss={(id) =>
                    feedbackMutation.mutate({ id, payload: { status: 'dismissed' } })
                  }
                  onRate={(id, helpful) =>
                    feedbackMutation.mutate({ id, payload: { is_helpful: helpful } })
                  }
                  onExecuteAction={(ins) => {
                    const payload = {
                      action_type: ins.action?.type || 'executed',
                      ...(ins.action?.payload || {}),
                    }
                    return actionMutation.mutateAsync({
                      id: ins.id,
                      payload,
                    })
                  }}
                />
              ))
            ) : (
              <div className="text-center py-16 px-4 bg-card rounded-xl border border-border">
                <div className="h-12 w-12 rounded-full bg-emerald-500/10 text-emerald-600 flex items-center justify-center mx-auto mb-3">
                  <CheckCircle2 size={24} />
                </div>
                <h4 className="text-base font-semibold text-foreground">No active recommendations</h4>
                <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto">
                  Your spending, recurring bills, and savings pace are aligned with your financial targets!
                </p>
                {(selectedSeverity !== 'all' || selectedFamily !== 'all' || searchQuery) && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      setSelectedSeverity('all')
                      setSelectedFamily('all')
                      setSearchQuery('')
                    }}
                    className="mt-4 text-xs"
                  >
                    Reset filters
                  </Button>
                )}
              </div>
            )}
          </div>
        </>
      ) : (
        /* Advice History & Timeline View */
        <div className="bg-card rounded-xl border border-border p-5">
          <h3 className="text-sm font-semibold text-foreground mb-1">Advice Timeline</h3>
          <p className="text-xs text-muted-foreground mb-4">
            Audit trail of snoozed, dismissed, and executed financial advice
          </p>
          <AdviceTimeline items={historyData || []} />
        </div>
      )}
    </div>
  )
}
