import { Button, cn } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import {
  TIME_PRESET_LABELS,
  type TimeRangePreset,
} from '@/features/logs/timeFilter'

export type TimeRangeFilterProps = {
  preset: TimeRangePreset
  onPresetChange: (preset: TimeRangePreset) => void
  customStart: string
  customEnd: string
  onCustomStartChange: (value: string) => void
  onCustomEndChange: (value: string) => void
  onApply?: (nextPreset?: TimeRangePreset) => void
  loading?: boolean
  className?: string
}

const PRESETS: TimeRangePreset[] = ['15m', '1h', '6h', '24h', '7d', 'all', 'custom']

export function TimeRangeFilter({
  preset,
  onPresetChange,
  customStart,
  customEnd,
  onCustomStartChange,
  onCustomEndChange,
  onApply,
  loading = false,
  className,
}: TimeRangeFilterProps) {
  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-400">
          Time range
        </span>
        {onApply && (
          <Button size="sm" variant="outline" onClick={() => onApply()} disabled={loading}>
            {loading ? 'Applying…' : 'Apply'}
          </Button>
        )}
      </div>

      <div className="flex flex-wrap gap-1.5">
        {PRESETS.map((p) => (
          <button
            key={p}
            type="button"
            onClick={() => {
              onPresetChange(p)
              if (p !== 'custom' && onApply) onApply(p)
            }}
            className={cn(
              'rounded-lg border px-2.5 py-1 text-[11px] font-medium transition-colors backdrop-blur-sm',
              preset === p
                ? 'border-cyan-400/40 bg-cyan-500/20 text-cyan-200 shadow-[0_0_20px_rgba(34,211,238,0.12)]'
                : 'border-white/10 bg-white/5 text-slate-400 hover:border-white/20 hover:bg-white/10 hover:text-slate-200',
            )}
          >
            {TIME_PRESET_LABELS[p]}
          </button>
        ))}
      </div>

      {preset === 'custom' && (
        <div className="grid gap-2 sm:grid-cols-2">
          <Input
            label="From"
            type="datetime-local"
            value={customStart}
            onChange={(e) => onCustomStartChange(e.target.value)}
          />
          <Input
            label="To"
            type="datetime-local"
            value={customEnd}
            onChange={(e) => onCustomEndChange(e.target.value)}
          />
        </div>
      )}
    </div>
  )
}
