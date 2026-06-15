import { cn } from '../../lib/utils'

export default function Input({ className = '', ...props }) {
  return (
    <input
      autoCapitalize="off"
      autoCorrect="off"
      spellCheck={false}
      className={cn(
        'w-full rounded-xl border border-white/20 bg-white/10 px-3 py-2 text-sm text-primary-text placeholder:text-gray-400 transition-all duration-300 focus:border-cyan-300 focus:outline-none focus:ring-2 focus:ring-cyan-300/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/60',
        className
      )}
      {...props}
    />
  )
}
