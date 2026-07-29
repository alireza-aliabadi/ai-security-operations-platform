import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from './Button'

export const glassCardClass = 'liquid-glass rounded-2xl'

type CardProps = HTMLAttributes<HTMLDivElement> & {
  title?: string
  action?: ReactNode
  children: ReactNode
  padded?: boolean
}

export function Card({
  title,
  action,
  children,
  className,
  padded = true,
  ...props
}: CardProps) {
  return (
    <div className={cn(glassCardClass, className)} {...props}>
      {(title || action) && (
        <div className="liquid-glass-header flex items-center justify-between gap-3 px-4 py-2.5">
          {title ? (
            <h3 className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-300/90">
              {title}
            </h3>
          ) : (
            <span />
          )}
          {action}
        </div>
      )}
      <div className={cn(padded && 'p-4', !padded && 'flex min-h-0 flex-1 flex-col')}>{children}</div>
    </div>
  )
}
