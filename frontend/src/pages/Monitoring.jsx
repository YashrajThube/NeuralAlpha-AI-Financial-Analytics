import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import Loader from '../components/ui/Loader'
import { useMonitoring } from '../hooks/useMonitoring'
import { formatNumber } from '../lib/utils'

export default function Monitoring() {
  const { data, loading, error, refresh } = useMonitoring(30000)

  const chartData = [
    { name: 'Predictions', value: Number(data?.total_predictions_24h || 0) },
    { name: 'Confidence', value: Number((data?.avg_confidence_24h || 0) * 100) },
    { name: 'P95(ms)', value: Number(data?.p95_latency_ms || 0) },
  ]

  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <p className="text-xs uppercase tracking-wide text-gray-400">Avg Latency</p>
          <p className="mt-2 text-3xl font-semibold text-gray-100">{formatNumber(data?.p95_latency_ms)}ms</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wide text-gray-400">Predictions (24h)</p>
          <p className="mt-2 text-3xl font-semibold text-gray-100">{formatNumber(data?.total_predictions_24h, 0)}</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wide text-gray-400">Error Rate</p>
          <p className="mt-2 text-3xl font-semibold text-gray-100">{formatNumber((data?.error_rate_24h || 0) * 100)}%</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wide text-gray-400">Avg Confidence</p>
          <p className="mt-2 text-3xl font-semibold text-gray-100">{formatNumber((data?.avg_confidence_24h || 0) * 100)}%</p>
        </Card>
      </div>

      <Card>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-100">System Metrics</h2>
          <Button variant="outline" onClick={() => refresh()}>
            Refresh
          </Button>
        </div>
        {loading ? (
          <Loader label="Refreshing metrics" />
        ) : data ? (
          <div className="h-80 w-full">
            <ResponsiveContainer>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
                <XAxis dataKey="name" tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                <YAxis tick={{ fill: '#9CA3AF', fontSize: 12 }} />
                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.15)' }} />
                <Bar dataKey="value" fill="#22d3ee" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <EmptyState
            title="No monitoring data yet"
            description="System metrics will appear here once the backend emits live inference activity."
            actionLabel="Refresh"
            onAction={() => refresh()}
          />
        )}
        {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
      </Card>
    </div>
  )
}
