import { lazy, Suspense, useState } from 'react'

import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import Loader from '../components/ui/Loader'
import { useForecast } from '../hooks/useForecast'
import { useTickers } from '../hooks/useTickers'
import { formatCurrency } from '../lib/utils'

const ForecastChart = lazy(() => import('../components/charts/ForecastChart'))

export default function Forecast() {
  const [ticker, setTicker] = useState('AAPL')
  const [horizon, setHorizon] = useState(7)
  const { result, loading, error, forecast } = useForecast()
  const { tickers } = useTickers()
  const normalizedTicker = ticker.replace(/[^A-Z]/g, '').slice(0, 10)
  const normalizedHorizon = Math.min(30, Math.max(1, Number(horizon) || 7))
  const points = Array.isArray(result?.forecast) ? result.forecast : []
  const minForecast = points.length ? Math.min(...points) : null
  const maxForecast = points.length ? Math.max(...points) : null
  const lastForecast = points.length ? points[points.length - 1] : null

  return (
    <div className="space-y-6">
      <Card>
        <div className="mb-3 flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-gray-100">Forecast Setup</h2>
          <p className="text-xs text-gray-400">Choose symbol and horizon, then generate projection.</p>
        </div>

        <div className="grid gap-4 md:grid-cols-12">
          <label className="block md:col-span-4">
            <span className="mb-2 block text-sm text-gray-400">Ticker</span>
            <Input
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 10))}
              maxLength={10}
              list="ticker-options-forecast"
            />
            <datalist id="ticker-options-forecast">
              {tickers.map((item) => (
                <option key={item} value={item} />
              ))}
            </datalist>
          </label>
          <label className="block md:col-span-4">
            <span className="mb-2 block text-sm text-gray-400">Horizon (days)</span>
            <Input type="number" min={1} max={30} value={horizon} disabled={loading} onChange={(e) => setHorizon(e.target.value)} />
            <span className="mt-1 block text-xs text-gray-500">Pick between 1 and 30 days.</span>
          </label>
          <div className="flex items-end md:col-span-4">
            <Button className="w-full" disabled={loading || !normalizedTicker} onClick={() => forecast({ symbol: normalizedTicker, horizon_days: normalizedHorizon })}>
              {loading ? 'Generating...' : 'Generate Forecast'}
            </Button>
          </div>
        </div>
        {loading && <div className="mt-4"><Loader label="Generating forecast" /></div>}
        {error && <p className="mt-4 text-sm text-rose-300">{error}</p>}
      </Card>

      <Card>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-100">Multi-step Forecast</h2>
          {result?.forecast?.[0] && <p className="text-sm text-gray-300">Next value: {formatCurrency(result.forecast[0])}</p>}
        </div>

        {points.length > 0 && (
          <div className="mb-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-white/10 bg-white/5 p-3">
              <p className="text-xs uppercase tracking-wide text-gray-400">Minimum</p>
              <p className="mt-1 text-base font-semibold text-gray-100">{formatCurrency(minForecast)}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-3">
              <p className="text-xs uppercase tracking-wide text-gray-400">Maximum</p>
              <p className="mt-1 text-base font-semibold text-gray-100">{formatCurrency(maxForecast)}</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-white/5 p-3">
              <p className="text-xs uppercase tracking-wide text-gray-400">End of Horizon</p>
              <p className="mt-1 text-base font-semibold text-gray-100">{formatCurrency(lastForecast)}</p>
            </div>
          </div>
        )}

        {result?.forecast?.length ? (
          <Suspense fallback={<div className="h-[22rem] animate-pulse rounded-2xl bg-white/10" />}>
            <ForecastChart values={result.forecast} />
          </Suspense>
        ) : (
          <p className="text-sm text-gray-400">Run forecast to visualize projected trend.</p>
        )}
      </Card>
    </div>
  )
}
