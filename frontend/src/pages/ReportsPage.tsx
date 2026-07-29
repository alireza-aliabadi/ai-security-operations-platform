import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiFetch } from '@/lib/api'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { ReportExport } from '@/features/reports/ReportExport'

type Report = {
  id: string
  investigation_id: string
  title: string
  kind: 'executive' | 'technical'
  created_at: string
}

const demo: Report[] = [
  {
    id: 'rpt-9',
    investigation_id: 'inv-1042',
    title: 'Lateral movement — executive brief',
    kind: 'executive',
    created_at: new Date().toISOString(),
  },
  {
    id: 'rpt-8',
    investigation_id: 'inv-1040',
    title: 'C2 DNS — technical dossier',
    kind: 'technical',
    created_at: new Date(Date.now() - 86400_000).toISOString(),
  },
]

export function ReportsPage() {
  const [items, setItems] = useState<Report[]>(demo)

  useEffect(() => {
    apiFetch<{ items: Report[] }>('/api/v1/reports')
      .then((d) => setItems(d.items))
      .catch(() => undefined)
  }, [])

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold text-slate-50">Reports</h1>
        <p className="text-sm text-slate-400">Generated executive and technical artifacts.</p>
      </header>
      <Card title="Recent">
        <ul className="divide-y divide-slate-800">
          {items.map((r) => (
            <li key={r.id} className="flex flex-wrap items-center justify-between gap-3 py-3">
              <div>
                <div className="text-sm text-slate-100">{r.title}</div>
                <div className="mt-1 flex gap-2">
                  <Badge severity="info">{r.kind}</Badge>
                  <Link
                    to={`/investigations/${r.investigation_id}`}
                    className="font-mono text-xs text-cyan-400 hover:underline"
                  >
                    {r.investigation_id}
                  </Link>
                </div>
              </div>
              <div className="text-xs text-slate-500">{new Date(r.created_at).toLocaleString()}</div>
            </li>
          ))}
        </ul>
      </Card>
      <Card title="Generate">
        <ReportExport investigationId="inv-1042" />
      </Card>
    </div>
  )
}
