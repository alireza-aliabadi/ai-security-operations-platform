import { useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ApiError } from '@/lib/api'
import { useAuth } from '@/lib/auth'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'

export function LoginPage() {
  const { login, isAuthenticated, loading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/'

  const [email, setEmail] = useState('analyst@aisoc.local')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)

  if (isAuthenticated) return <Navigate to={from} replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError('Login failed — check API and credentials')
    }
  }

  return (
    <div className="flex min-h-full items-center justify-center p-6">
      <div className="liquid-glass w-full max-w-md rounded-2xl p-8">
        <div className="mb-6">
          <div className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-400">
            AISOC
          </div>
          <h1 className="mt-2 text-2xl font-semibold text-slate-50">Sign in</h1>
          <p className="mt-1 text-sm text-slate-400">
            Password auth for local SOC console. OIDC optional via mock issuer.
          </p>
        </div>
        <form className="flex flex-col gap-4" onSubmit={onSubmit}>
          <Input
            label="Email"
            name="email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <Input
            label="Password"
            name="password"
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && (
            <div className="rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300">
              {error}
            </div>
          )}
          <Button type="submit" disabled={loading} className="mt-2 w-full">
            {loading ? 'Signing in…' : 'Sign in'}
          </Button>
        </form>
      </div>
    </div>
  )
}
