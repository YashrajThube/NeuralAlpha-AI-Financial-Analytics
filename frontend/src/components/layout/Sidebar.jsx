import { Activity, Bot, CandlestickChart, Gauge, Home, PieChart, Radar, Sparkles, X } from 'lucide-react'
import { useEffect } from 'react'
import { NavLink } from 'react-router-dom'

const navItems = [
  { label: 'Dashboard', icon: Home, to: '/dashboard' },
  { label: 'Prediction', icon: Sparkles, to: '/prediction' },
  { label: 'Forecast', icon: CandlestickChart, to: '/forecast' },
  { label: 'Chat', icon: Bot, to: '/chat' },
  { label: 'Portfolio', icon: PieChart, to: '/portfolio' },
  { label: 'Sentiment', icon: Radar, to: '/sentiment' },
  { label: 'Monitoring', icon: Activity, to: '/monitoring' },
]

export default function Sidebar({ isOpen = false, onClose = () => {} }) {
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown)
    }

    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [isOpen, onClose])

  return (
    <>
      <button
        type="button"
        aria-label="Close menu"
        onClick={onClose}
        className={[
          'fixed inset-0 z-30 bg-slate-950/50 backdrop-blur-sm transition-opacity md:hidden',
          isOpen ? 'pointer-events-auto opacity-100' : 'pointer-events-none opacity-0',
        ].join(' ')}
      />
      <aside
        className={[
          'fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-white/10 bg-slate-950/80 p-4 backdrop-blur-xl transition-transform duration-300',
          isOpen ? 'translate-x-0' : '-translate-x-full',
          'md:translate-x-0',
        ].join(' ')}
      >
        <div className="mb-8 flex items-center gap-3 px-2">
          <div className="rounded-lg bg-cyan-300/20 p-2 text-cyan-200">
            <Gauge size={20} />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-gray-400">NeuralAlpha</p>
            <p className="text-lg font-semibold text-gray-100">Fintech OS</p>
          </div>
          <button
            type="button"
            aria-label="Close sidebar"
            onClick={onClose}
            className="ml-auto rounded-lg border border-white/15 bg-white/10 p-1 text-gray-200 md:hidden"
          >
            <X size={16} />
          </button>
        </div>

        <nav className="flex-1 space-y-2">
          {navItems.map(({ icon: Icon, label, to }) => (
            <NavLink
              key={label}
              to={to}
              onClick={onClose}
              aria-label={label}
              className={({ isActive }) =>
                [
                  'group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/60',
                  isActive ? 'bg-cyan-300/20 text-cyan-100' : 'text-gray-300 hover:bg-white/10 hover:text-white',
                ].join(' ')
              }
            >
              <Icon size={16} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4">
          <p className="text-xs uppercase tracking-[0.2em] text-gray-400">Access Mode</p>
          <p className="mt-1 truncate text-sm font-semibold text-gray-100">Public API Session</p>
        </div>
      </aside>
    </>
  )
}
