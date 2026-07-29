import { useEffect, useState } from 'react'
import { apiFetch } from '@/lib/api'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'

type Approval = {
  id: string
  title: string
  action: string
  risk: 'high' | 'medium' | 'low'
  requested_by: string
  status: 'pending' | 'approved' | 'rejected'
}

type ApprovalApi = {
  id: string
  investigation_id: string
  action: string
  status: Approval['status']
  requested_by: string | null
  reason: string | null
}

function inferRisk(action: string): Approval['risk'] {
  const high = /isolate|disable|delete|revoke|block|quarantine/i
  const low = /notify|log|tag|annotate/i
  if (high.test(action)) return 'high'
  if (low.test(action)) return 'low'
  return 'medium'
}

function mapApproval(row: ApprovalApi): Approval {
  return {
    id: row.id,
    title: row.reason?.trim() || row.action,
    action: row.action,
    risk: inferRisk(row.action),
    requested_by: row.requested_by ?? 'unknown',
    status: row.status,
  }
}

function parseApprovals(data: ApprovalApi[] | { items?: ApprovalApi[] }): Approval[] {
  const rows = Array.isArray(data) ? data : (data.items ?? [])
  return rows.map(mapApproval)
}

export function ApprovalsPage() {
  const [items, setItems] = useState<Approval[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    apiFetch<ApprovalApi[] | { items?: ApprovalApi[] }>('/api/v1/approvals')
      .then((data) => setItems(parseApprovals(data)))
      .catch(() => undefined)
      .finally(() => setLoading(false))
  }, [])

  function decide(id: string, status: 'approved' | 'rejected') {
    setItems((prev) => prev.map((a) => (a.id === id ? { ...a, status } : a)))
    apiFetch(`/api/v1/approvals/${id}/decide`, {
      method: 'POST',
      body: { status },
    }).catch(() => undefined)
  }

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-xl font-semibold text-slate-50">Human approvals</h1>
        <p className="text-sm text-slate-400">High-impact actions require analyst confirmation.</p>
      </header>
      <div className="space-y-3">
        {loading && (
          <Card>
            <p className="text-sm text-slate-400">Loading approvals…</p>
          </Card>
        )}
        {!loading && items.length === 0 && (
          <Card>
            <p className="text-sm text-slate-400">No pending approvals.</p>
          </Card>
        )}
        {items.map((a) => (
          <Card key={a.id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="font-medium text-slate-100">{a.title}</div>
                <div className="mt-1 font-mono text-xs text-slate-500">{a.action}</div>
                <div className="mt-2 flex gap-2">
                  <Badge severity={a.risk === 'high' ? 'high' : a.risk === 'medium' ? 'medium' : 'low'}>
                    {a.risk} risk
                  </Badge>
                  <Badge>{a.status}</Badge>
                </div>
              </div>
              {a.status === 'pending' && (
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => decide(a.id, 'approved')}>
                    Approve
                  </Button>
                  <Button size="sm" variant="danger" onClick={() => decide(a.id, 'rejected')}>
                    Reject
                  </Button>
                </div>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
