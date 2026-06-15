export default function PageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-10 w-64 animate-pulse rounded-xl bg-white/10" />
      <div className="grid gap-6 md:grid-cols-3">
        <div className="h-32 animate-pulse rounded-2xl bg-white/10" />
        <div className="h-32 animate-pulse rounded-2xl bg-white/10" />
        <div className="h-32 animate-pulse rounded-2xl bg-white/10" />
      </div>
      <div className="h-80 animate-pulse rounded-2xl bg-white/10" />
    </div>
  )
}
