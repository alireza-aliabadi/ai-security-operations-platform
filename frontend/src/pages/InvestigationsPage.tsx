import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/lib/api'
import { Badge, type Severity } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { TimeRangeFilter } from '@/components/ui/TimeRangeFilter'
import {
  resolveTimeRange,
  toDatetimeLocalValue,
  type TimeRangePreset,
} from '@/features/logs/timeFilter'

export type Investigation = {
  id: string
  title: string
  status: string
  severity: Severity
  updated_at: string
  confidence?: number
}

const demo: Investigation[] = [
  {
    id: 'inv-1042',
    title: 'Suspicious lateral movement — finance VPC',
    status: 'investigating',
    severity: 'high',
    updated_at: new Date().toISOString(),
    confidence: 0.82,
  },
  {
    id: 'inv-1041',
    title: 'Brute force against VPN gateway',
    status: 'triaged',
    severity: 'medium',
    updated_at: new Date(Date.now() - 3600_000).toISOString(),
    confidence: 0.71,
  },
  {
    id: 'inv-1040',
    title: 'Anomalous DNS to known C2 cluster',
    status: 'open',
    severity: 'critical',
    updated_at: new Date(Date.now() - 7200_000).toISOString(),
    confidence: 0.91,
  },
]

export function InvestigationsPage() {
  const end = new Date()
  const start = new Date(end.getTime() - 7 * 24 * 60 * 60 * 1000)

  const [items, setItems] = useState<Investigation[]>(demo)
  const [preset, setPreset] = useState<TimeRangePreset>('7d')
  const [customStart, setCustomStart] = useState(toDatetimeLocalValue(start))
  const [customEnd, setCustomEnd] = useState(toDatetimeLocalValue(end))
  const [appliedPreset, setAppliedPreset] = useState<TimeRangePreset>('7d')
  const [appliedCustomStart, setAppliedCustomStart] = useState(customStart)
  const [appliedCustomEnd, setAppliedCustomEnd] = useState(customEnd)

  useEffect(() => {
    apiFetch<{ items: Investigation[] }>('/api/v1/investigations')
      .then((data) => setItems(data.items ?? []))
      .catch(() => undefined)
  }, [])

  const filtered = useMemo(() => {
    const range = resolveTimeRange(appliedPreset, appliedCustomStart, appliedCustomEnd)
    return items.filter((inv) => {
      const t = new Date(inv.updated_at).getTime()
      if (Number.isNaN(t)) return true
      if (range.start && t < range.start.getTime()) return false
      if (range.end && t > range.end.getTime()) return false
      return true
    })
  }, [items, appliedPreset, appliedCustomStart, appliedCustomEnd])

  function applyTimeFilter(nextPreset = preset) {
    setAppliedPreset(nextPreset)
    setAppliedCustomStart(customStart)
    setAppliedCustomEnd(customEnd)
  }

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold text-slate-50">Investigations</h1>
        <p className="text-sm text-slate-400">Agent-driven cases across connected platforms.</p>
      </header>

      <Card title="Filters">
        <TimeRangeFilter
          preset={preset}
          onPresetChange={setPreset}
          customStart={customStart}
          customEnd={customEnd}
          onCustomStartChange={setCustomStart}
          onCustomEndChange={setCustomEnd}
          onApply={applyTimeFilter}
        />
      </Card>

      <Card
        title="Cases"
        action={
          <span className="text-[11px] tabular-nums text-slate-500">
            {filtered.length} of {items.length}
          </span>
        }
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="text-[11px] uppercase tracking-wide text-slate-500">
              <tr className="border-b border-white/10">
                <th className="px-2 py-2 font-medium">ID</th>
                <th className="px-2 py-2 font-medium">Title</th>
                <th className="px-2 py-2 font-medium">Severity</th>
                <th className="px-2 py-2 font-medium">Status</th>
                <th className="px-2 py-2 font-medium">Confidence</th>
                <th className="px-2 py-2 font-medium">Updated</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-2 py-8 text-center text-slate-500">
                    No investigations in the selected time range.
                  </td>
                </tr>
              ) : (
                filtered.map((inv) => (
                  <tr key={inv.id} className="border-b border-white/5 hover:bg-white/5">
                    <td className="px-2 py-2.5 font-mono text-xs text-cyan-400/90">
                      <Link to={`/investigations/${inv.id}`}>{inv.id}</Link>
                    </td>
                    <td className="px-2 py-2.5">
                      <Link
                        to={`/investigations/${inv.id}`}
                        className="text-slate-100 hover:underline"
                      >
                        {inv.title}
                      </Link>
                    </td>
                    <td className="px-2 py-2.5">
                      <Badge severity={inv.severity}>{inv.severity}</Badge>
                    </td>
                    <td className="px-2 py-2.5 capitalize text-slate-300">{inv.status}</td>
                    <td className="px-2 py-2.5 tabular-nums text-slate-300">
                      {inv.confidence != null ? `${Math.round(inv.confidence * 100)}%` : '—'}
                    </td>
                    <td className="px-2 py-2.5 text-slate-400">
                      {new Date(inv.updated_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
