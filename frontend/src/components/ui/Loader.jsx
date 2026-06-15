export default function Loader({ label = 'Loading...' }) {
  return (
    <div className="flex items-center gap-3 text-gray-300" role="status" aria-live="polite">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-cyan-300/40 border-t-cyan-300" />
      <span className="text-sm text-gray-300">{label}</span>
    </div>
  )
}
