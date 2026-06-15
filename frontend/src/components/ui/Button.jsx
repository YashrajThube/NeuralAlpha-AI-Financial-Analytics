import { cn } from '../../lib/utils'

const variants = {
  primary: 'bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400 text-white shadow-lg shadow-cyan-500/20 hover:brightness-110',
  ghost: 'bg-transparent text-primary-text hover:bg-white/10',
  outline: 'border border-cyan-300/25 bg-transparent text-primary-text hover:bg-cyan-300/10 hover:border-cyan-300/40',
}

export default function Button({
  className = '',
  variant = 'primary',
  type = 'button',
  disabled = false,
  children,
  ...props
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      className={cn(
        'inline-flex items-center justify-center rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-300 disabled:cursor-not-allowed disabled:opacity-60 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/60 focus-visible:ring-offset-0 active:scale-[0.98] motion-safe:hover:-translate-y-0.5',
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}
