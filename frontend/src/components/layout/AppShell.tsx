import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '@/lib/auth'
import { Button, cn } from '@/components/ui/Button'

const nav = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/investigations', label: 'Investigations' },
  { to: '/chat', label: 'AI Chat' },
  { to: '/connectors', label: 'Connectors' },
  { to: '/approvals', label: 'Approvals' },
  { to: '/reports', label: 'Reports' },
]

export function AppShell() {
  const { user, logout } = useAuth()

  return (
    <div className="flex h-full min-h-0">
      <aside className="flex w-56 shrink-0 flex-col border-r border-slate-700/70 bg-slate-950/80">
        <div className="border-b border-slate-700/70 px-4 py-4">
          <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-cyan-400/90">
            AISOC
          </div>
          <div className="mt-0.5 text-sm font-semibold text-slate-100">Security Ops</div>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 p-2">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                cn(
                  'rounded-md px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-800/80 hover:text-white',
                  isActive && 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/20',
                  !isActive && 'border border-transparent',
                )
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-700/70 p-3">
          <div className="truncate text-xs text-slate-400">{user?.email ?? '—'}</div>
          <div className="mt-0.5 text-[10px] uppercase tracking-wide text-slate-500">
            {(user?.roles ?? []).join(', ') || 'analyst'}
          </div>
          <Button variant="ghost" size="sm" className="mt-2 w-full justify-start" onClick={logout}>
            Sign out
          </Button>
        </div>
      </aside>
      <main className="min-w-0 flex-1 overflow-auto">
        <div className="mx-auto max-w-[1400px] p-5">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
