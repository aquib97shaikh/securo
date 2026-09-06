import { AlertCircle, AlertTriangle, Eye, Sparkles } from 'lucide-react'
import type { GuidanceSummaryStats } from '@/types'

interface GuidanceSummaryStripProps {
  summary?: GuidanceSummaryStats | null
  currency?: string
  onSelectSeverity?: (severity: string) => void
  selectedSeverity?: string
}

export function GuidanceSummaryStrip({
  summary,
  onSelectSeverity,
  selectedSeverity,
}: GuidanceSummaryStripProps) {
  if (!summary) return null

  const items = [
    {
      id: 'urgent',
      label: 'Urgent now',
      count: summary.urgent_count,
      color: 'text-rose-600 dark:text-rose-400',
      border: 'border-rose-500/30',
      bg: 'bg-rose-500/5 hover:bg-rose-500/10',
      icon: AlertCircle,
    },
    {
      id: 'action_needed',
      label: 'Needs attention',
      count: summary.action_needed_count,
      color: 'text-amber-600 dark:text-amber-400',
      border: 'border-amber-500/30',
      bg: 'bg-amber-500/5 hover:bg-amber-500/10',
      icon: AlertTriangle,
    },
    {
      id: 'watch',
      label: 'Watch list',
      count: summary.watch_count,
      color: 'text-blue-600 dark:text-blue-400',
      border: 'border-blue-500/30',
      bg: 'bg-blue-500/5 hover:bg-blue-500/10',
      icon: Eye,
    },
    {
      id: 'informational',
      label: 'Improve over time',
      count: summary.informational_count,
      color: 'text-emerald-600 dark:text-emerald-400',
      border: 'border-emerald-500/30',
      bg: 'bg-emerald-500/5 hover:bg-emerald-500/10',
      icon: Sparkles,
    },
  ]

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {items.map((item) => {
        const Icon = item.icon
        const isSelected = selectedSeverity === item.id
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onSelectSeverity?.(item.id)}
            className={`flex items-center gap-3 p-3.5 rounded-xl border text-left transition-all ${item.border} ${
              item.bg
            } ${isSelected ? 'ring-2 ring-primary ring-offset-2' : ''}`}
          >
            <div className={`p-2 rounded-lg bg-card shadow-xs ${item.color}`}>
              <Icon size={18} />
            </div>
            <div>
              <p className="text-xl font-bold tabular-nums text-foreground leading-none">
                {item.count}
              </p>
              <p className="text-xs text-muted-foreground font-medium mt-1 leading-tight">
                {item.label}
              </p>
            </div>
          </button>
        )
      })}
    </div>
  )
}
