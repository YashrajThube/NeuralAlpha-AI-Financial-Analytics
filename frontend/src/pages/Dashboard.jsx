import { lazy, Suspense, useEffect } from 'react'

import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Loader from '../components/ui/Loader'
import { useDashboardSummary } from '../hooks/useDashboardSummary'
import { useMonitoring } from '../hooks/useMonitoring'
import { useSentiment } from '../hooks/useSentiment'
import { formatCurrency, formatNumber } from '../lib/utils'

const LineChart = lazy(() => import('../components/charts/LineChart'))

export default function Dashboard() {
  const { data: monitoring, loading: monitoringLoading } = useMonitoring(45000)
  const { data: sentiment, fetchSentiment, loading: sentimentLoading } = useSentiment('AAPL')
  const { data: summary, loading: summaryLoading, error: summaryError, refresh: refreshSummary } = useDashboardSummary('AAPL', 7)

  useEffect(() => {
    fetchSentiment('AAPL').catch(() => {})
  }, [fetchSentiment])

  const forecastSeries = Array.isArray(summary?.forecast?.forecast) ? summary.forecast.forecast : []
  const chartData = forecastSeries.map((value, idx) => ({ name: `D${idx + 1}`, value: Number(value || 0) }))

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-gray-100">Overview</h2>
          <p className="text-sm text-gray-400">Live system summary for AAPL and platform health.</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        <Card>
          <p className="text-xs uppercase tracking-wide text-gray-400">Sentiment Score</p>
          <p className="mt-2 text-3xl font-semibold text-gray-100">{sentiment ? formatNumber(sentiment.score, 3) : '--'}</p>
          <p className="mt-1 text-sm text-gray-400">AAPL live sentiment</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wide text-gray-400">Error Rate</p>
          <p className="mt-2 text-3xl font-semibold text-gray-100">{monitoring ? `${formatNumber((monitoring.error_rate_24h || 0) * 100)}%` : '--'}</p>
          <p className="mt-1 text-sm text-gray-400">24h rolling window</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wide text-gray-400">P95 Latency</p>
          <p className="mt-2 text-3xl font-semibold text-gray-100">{monitoring ? `${formatNumber(monitoring.p95_latency_ms)}ms` : '--'}</p>
          <p className="mt-1 text-sm text-gray-400">Inference runtime</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wide text-gray-400">Predicted Value</p>
          <p className="mt-2 text-3xl font-semibold text-gray-100">
            {summary?.prediction ? formatCurrency(summary.prediction.predicted_value || 0) : '--'}
          </p>
          <p className="mt-1 text-sm text-gray-400">AAPL one-shot prediction</p>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-12">
        <Card className="xl:col-span-8">
          <div className="mb-4 flex items-center justify-between gap-4">
            <h2 className="text-lg font-semibold text-gray-100">Forecast Summary (7 days)</h2>
            <div className="flex items-center gap-3">
              {(summaryLoading || monitoringLoading || sentimentLoading) && <Loader label="Syncing live data" />}
              <Button variant="outline" onClick={() => refreshSummary('AAPL', 7)} disabled={summaryLoading}>Refresh</Button>
            </div>
          </div>
          {chartData.length > 1 ? (
            <Suspense fallback={<div className="h-72 animate-pulse rounded-2xl bg-white/10" />}>
              <LineChart data={chartData} dataKey="value" label="Predicted Price" />
            </Suspense>
          ) : (
            <p className="text-sm text-gray-400">Run summary refresh to load forecast points.</p>
          )}
          {summaryError && <p className="mt-3 text-sm text-rose-300">{summaryError}</p>}
        </Card>

        <Card className="xl:col-span-4">
          <h2 className="text-lg font-semibold text-gray-100">Quick Insights</h2>
          <div className="mt-4 space-y-3 text-sm text-gray-300">
            <p className="rounded-xl border border-white/10 bg-white/5 p-3">
              {monitoring?.avg_confidence_24h < 0.6
                ? 'Confidence drift is elevated. Validate feature quality and model freshness.'
                : 'Model confidence remains stable in the last 24h window.'}
            </p>
            <p className="rounded-xl border border-white/10 bg-white/5 p-3">
              {Number(monitoring?.p95_latency_ms || 0) > 500
                ? 'Latency is elevated. Consider scaling inference workers.'
                : 'Latency is stable with healthy p95 levels.'}
            </p>
            <p className="rounded-xl border border-white/10 bg-white/5 p-3">
              Sentiment for AAPL is currently <strong>{sentiment?.label || 'neutral'}</strong>.
            </p>
          </div>
        </Card>
      </div>
    </div>
  )
}
