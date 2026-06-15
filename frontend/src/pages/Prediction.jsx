import { useMemo, useState } from 'react'

import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import Input from '../components/ui/Input'
import Loader from '../components/ui/Loader'
import { usePrediction } from '../hooks/usePrediction'
import { useTickers } from '../hooks/useTickers'
import { formatCurrency, formatNumber } from '../lib/utils'

export default function Prediction() {
  const [ticker, setTicker] = useState('AAPL')
  const [modelType, setModelType] = useState('ml')
  const { result, loading, error, predict } = usePrediction()
  const { tickers } = useTickers()

  const confidenceWidth = useMemo(() => `${Math.min(100, Math.max(0, Number(result?.confidence_score || 0) * 100))}%`, [result])

  const normalizedTicker = ticker.replace(/[^A-Z]/g, '').slice(0, 10)

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">Prediction</h2>
        <p className="text-sm text-gray-400">Run ML inference with a selected ticker and model type.</p>
      </div>

      <div className="grid gap-6 xl:grid-cols-12">
      <Card className="xl:col-span-4">
        <h2 className="text-lg font-semibold text-gray-100">Inference Input</h2>
        <div className="mt-4 space-y-4">
          <label className="block">
            <span className="mb-2 block text-sm text-gray-400">Ticker</span>
            <Input
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 10))}
              placeholder="AAPL"
              maxLength={10}
              list="ticker-options-prediction"
            />
            <datalist id="ticker-options-prediction">
              {tickers.map((item) => (
                <option key={item} value={item} />
              ))}
            </datalist>
            <span className="mt-1 block text-xs text-gray-500">Use stock symbols like AAPL, TSLA, MSFT.</span>
          </label>
          <label className="block">
            <span className="mb-2 block text-sm text-gray-400">Model Type</span>
            <select
              value={modelType}
              disabled={loading}
              onChange={(e) => setModelType(e.target.value)}
              className="w-full rounded-xl border border-white/20 bg-white/10 px-3 py-2 text-sm text-gray-100 transition-all duration-300 focus:border-cyan-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/60"
              aria-label="Select model type"
            >
              <option className="bg-slate-900" value="ml">ML</option>
              <option className="bg-slate-900" value="dl">DL</option>
              <option className="bg-slate-900" value="ensemble">Ensemble</option>
            </select>
          </label>
          <Button
            onClick={() => predict({ symbol: normalizedTicker, model_type: modelType })}
            className="w-full"
            disabled={loading || !normalizedTicker}
          >
            {loading ? 'Running...' : 'Run Prediction'}
          </Button>
          {loading && <Loader label="Computing prediction" />}
          {error && <p className="text-sm text-rose-300">{error}</p>}
        </div>
      </Card>

      <Card className="xl:col-span-8">
        <h2 className="text-lg font-semibold text-gray-100">Prediction Output</h2>
        {result ? (
          <div className="mt-5 space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-400">Ticker</p>
                <p className="mt-1 text-2xl font-semibold text-gray-100">{result.symbol}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs uppercase tracking-wide text-gray-400">Predicted Value</p>
                <p className="mt-1 text-2xl font-semibold text-gray-100">{formatCurrency(result.predicted_value)}</p>
              </div>
            </div>

            <div>
              <div className="mb-2 flex justify-between text-sm text-gray-300">
                <span>Confidence</span>
                <span>{formatNumber((result.confidence_score || 0) * 100)}%</span>
              </div>
              <div className="h-3 w-full overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-blue-400 transition-all duration-500"
                  style={{ width: confidenceWidth }}
                />
              </div>
            </div>

            <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-gray-300">
              Model type: <span className="font-semibold text-gray-100">{result.model_type}</span>
            </div>
          </div>
        ) : (
          <div className="mt-5">
            <EmptyState
              title="No prediction yet"
              description="Run inference to view predicted value, confidence, and model metadata."
            />
          </div>
        )}
      </Card>
      </div>
    </div>
  )
}
