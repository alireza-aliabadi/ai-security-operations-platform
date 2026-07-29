import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { apiFetch } from '@/lib/api'

type Props = {
  investigationId: string
}

export function ReportExport({ investigationId }: Props) {
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState<string | null>(null)

  async function exportReport(kind: 'executive' | 'technical') {
    setBusy(true)
    setStatus(null)
    try {
      await apiFetch(`/api/v1/investigations/${investigationId}/reports`, {
        method: 'POST',
        body: { kind },
      })
      setStatus(`${kind} report queued for ${investigationId}`)
    } catch {
      const blob = new Blob(
        [
          `# AISOC ${kind} report\n\nInvestigation: ${investigationId}\nGenerated: ${new Date().toISOString()}\n`,
        ],
        { type: 'text/markdown' },
      )
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${investigationId}-${kind}.md`
      a.click()
      URL.revokeObjectURL(url)
      setStatus(`Downloaded local ${kind} stub (API unavailable)`)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-400">
        Export executive or technical reports for <span className="font-mono text-cyan-400">{investigationId}</span>.
      </p>
      <div className="flex flex-wrap gap-2">
        <Button disabled={busy} onClick={() => exportReport('executive')}>
          Executive PDF/MD
        </Button>
        <Button variant="outline" disabled={busy} onClick={() => exportReport('technical')}>
          Technical dossier
        </Button>
      </div>
      {status && <p className="text-xs text-slate-400">{status}</p>}
    </div>
  )
}
