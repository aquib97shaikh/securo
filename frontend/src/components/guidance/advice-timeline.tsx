import { Check, Clock, ThumbsDown, ThumbsUp } from 'lucide-react'
import type { GuidanceHistoryItem } from '@/types'

interface AdviceTimelineProps {
  items: GuidanceHistoryItem[]
}

export function AdviceTimeline({ items }: AdviceTimelineProps) {
  if (!items || items.length === 0) {
    return (
      <div className="text-center py-10 text-muted-foreground text-xs">
        No interaction history yet. Snoozed, dismissed, or acted-on recommendations will appear here.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div
          key={item.id}
          className="p-3.5 rounded-xl border border-border bg-card flex items-start justify-between gap-3 text-xs"
        >
          <div className="space-y-1 min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-foreground truncate">{item.title}</span>
              <span
                className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                  item.status === 'dismissed'
                    ? 'bg-muted text-muted-foreground'
                    : item.status === 'snoozed'
                    ? 'bg-amber-500/10 text-amber-600'
                    : 'bg-primary/10 text-primary'
                }`}
              >
                {item.status}
              </span>
            </div>

            {item.action_taken && (
              <p className="text-emerald-600 text-[11px] font-medium flex items-center gap-1">
                <Check size={12} />
                Action executed: {item.action_taken}
              </p>
            )}

            {item.snoozed_until && (
              <p className="text-muted-foreground text-[11px] flex items-center gap-1">
                <Clock size={12} />
                Snoozed until {new Date(item.snoozed_until).toLocaleDateString()}
              </p>
            )}
          </div>

          <div className="flex items-center gap-1.5 shrink-0">
            {item.is_helpful === true && (
              <span className="p-1 text-emerald-600 bg-emerald-500/10 rounded" title="Rated helpful">
                <ThumbsUp size={12} />
              </span>
            )}
            {item.is_helpful === false && (
              <span className="p-1 text-rose-600 bg-rose-500/10 rounded" title="Rated not helpful">
                <ThumbsDown size={12} />
              </span>
            )}
            <span className="text-[10px] text-muted-foreground tabular-nums">
              {new Date(item.updated_at).toLocaleDateString()}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}
