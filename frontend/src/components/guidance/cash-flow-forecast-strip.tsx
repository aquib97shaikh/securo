import { useMemo } from 'react'
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from 'recharts'
import { AlertCircle } from 'lucide-react'
import { formatCurrency } from '@/lib/format'
import { useDisplayLocale } from '@/hooks/use-display-locale'
import { usePrivacyMode } from '@/hooks/use-privacy-mode'
import type { CashFlowForecastStripItem } from '@/types'

interface CashFlowForecastStripProps {
  strip?: CashFlowForecastStripItem[]
  currency?: string
  safetyBuffer?: number
}

export function CashFlowForecastStrip({
  strip = [],
  currency = 'USD',
  safetyBuffer = 0,
}: CashFlowForecastStripProps) {
  const locale = useDisplayLocale()
  const { mask } = usePrivacyMode()

  const chartData = useMemo(() => {
    return strip.map((item) => ({
      date: item.date,
      label: item.day_label,
      balance: item.projected_balance,
      hasShortfall: item.has_shortfall,
      events: item.events,
    }))
  }, [strip])

  const lowestPoint = useMemo(() => {
    if (!strip.length) return null
    return strip.reduce((min, cur) =>
      cur.projected_balance < min.projected_balance ? cur : min
    )
  }, [strip])

  const hasAnyShortfall = strip.some((s) => s.has_shortfall)

  if (!strip || strip.length === 0) return null

  return (
    <div className="bg-card rounded-xl border border-border shadow-xs p-4 sm:p-5">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-foreground">Upcoming 14-Day Cash Flow Forecast</h3>
            {hasAnyShortfall && (
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-600 dark:text-rose-400 px-2 py-0.5 rounded-full bg-rose-500/10">
                <AlertCircle size={12} />
                Shortfall risk detected
              </span>
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">
            Projected daily balance based on active recurring schedules and baseline burn
          </p>
        </div>

        {lowestPoint && (
          <div className="text-right">
            <span className="text-[11px] text-muted-foreground block">Projected 14-day low</span>
            <span
              className={`text-sm font-bold tabular-nums ${
                lowestPoint.projected_balance < 0
                  ? 'text-rose-600 dark:text-rose-400'
                  : lowestPoint.projected_balance < safetyBuffer
                  ? 'text-amber-600 dark:text-amber-400'
                  : 'text-foreground'
              }`}
            >
              {mask(formatCurrency(lowestPoint.projected_balance, currency, locale))}
            </span>
          </div>
        )}
      </div>

      {/* Mini 14-Day Timeline Chart */}
      <div className="h-32 w-full mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
            <defs>
              <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.25} />
                <stop offset="95%" stopColor="var(--primary)" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="label"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 10, fill: 'var(--muted-foreground)' }}
            />
            <YAxis
              hide
              domain={['auto', 'auto']}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null
                const item = payload[0].payload
                return (
                  <div className="rounded-lg bg-popover p-2.5 shadow-md border border-border text-xs">
                    <span className="font-semibold text-popover-foreground block mb-1">
                      {item.label}
                    </span>
                    <div className="text-sm font-bold tabular-nums text-foreground">
                      {mask(formatCurrency(item.balance, currency, locale))}
                    </div>
                    {item.events?.length > 0 && (
                      <div className="mt-1.5 pt-1.5 border-t border-border space-y-0.5">
                        {item.events.map((ev: string, idx: number) => (
                          <span key={idx} className="block text-[11px] text-muted-foreground">
                            • {ev}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )
              }}
            />
            {safetyBuffer > 0 && (
              <ReferenceLine
                y={safetyBuffer}
                stroke="#f59e0b"
                strokeDasharray="3 3"
                label={{
                  value: 'Safety buffer',
                  fill: '#f59e0b',
                  fontSize: 10,
                  position: 'insideTopRight',
                }}
              />
            )}
            <Area
              type="monotone"
              dataKey="balance"
              stroke="var(--primary)"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#forecastGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
