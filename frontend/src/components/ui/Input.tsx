import type { InputHTMLAttributes } from 'react'
import { cn } from './Button'

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string
  error?: string
}

export function Input({ label, error, className, id, ...props }: InputProps) {
  const inputId = id ?? props.name
  return (
    <label className="flex w-full flex-col gap-1.5 text-sm">
      {label && <span className="text-slate-400">{label}</span>}
      <input
        id={inputId}
        className={cn(
          'w-full rounded-md border border-slate-600 bg-slate-950/80 px-3 py-2 text-slate-100 outline-none',
          'placeholder:text-slate-500 focus:border-cyan-500/70 focus:ring-1 focus:ring-cyan-500/40',
          error && 'border-red-500/60',
          className,
        )}
        {...props}
      />
      {error && <span className="text-xs text-red-400">{error}</span>}
    </label>
  )
}
