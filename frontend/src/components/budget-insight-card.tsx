import { AlertTriangle, CheckCircle2, Info, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { BudgetInsight } from '@/types'

const severityConfig = {
  warning: {
    icon: AlertTriangle,
    bg: 'bg-amber-500/10 dark:bg-amber-500/15',
    border: 'border-amber-500/30',
    iconColor: 'text-amber-500',
    titleColor: 'text-amber-700 dark:text-amber-400',
  },
  info: {
    icon: Info,
    bg: 'bg-blue-500/10 dark:bg-blue-500/15',
    border: 'border-blue-500/30',
    iconColor: 'text-blue-500',
    titleColor: 'text-blue-700 dark:text-blue-400',
  },
  success: {
    icon: CheckCircle2,
    bg: 'bg-emerald-500/10 dark:bg-emerald-500/15',
    border: 'border-emerald-500/30',
    iconColor: 'text-emerald-500',
    titleColor: 'text-emerald-700 dark:text-emerald-400',
  },
}

interface BudgetInsightCardProps {
  insight: BudgetInsight
  onDismiss?: (id: string) => void
}

export function BudgetInsightCard({ insight, onDismiss }: BudgetInsightCardProps) {
  const navigate = useNavigate()
  const config = severityConfig[insight.severity] || severityConfig.info
  const Icon = config.icon

  return (
    <div
      className={`relative rounded-xl border ${config.border} ${config.bg} p-4 transition-all hover:shadow-sm min-w-[280px] max-w-[360px] flex-shrink-0`}
    >
      {onDismiss && (
        <button
          onClick={() => onDismiss(insight.id)}
          className="absolute top-2.5 right-2.5 p-1 rounded-md text-muted-foreground/60 hover:text-muted-foreground hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
          aria-label="Dismiss"
        >
          <X size={14} />
        </button>
      )}

      <div className="flex gap-3">
        <div className={`mt-0.5 ${config.iconColor}`}>
          <Icon size={18} />
        </div>
        <div className="flex-1 min-w-0 pr-4">
          <p className={`text-sm font-semibold ${config.titleColor} leading-tight`}>
            {insight.title}
          </p>
          <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
            {insight.description}
          </p>
          {insight.suggestion && (
            <p className="text-xs text-muted-foreground/80 mt-1.5 italic">
              {insight.suggestion}
            </p>
          )}
          {insight.action_url && (
            <button
              onClick={() => navigate(insight.action_url!)}
              className="text-xs font-medium text-primary hover:text-primary/80 mt-2 transition-colors"
            >
              View details →
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
