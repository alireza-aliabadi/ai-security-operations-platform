import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/lib/api'
import { Badge, type Severity } from '@/components/ui/Badge'
import { Card, glassCardClass } from '@/components/ui/Card'
import { cn } from '@/components/ui/Button'
import { SeverityHeatmap } from '@/features/heatmap/SeverityHeatmap'
import { LiveLogStream } from '@/features/logs/LiveLogStream'

type Summary = {
  open_investigations: number
  critical_alerts: number
  pending_approvals: number
  connectors_healthy: number
  connectors_total: number
}

const fallback: Summary = {
  open_investigations: 12,
  critical_alerts: 3,
  pending_approvals: 2,
  connectors_healthy: 4,
  connectors_total: 5,
}

const recent = [
  { id: 'inv-1042', title: 'Suspicious lateral movement — finance VPC', severity: 'high' as Severity },
  { id: 'inv-1041', title: 'Brute force against VPN gateway', severity: 'medium' as Severity },
  { id: 'inv-1040', title: 'Anomalous DNS to known C2 cluster', severity: 'critical' as Severity },
]

export function DashboardPage() {
  const [summary, setSummary] = useState<Summary>(fallback)

  useEffect(() => {
    let cancelled = false
    apiFetch<Summary>('/api/v1/dashboard/summary')
      .then((data) => {
        if (!cancelled) setSummary(data)
      })
      .catch(() => {
        /* keep demo fallback while API matures */
      })
    return () => {
      cancelled = true
    }
  }, [])

  const cards = [
    { label: 'Open investigations', value: summary.open_investigations },
    { label: 'Critical alerts', value: summary.critical_alerts },
    { label: 'Pending approvals', value: summary.pending_approvals },
    {
      label: 'Connectors',
      value: `${summary.connectors_healthy}/${summary.connectors_total}`,
    },
  ]

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold text-slate-50">Operations dashboard</h1>
        <p className="text-sm text-slate-400">Live posture across investigations and connectors.</p>
      </header>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((c) => (
          <div key={c.label} className={cn(glassCardClass, 'px-4 py-3')}>
            <div className="text-[11px] uppercase tracking-wide text-slate-500">{c.label}</div>
            <div className="mt-1 text-2xl font-semibold tabular-nums text-cyan-300">{c.value}</div>
          </div>
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Severity heatmap (7d)">
          <SeverityHeatmap />
        </Card>
        <Card title="Recent investigations">
          <ul className="space-y-2">
            {recent.map((r) => (
              <li key={r.id}>
                <Link
                  to={`/investigations/${r.id}`}
                  className="flex items-center justify-between gap-3 rounded-xl border border-transparent px-2 py-2 transition-colors hover:border-white/10 hover:bg-white/5"
                >
                  <div>
                    <div className="font-mono text-[11px] text-slate-500">{r.id}</div>
                    <div className="text-sm text-slate-200">{r.title}</div>
                  </div>
                  <Badge severity={r.severity}>{r.severity}</Badge>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card title="Live log stream" padded={false}>
        <LiveLogStream />
      </Card>
    </div>
  )
}
