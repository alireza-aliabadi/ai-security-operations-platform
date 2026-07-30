import { useEffect, useState, type FormEvent } from 'react'
import { ApiError, apiFetch } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'

const PLATFORMS = [
  'graylog',
  'elasticsearch',
  'opensearch',
  'loki',
  'splunk',
  'datadog',
] as const

type Platform = (typeof PLATFORMS)[number]

type Connector = {
  id: string
  name: string
  platform: Platform | string
  base_url: string
  enabled: boolean
  meta: Record<string, unknown>
  created_at: string
  updated_at: string
  has_credentials: boolean
}

type ConnectorForm = {
  name: string
  platform: Platform
  base_url: string
  token: string
  username: string
  password: string
  api_key: string
  app_key: string
  enabled: boolean
  streams: string
}

const emptyForm = (): ConnectorForm => ({
  name: '',
  platform: 'graylog',
  base_url: 'https://',
  token: '',
  username: '',
  password: '',
  api_key: '',
  app_key: '',
  enabled: true,
  streams: '',
})

function buildCredentials(form: ConnectorForm): Record<string, string> {
  const creds: Record<string, string> = {}
  if (form.token.trim()) creds.token = form.token.trim()
  if (form.username.trim()) creds.username = form.username.trim()
  if (form.password) creds.password = form.password
  if (form.api_key.trim()) creds.api_key = form.api_key.trim()
  if (form.app_key.trim()) creds.app_key = form.app_key.trim()
  return creds
}

function credentialHints(platform: Platform): string {
  switch (platform) {
    case 'graylog':
      return 'Use a Graylog API token (Users → Tokens).'
    case 'elasticsearch':
    case 'opensearch':
      return 'Use username/password or an API key.'
    case 'loki':
      return 'Optional bearer token if Loki is authenticated.'
    case 'splunk':
      return 'Use a Splunk auth token.'
    case 'datadog':
      return 'Provide Datadog API key and Application key.'
    default:
      return 'Provide credentials for this platform.'
  }
}

export function ConnectorsPage() {
  const { user } = useAuth()
  const canWrite = (user?.roles ?? []).includes('admin')

  const [items, setItems] = useState<Connector[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Connector | null>(null)
  const [form, setForm] = useState<ConnectorForm>(emptyForm)
  const [saving, setSaving] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  async function loadConnectors() {
    setLoading(true)
    setError(null)
    try {
      const data = await apiFetch<{ items: Connector[] }>('/api/v1/connectors')
      setItems(data.items)
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError('Failed to load connectors')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadConnectors()
  }, [])

  function openCreate() {
    setEditing(null)
    setForm(emptyForm())
    setFormOpen(true)
    setError(null)
  }

  function openEdit(connector: Connector) {
    setEditing(connector)
    setForm({
      ...emptyForm(),
      name: connector.name,
      platform: (PLATFORMS.includes(connector.platform as Platform)
        ? connector.platform
        : 'graylog') as Platform,
      base_url: connector.base_url,
      enabled: connector.enabled,
      streams:
        typeof connector.meta?.streams === 'string'
          ? connector.meta.streams
          : Array.isArray(connector.meta?.streams)
            ? (connector.meta.streams as string[]).join(', ')
            : '',
    })
    setFormOpen(true)
    setError(null)
  }

  function closeForm() {
    setFormOpen(false)
    setEditing(null)
    setForm(emptyForm())
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!canWrite) return
    setSaving(true)
    setError(null)

    const streams = form.streams
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
    const meta: Record<string, unknown> = {}
    if (streams.length) meta.streams = streams

    const credentials = buildCredentials(form)

    try {
      if (editing) {
        const body: Record<string, unknown> = {
          name: form.name.trim(),
          base_url: form.base_url.trim(),
          enabled: form.enabled,
          meta,
        }
        if (Object.keys(credentials).length) body.credentials = credentials
        await apiFetch(`/api/v1/connectors/${editing.id}`, {
          method: 'PATCH',
          body,
        })
      } else {
        await apiFetch('/api/v1/connectors', {
          method: 'POST',
          body: {
            name: form.name.trim(),
            platform: form.platform,
            base_url: form.base_url.trim(),
            credentials,
            enabled: form.enabled,
            meta,
          },
        })
      }
      closeForm()
      await loadConnectors()
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError('Failed to save connector')
    } finally {
      setSaving(false)
    }
  }

  async function onDelete(connector: Connector) {
    if (!canWrite) return
    if (!window.confirm(`Delete connector “${connector.name}”?`)) return
    setDeletingId(connector.id)
    setError(null)
    try {
      await apiFetch(`/api/v1/connectors/${connector.id}`, { method: 'DELETE' })
      await loadConnectors()
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError('Failed to delete connector')
    } finally {
      setDeletingId(null)
    }
  }

  async function onToggleEnabled(connector: Connector) {
    if (!canWrite) return
    setError(null)
    try {
      await apiFetch(`/api/v1/connectors/${connector.id}`, {
        method: 'PATCH',
        body: { enabled: !connector.enabled },
      })
      await loadConnectors()
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError('Failed to update connector')
    }
  }

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold text-slate-50">Connectors</h1>
          <p className="text-sm text-slate-400">
            Configure log platforms (Graylog, Elasticsearch, Loki, Splunk, …).
          </p>
        </div>
        {canWrite && (
          <Button onClick={openCreate} disabled={formOpen}>
            Add connector
          </Button>
        )}
      </header>

      {!canWrite && (
        <Card>
          <p className="text-sm text-slate-400">
            You can view connectors. Creating or editing requires an{' '}
            <span className="text-slate-200">admin</span> account.
          </p>
        </Card>
      )}

      <Card>
        <p className="text-sm text-amber-200/90">
          Configurations are stored encrypted. Search still uses the mock corpus until live HTTP
          clients are enabled (`CONNECTOR_MODE=live` + platform live connector).
        </p>
      </Card>

      {error && (
        <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      {formOpen && canWrite && (
        <Card>
          <form className="space-y-4" onSubmit={onSubmit}>
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-base font-medium text-slate-100">
                {editing ? `Edit ${editing.name}` : 'New connector'}
              </h2>
              <Button type="button" variant="ghost" size="sm" onClick={closeForm}>
                Cancel
              </Button>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <Input
                label="Name"
                name="name"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="prod-graylog"
                required
              />

              <label className="flex w-full flex-col gap-1.5 text-sm">
                <span className="text-slate-400">Platform</span>
                <select
                  name="platform"
                  className="w-full rounded-md border border-slate-600 bg-slate-950/80 px-3 py-2 text-slate-100 outline-none focus:border-cyan-500/70 focus:ring-1 focus:ring-cyan-500/40 disabled:opacity-60"
                  value={form.platform}
                  disabled={Boolean(editing)}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, platform: e.target.value as Platform }))
                  }
                >
                  {PLATFORMS.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </label>

              <div className="md:col-span-2">
                <Input
                  label="Base URL"
                  name="base_url"
                  value={form.base_url}
                  onChange={(e) => setForm((f) => ({ ...f, base_url: e.target.value }))}
                  placeholder="https://graylog.example.com"
                  required
                />
              </div>

              <div className="md:col-span-2 text-xs text-slate-500">
                {credentialHints(form.platform)}
                {editing ? ' Leave credential fields blank to keep existing secrets.' : null}
              </div>

              {(form.platform === 'graylog' ||
                form.platform === 'loki' ||
                form.platform === 'splunk') && (
                <Input
                  label="API token"
                  name="token"
                  type="password"
                  autoComplete="off"
                  value={form.token}
                  onChange={(e) => setForm((f) => ({ ...f, token: e.target.value }))}
                  placeholder={editing ? '••••••••' : 'token'}
                />
              )}

              {(form.platform === 'elasticsearch' || form.platform === 'opensearch') && (
                <>
                  <Input
                    label="Username"
                    name="username"
                    value={form.username}
                    onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                  />
                  <Input
                    label="Password"
                    name="password"
                    type="password"
                    autoComplete="new-password"
                    value={form.password}
                    onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                  />
                  <Input
                    label="API key (optional)"
                    name="api_key"
                    type="password"
                    autoComplete="off"
                    value={form.api_key}
                    onChange={(e) => setForm((f) => ({ ...f, api_key: e.target.value }))}
                  />
                </>
              )}

              {form.platform === 'datadog' && (
                <>
                  <Input
                    label="API key"
                    name="api_key"
                    type="password"
                    autoComplete="off"
                    value={form.api_key}
                    onChange={(e) => setForm((f) => ({ ...f, api_key: e.target.value }))}
                  />
                  <Input
                    label="Application key"
                    name="app_key"
                    type="password"
                    autoComplete="off"
                    value={form.app_key}
                    onChange={(e) => setForm((f) => ({ ...f, app_key: e.target.value }))}
                  />
                </>
              )}

              <Input
                label="Streams / indices (comma-separated, optional)"
                name="streams"
                value={form.streams}
                onChange={(e) => setForm((f) => ({ ...f, streams: e.target.value }))}
                placeholder="security, windows-security"
              />

              <label className="flex items-center gap-2 self-end pb-2 text-sm text-slate-300">
                <input
                  type="checkbox"
                  checked={form.enabled}
                  onChange={(e) => setForm((f) => ({ ...f, enabled: e.target.checked }))}
                  className="size-4 rounded border-slate-600 bg-slate-950"
                />
                Enabled
              </label>
            </div>

            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={closeForm}>
                Cancel
              </Button>
              <Button type="submit" disabled={saving}>
                {saving ? 'Saving…' : editing ? 'Save changes' : 'Create connector'}
              </Button>
            </div>
          </form>
        </Card>
      )}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {loading && (
          <Card>
            <p className="text-sm text-slate-400">Loading connectors…</p>
          </Card>
        )}
        {!loading && items.length === 0 && (
          <Card>
            <p className="text-sm text-slate-400">
              No connectors configured yet.
              {canWrite ? ' Use “Add connector” to register Graylog or another log platform.' : ''}
            </p>
          </Card>
        )}
        {items.map((c) => (
          <Card key={c.id}>
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <div className="truncate font-medium text-slate-100">{c.name}</div>
                <div className="mt-0.5 font-mono text-xs uppercase text-slate-500">{c.platform}</div>
                <div className="mt-2 truncate text-xs text-slate-400" title={c.base_url}>
                  {c.base_url}
                </div>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <Badge severity={c.enabled ? 'low' : 'medium'}>
                  {c.enabled ? 'enabled' : 'disabled'}
                </Badge>
                {c.has_credentials && <Badge>credentials</Badge>}
              </div>
            </div>
            {canWrite && (
              <div className="mt-4 flex flex-wrap gap-2">
                <Button size="sm" variant="outline" onClick={() => openEdit(c)}>
                  Edit
                </Button>
                <Button size="sm" variant="ghost" onClick={() => void onToggleEnabled(c)}>
                  {c.enabled ? 'Disable' : 'Enable'}
                </Button>
                <Button
                  size="sm"
                  variant="danger"
                  disabled={deletingId === c.id}
                  onClick={() => void onDelete(c)}
                >
                  {deletingId === c.id ? 'Deleting…' : 'Delete'}
                </Button>
              </div>
            )}
          </Card>
        ))}
      </div>
    </div>
  )
}
