import Loader from './Loader'

export default function GlobalLoader({ label = 'Loading workspace...' }) {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/65 backdrop-blur-sm" aria-busy="true" aria-live="polite">
      <div className="rounded-2xl border border-white/15 bg-slate-900/90 px-6 py-5 shadow-2xl">
        <Loader label={label} />
      </div>
    </div>
  )
}
