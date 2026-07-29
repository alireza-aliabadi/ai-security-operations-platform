import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Badge } from '@/components/ui/Badge'
import { Card } from '@/components/ui/Card'
import { cn } from '@/components/ui/Button'
import { AgentGraph } from '@/features/agents/AgentGraph'
import { ExplainabilityPanel } from '@/features/explain/ExplainabilityPanel'
import { ServiceDependencyGraph } from '@/features/graph/ServiceDependencyGraph'
import { ReportExport } from '@/features/reports/ReportExport'
import { TimelineView } from '@/features/timeline/TimelineView'

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'timeline', label: 'Timeline' },
  { id: 'agents', label: 'Agent graph' },
  { id: 'deps', label: 'Dependencies' },
  { id: 'explain', label: 'Explainability' },
  { id: 'report', label: 'Report' },
] as const

type TabId = (typeof tabs)[number]['id']

export function InvestigationDetailPage() {
  const { id = 'inv-unknown' } = useParams()
  const [tab, setTab] = useState<TabId>('overview')

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="font-mono text-xs text-cyan-400/80">{id}</div>
          <h1 className="text-xl font-semibold text-slate-50">
            Suspicious lateral movement — finance VPC
          </h1>
          <div className="mt-2 flex flex-wrap gap-2">
            <Badge severity="high">high</Badge>
            <Badge>investigating</Badge>
            <Badge severity="info">confidence 82%</Badge>
          </div>
        </div>
      </header>

      <div className="flex flex-wrap gap-1 border-b border-slate-700/70 pb-px">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={cn(
              'rounded-t-md px-3 py-2 text-sm transition-colors',
              tab === t.id
                ? 'bg-slate-800/80 text-cyan-300 border border-b-0 border-slate-600'
                : 'text-slate-400 hover:text-slate-200',
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Card title="Summary">
            <p className="text-sm leading-relaxed text-slate-300">
              Multi-hop authentication from a jump host into finance workloads followed by unusual
              SMB enumeration. Agents correlated Graylog auth failures with Elasticsearch network
              flows and mapped activity to MITRE T1021 / T1078.
            </p>
            <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <div>
                <dt className="text-slate-500">First seen</dt>
                <dd className="text-slate-200">2026-07-29 06:12 UTC</dd>
              </div>
              <div>
                <dt className="text-slate-500">Affected assets</dt>
                <dd className="text-slate-200">12 hosts</dd>
              </div>
              <div>
                <dt className="text-slate-500">IOCs</dt>
                <dd className="font-mono text-xs text-cyan-300">3 IPs · 1 hash</dd>
              </div>
              <div>
                <dt className="text-slate-500">Platforms</dt>
                <dd className="text-slate-200">Graylog, OpenSearch</dd>
              </div>
            </dl>
          </Card>
          <Card title="Remediation">
            <ul className="list-disc space-y-2 pl-4 text-sm text-slate-300">
              <li>Disable compromised service account pending password reset</li>
              <li>Isolate finance-jump-03 from east-west traffic</li>
              <li>Review privileged group membership changes in last 24h</li>
            </ul>
          </Card>
        </div>
      )}

      {tab === 'timeline' && (
        <Card title="Event timeline">
          <TimelineView />
        </Card>
      )}

      {tab === 'agents' && (
        <Card title="Multi-agent execution">
          <div className="h-[420px]">
            <AgentGraph />
          </div>
        </Card>
      )}

      {tab === 'deps' && (
        <Card title="Service dependency graph">
          <div className="h-[420px]">
            <ServiceDependencyGraph />
          </div>
        </Card>
      )}

      {tab === 'explain' && (
        <Card title="Model explainability">
          <ExplainabilityPanel />
        </Card>
      )}

      {tab === 'report' && (
        <Card title="Export report">
          <ReportExport investigationId={id} />
        </Card>
      )}
    </div>
  )
}
