import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  AlertCircle,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Eye,
  HelpCircle,
  Loader2,
  MoreVertical,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
  X,
} from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { formatCurrency } from '@/lib/format'
import { useDisplayLocale } from '@/hooks/use-display-locale'
import { usePrivacyMode } from '@/hooks/use-privacy-mode'
import { useAuth } from '@/contexts/auth-context'
import type { GuidanceInsight } from '@/types'

const severityStyles = {
  urgent: {
    bg: 'bg-rose-500/10 dark:bg-rose-500/15 border-rose-500/30 text-rose-700 dark:text-rose-400',
    badge: 'bg-rose-500 text-white',
    icon: AlertCircle,
    label: 'Urgent',
  },
  action_needed: {
    bg: 'bg-amber-500/10 dark:bg-amber-500/15 border-amber-500/30 text-amber-700 dark:text-amber-400',
    badge: 'bg-amber-500 text-white',
    icon: AlertTriangle,
    label: 'Action needed',
  },
  watch: {
    bg: 'bg-blue-500/10 dark:bg-blue-500/15 border-blue-500/30 text-blue-700 dark:text-blue-400',
    badge: 'bg-blue-500 text-white',
    icon: Eye,
    label: 'Watch',
  },
  informational: {
    bg: 'bg-emerald-500/10 dark:bg-emerald-500/15 border-emerald-500/30 text-emerald-700 dark:text-emerald-400',
    badge: 'bg-emerald-600 text-white',
    icon: Sparkles,
    label: 'Tip',
  },
}

const familyLabels: Record<string, string> = {
  budget_control: 'Budget Control',
  recurring_optimization: 'Recurring & Bills',
  cash_flow_safety: 'Cash-Flow Safety',
  goal_recovery: 'Goal Recovery',
  habit_correction: 'Habit Correction',
}

interface GuidanceCardProps {
  insight: GuidanceInsight
  onSnooze?: (id: string, days: number) => void
  onDismiss?: (id: string) => void
  onRate?: (id: string, helpful: boolean) => void
  onExecuteAction?: (insight: GuidanceInsight) => Promise<any> | void
  compact?: boolean
}

export function GuidanceCard({
  insight,
  onSnooze,
  onDismiss,
  onRate,
  onExecuteAction,
}: GuidanceCardProps) {
  const navigate = useNavigate()
  const { user } = useAuth()
  const locale = useDisplayLocale()
  const { mask } = usePrivacyMode()
  const [expanded, setExpanded] = useState(false)
  const [rated, setRated] = useState<boolean | null>(null)
  const [isExecuting, setIsExecuting] = useState(false)
  const [executed, setExecuted] = useState(false)

  const autoActionsEnabled = user?.preferences?.guidance_auto_actions !== false

  const sev = severityStyles[insight.severity] || severityStyles.informational
  const Icon = sev.icon

  const handleActionClick = async () => {
    if (isExecuting || executed) return

    if (onExecuteAction) {
      try {
        setIsExecuting(true)
        await onExecuteAction(insight)
        setExecuted(true)
        toast.success(
          insight.action?.label ? `${insight.action.label} applied!` : 'Action applied successfully!'
        )
      } catch (err: any) {
        toast.error(err?.message || 'Failed to apply recommendation')
      } finally {
        setIsExecuting(false)
      }
      return
    }

    if (insight.action?.url) {
      navigate(insight.action.url)
    }
  }

  const handleRate = (helpful: boolean) => {
    setRated(helpful)
    if (onRate) {
      onRate(insight.id, helpful)
    }
  }

  return (
    <div
      className={`rounded-xl border transition-all duration-200 bg-card hover:shadow-md ${
        insight.severity === 'urgent'
          ? 'border-rose-500/40 shadow-rose-500/5'
          : insight.severity === 'action_needed'
          ? 'border-amber-500/40'
          : 'border-border'
      } overflow-hidden`}
    >
      {/* Card Header & Badges */}
      <div className="p-4 sm:p-5">
        <div className="flex items-start justify-between gap-2 mb-2.5">
          <div className="flex flex-wrap items-center gap-1.5">
            {/* Severity Pill */}
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold tracking-wide uppercase ${sev.badge}`}
            >
              <Icon size={12} />
              {sev.label}
            </span>

            {/* 100-Point Score Pill */}
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-muted text-muted-foreground">
              Score: <strong className="text-foreground">{insight.score.toFixed(0)}</strong>/100
            </span>

            {/* Family Tag */}
            <span className="text-[11px] text-muted-foreground font-medium px-1.5 py-0.5 rounded bg-secondary/50">
              {familyLabels[insight.family] || insight.family}
            </span>
          </div>

          {/* Card Context Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 w-7 p-0 text-muted-foreground hover:text-foreground"
                aria-label="Options"
              >
                <MoreVertical size={15} />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48 text-xs">
              <DropdownMenuItem onClick={() => onSnooze?.(insight.id, 7)}>
                <Clock size={13} className="mr-2 text-muted-foreground" />
                Snooze for 7 days
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onSnooze?.(insight.id, 30)}>
                <Clock size={13} className="mr-2 text-muted-foreground" />
                Snooze for 30 days
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => onDismiss?.(insight.id)}
                className="text-destructive focus:text-destructive"
              >
                <X size={13} className="mr-2" />
                Dismiss permanently
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Title */}
        <h4 className="text-sm sm:text-base font-semibold text-foreground tracking-tight leading-snug mb-1.5">
          {insight.title}
        </h4>

        {/* One-line explanation */}
        <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed mb-3">
          {insight.one_line_explanation}
        </p>

        {/* Impact Amount (if any) */}
        {insight.impact_amount !== null && insight.impact_amount !== undefined && (
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-lg bg-secondary/60 border border-border/60 text-xs font-semibold text-foreground mb-3.5">
            <span className="text-muted-foreground font-normal">Impact:</span>
            <span className="tabular-nums">
              {mask(formatCurrency(Number(insight.impact_amount), insight.currency, locale))}
            </span>
          </div>
        )}

        {/* Primary Recommended Action & Controls */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-border/50">
          {autoActionsEnabled ? (
            <Button
              size="sm"
              onClick={handleActionClick}
              disabled={isExecuting || executed}
              className={`text-xs font-medium h-8 transition-all ${
                executed
                  ? 'bg-emerald-600 hover:bg-emerald-600 text-white cursor-default'
                  : insight.severity === 'urgent'
                  ? 'bg-rose-600 hover:bg-rose-700 text-white'
                  : insight.severity === 'action_needed'
                  ? 'bg-amber-600 hover:bg-amber-700 text-white'
                  : 'bg-primary hover:bg-primary/90 text-primary-foreground'
              }`}
            >
              {isExecuting ? (
                <>
                  <Loader2 size={13} className="mr-1.5 animate-spin" />
                  Applying...
                </>
              ) : executed ? (
                <>
                  <CheckCircle2 size={13} className="mr-1.5 text-white" />
                  Applied
                </>
              ) : (
                <>
                  {insight.action?.label || 'Take action'}
                  <ArrowRight size={13} className="ml-1.5" />
                </>
              )}
            </Button>
          ) : insight.action?.url ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => navigate(insight.action!.url!)}
              className="text-xs font-medium h-8"
            >
              <span>Review in page</span>
              <ArrowRight size={13} className="ml-1.5" />
            </Button>
          ) : (
            <div className="text-[11px] text-muted-foreground italic py-1">
              Manual review recommended
            </div>
          )}

          <div className="flex items-center gap-1">
            {/* Feedback: Useful / Not Useful */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleRate(true)}
              className={`h-7 px-2 text-xs gap-1 ${
                rated === true ? 'text-emerald-600 bg-emerald-500/10' : 'text-muted-foreground hover:text-foreground'
              }`}
              title="Helpful recommendation"
            >
              <ThumbsUp size={12} />
              {rated === true && <span className="text-[10px]">Helpful</span>}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => handleRate(false)}
              className={`h-7 px-2 text-xs ${
                rated === false ? 'text-rose-600 bg-rose-500/10' : 'text-muted-foreground hover:text-foreground'
              }`}
              title="Not helpful"
            >
              <ThumbsDown size={12} />
            </Button>

            {/* "Why am I seeing this?" Toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
              className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground gap-1"
            >
              <HelpCircle size={12} />
              <span className="hidden sm:inline">Why?</span>
              {expanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </Button>
          </div>
        </div>
      </div>

      {/* Expandable 5-Point Explainability Panel */}
      {expanded && (
        <div className="bg-muted/40 border-t border-border px-4 sm:px-5 py-4 space-y-3.5 text-xs text-foreground animate-in fade-in-50 duration-150">
          <div>
            <span className="font-semibold text-muted-foreground uppercase text-[10px] tracking-wider block mb-0.5">
              1. What happened?
            </span>
            <p className="text-foreground leading-relaxed">{insight.what_happened}</p>
          </div>

          <div>
            <span className="font-semibold text-muted-foreground uppercase text-[10px] tracking-wider block mb-0.5">
              2. Why does it matter?
            </span>
            <p className="text-foreground leading-relaxed">{insight.why_it_matters}</p>
          </div>

          <div>
            <span className="font-semibold text-muted-foreground uppercase text-[10px] tracking-wider block mb-0.5">
              3. How was it calculated?
            </span>
            <p className="text-foreground leading-relaxed font-mono text-[11px] bg-card p-2 rounded border border-border">
              {insight.how_calculated}
            </p>
          </div>

          <div>
            <span className="font-semibold text-muted-foreground uppercase text-[10px] tracking-wider block mb-0.5">
              4. Suggested next action
            </span>
            <p className="text-foreground leading-relaxed font-medium">{insight.next_action}</p>
          </div>

          {/* 5. Supporting Evidence (Transactions / Forecast) */}
          {insight.evidence?.transactions && insight.evidence.transactions.length > 0 && (
            <div>
              <span className="font-semibold text-muted-foreground uppercase text-[10px] tracking-wider block mb-1.5">
                5. Supporting transactions ({insight.evidence.transactions.length})
              </span>
              <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                {insight.evidence.transactions.map((tx) => (
                  <div
                    key={tx.id}
                    className="flex items-center justify-between gap-2 p-1.5 rounded bg-card border border-border text-[11px]"
                  >
                    <div className="min-w-0 flex-1">
                      <span className="font-medium text-foreground truncate block">
                        {tx.description}
                      </span>
                      <span className="text-muted-foreground text-[10px] block">
                        {tx.date} • {tx.category_name || 'Uncategorized'}
                      </span>
                    </div>
                    <span className="font-semibold text-foreground tabular-nums">
                      {mask(formatCurrency(Number(tx.amount), insight.currency, locale))}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Score breakdown pills */}
          <div className="pt-2 border-t border-border/40 flex flex-wrap gap-2 text-[10px] text-muted-foreground">
            <span>Impact: {insight.score_breakdown.impact.toFixed(0)}</span>
            <span>•</span>
            <span>Urgency: {insight.score_breakdown.urgency.toFixed(0)}</span>
            <span>•</span>
            <span>Persistence: {insight.score_breakdown.persistence.toFixed(0)}</span>
            <span>•</span>
            <span>Confidence: {insight.score_breakdown.confidence.toFixed(0)}</span>
            <span>•</span>
            <span>Relevance: {insight.score_breakdown.relevance.toFixed(0)}</span>
          </div>
        </div>
      )}
    </div>
  )
}
