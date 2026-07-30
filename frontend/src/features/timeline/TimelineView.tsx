import { useMemo, useState } from 'react'
import { TimeRangeFilter } from '@/components/ui/TimeRangeFilter'
import {
  resolveTimeRange,
  toDatetimeLocalValue,
  type TimeRangePreset,
} from '@/features/logs/timeFilter'

type TimelineEvent = {
  id: string
  ts: string
  at: string
  title: string
  detail: string
  source: string
}

const now = Date.now()
const events: TimelineEvent[] = [
  {
    id: '1',
    ts: '06:12:04',
    at: new Date(now - 4 * 60 * 60 * 1000).toISOString(),
    title: 'VPN auth success',
    detail: 'user=svc-finance-etl src=203.0.113.44',
    source: 'Graylog',
  },
  {
    id: '2',
    ts: '06:14:21',
    at: new Date(now - 3.5 * 60 * 60 * 1000).toISOString(),
    title: 'RDP to finance-jump-03',
    detail: 'Unusual hour + new device fingerprint',
    source: 'OpenSearch',
  },
  {
    id: '3',
    ts: '06:18:55',
    at: new Date(now - 2 * 60 * 60 * 1000).toISOString(),
    title: 'SMB enumeration',
    detail: '\\\\files\\finance$ — 240 share probes',
    source: 'Graylog',
  },
  {
    id: '4',
    ts: '06:22:10',
    at: new Date(now - 90 * 60 * 1000).toISOString(),
    title: 'Privilege group change',
    detail: 'Added to Domain Admins (pending approval block)',
    source: 'AD audit',
  },
]

export function TimelineView() {
  const end = new Date()
  const start = new Date(end.getTime() - 24 * 60 * 60 * 1000)

  const [preset, setPreset] = useState<TimeRangePreset>('24h')
  const [customStart, setCustomStart] = useState(toDatetimeLocalValue(start))
  const [customEnd, setCustomEnd] = useState(toDatetimeLocalValue(end))
  const [appliedPreset, setAppliedPreset] = useState<TimeRangePreset>('24h')
  const [appliedCustomStart, setAppliedCustomStart] = useState(customStart)
  const [appliedCustomEnd, setAppliedCustomEnd] = useState(customEnd)

  const filtered = useMemo(() => {
    const range = resolveTimeRange(appliedPreset, appliedCustomStart, appliedCustomEnd)
    return events.filter((ev) => {
      const t = new Date(ev.at).getTime()
      if (range.start && t < range.start.getTime()) return false
      if (range.end && t > range.end.getTime()) return false
      return true
    })
  }, [appliedPreset, appliedCustomStart, appliedCustomEnd])

  function applyFilter(nextPreset = preset) {
    setAppliedPreset(nextPreset)
    setAppliedCustomStart(customStart)
    setAppliedCustomEnd(customEnd)
  }

  return (
    <div className="space-y-4">
      <TimeRangeFilter
        preset={preset}
        onPresetChange={setPreset}
        customStart={customStart}
        customEnd={customEnd}
        onCustomStartChange={setCustomStart}
        onCustomEndChange={setCustomEnd}
        onApply={applyFilter}
      />

      {filtered.length === 0 ? (
        <p className="text-sm text-slate-500">No events in the selected time range.</p>
      ) : (
        <ol className="relative ml-3 space-y-0 border-l border-white/15">
          {filtered.map((ev) => (
            <li key={ev.id} className="mb-5 ml-4">
              <span className="absolute -left-1.5 mt-1.5 h-3 w-3 rounded-full border border-cyan-400/80 bg-slate-950 shadow-[0_0_8px_rgba(34,211,238,0.45)]" />
              <div className="flex flex-wrap items-baseline gap-2">
                <time className="font-mono text-xs text-cyan-300/90" dateTime={ev.at}>
                  {ev.ts}
                </time>
                <span className="text-[10px] uppercase tracking-wide text-slate-500">{ev.source}</span>
              </div>
              <div className="mt-0.5 text-sm font-medium text-slate-100">{ev.title}</div>
              <div className="font-mono text-xs text-slate-400">{ev.detail}</div>
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
