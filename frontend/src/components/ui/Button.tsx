import { clsx, type ClassValue } from 'clsx'
import type { ButtonHTMLAttributes, ReactNode } from 'react'

export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs)
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'ghost' | 'danger' | 'outline'
  size?: 'sm' | 'md'
  children: ReactNode
}

const variants: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary:
    'bg-cyan-500/90 text-slate-950 hover:bg-cyan-400 border border-cyan-400/40 font-semibold',
  ghost: 'bg-transparent text-slate-200 hover:bg-slate-800/80 border border-transparent',
  danger: 'bg-red-500/20 text-red-300 hover:bg-red-500/30 border border-red-500/40',
  outline: 'bg-transparent text-slate-200 hover:bg-slate-800/60 border border-slate-600',
}

export function Button({
  variant = 'primary',
  size = 'md',
  className,
  children,
  type = 'button',
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-md transition-colors disabled:opacity-50 disabled:pointer-events-none',
        size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3.5 py-2 text-sm',
        variants[variant],
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}
