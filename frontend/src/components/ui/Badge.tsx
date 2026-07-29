import type { HTMLAttributes } from 'react'
import { cn } from './Button'

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info' | 'neutral'

const severityClass: Record<Severity, string> = {
  critical: 'bg-red-500/20 text-red-300 border-red-500/40',
  high: 'bg-orange-500/20 text-orange-300 border-orange-500/40',
  medium: 'bg-amber-500/20 text-amber-200 border-amber-500/40',
  low: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40',
  info: 'bg-sky-500/20 text-sky-300 border-sky-500/40',
  neutral: 'bg-slate-700/50 text-slate-300 border-slate-600/60',
}

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  severity?: Severity
}

export function Badge({ severity = 'neutral', className, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide',
        severityClass[severity],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  )
}
