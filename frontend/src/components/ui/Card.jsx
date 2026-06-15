import { cn } from '../../lib/utils'

export default function Card({ className = '', children }) {
  return (
    <section
      className={cn(
        'surface-glass animate-card-in rounded-2xl p-6 shadow-xl transition-all duration-300 hover:surface-glass-strong hover:shadow-2xl hover:-translate-y-0.5',
        className
      )}
    >
      {children}
    </section>
  )
}
