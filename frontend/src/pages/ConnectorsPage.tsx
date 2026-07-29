import { useEffect, useState } from 'react'
import { apiFetch } from '@/lib/api'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'

type Connector = {
  id: string
  name: string
  platform: string
  status: 'healthy' | 'degraded' | 'down'
  last_sync?: string
}

const demo: Connector[] = [
  { id: 'c1', name: 'Prod Graylog', platform: 'graylog', status: 'healthy' },
  { id: 'c2', name: 'Security OpenSearch', platform: 'opensearch', status: 'healthy' },
  { id: 'c3', name: 'Central Loki', platform: 'loki', status: 'healthy' },
  { id: 'c4', name: 'Splunk ES', platform: 'splunk', status: 'degraded' },
  { id: 'c5', name: 'Datadog US1', platform: 'datadog', status: 'down' },
]

export function ConnectorsPage() {
  const [items, setItems] = useState<Connector[]>(demo)

  useEffect(() => {
    apiFetch<{ items: Connector[] }>('/api/v1/connectors')
      .then((d) => setItems(d.items))
      .catch(() => undefined)
  }, [])

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold text-slate-50">Connectors</h1>
        <p className="text-sm text-slate-400">Log platform integrations (mock mode supported).</p>
      </header>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {items.map((c) => (
          <Card key={c.id}>
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="font-medium text-slate-100">{c.name}</div>
                <div className="mt-0.5 font-mono text-xs uppercase text-slate-500">{c.platform}</div>
              </div>
              <Badge
                severity={
                  c.status === 'healthy' ? 'low' : c.status === 'degraded' ? 'medium' : 'critical'
                }
              >
                {c.status}
              </Badge>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
