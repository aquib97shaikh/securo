import { Link } from 'react-router-dom'
import { ChevronRight, ShieldAlert } from 'lucide-react'
import { formatCurrency } from '@/lib/format'
import { useDisplayLocale } from '@/hooks/use-display-locale'
import { usePrivacyMode } from '@/hooks/use-privacy-mode'
import type { MonthAtRiskItem } from '@/types'

interface MonthAtRiskCardProps {
  items?: MonthAtRiskItem[]
  currency?: string
}

export function MonthAtRiskCard({ items = [], currency = 'USD' }: MonthAtRiskCardProps) {
  const locale = useDisplayLocale()
  const { mask } = usePrivacyMode()

  if (!items || items.length === 0) return null

  return (
    <div className="bg-card rounded-xl border border-border shadow-xs p-4 sm:p-5">
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded-md bg-amber-500/10 text-amber-600">
            <ShieldAlert size={16} />
          </div>
          <h3 className="text-sm font-semibold text-foreground">This Month at Risk</h3>
        </div>
        <span className="text-xs text-muted-foreground">{items.length} items flagged</span>
      </div>

      <div className="divide-y divide-border">
        {items.map((item) => (
          <div key={item.id} className="py-2.5 flex items-center justify-between gap-3 text-xs">
            <div className="min-w-0 flex-1">
              <span className="font-medium text-foreground truncate block">{item.name}</span>
              <span className="text-[11px] text-muted-foreground">{item.status_label}</span>
            </div>

            <div className="text-right flex items-center gap-2 shrink-0">
              <span className="font-semibold tabular-nums text-foreground">
                {mask(formatCurrency(Number(item.amount), currency, locale))}
              </span>
              {item.url && (
                <Link
                  to={item.url}
                  className="text-muted-foreground hover:text-foreground transition-colors p-1"
                >
                  <ChevronRight size={14} />
                </Link>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
