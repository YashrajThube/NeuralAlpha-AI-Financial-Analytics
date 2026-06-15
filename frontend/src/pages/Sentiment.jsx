import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts'

import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import Input from '../components/ui/Input'
import Loader from '../components/ui/Loader'
import { useSentiment } from '../hooks/useSentiment'
import { useTickers } from '../hooks/useTickers'
import { formatNumber } from '../lib/utils'

export default function Sentiment() {
  const { ticker, setTicker, result, loading, error, fetchSentiment } = useSentiment('AAPL')
  const { tickers } = useTickers()
  const normalizedTicker = ticker.replace(/[^A-Z]/g, '').slice(0, 10)

  const score = Number(result?.score || 0)
  const mapped = Math.min(100, Math.max(0, (score + 1) * 50))
  const chartData = [
    { name: 'score', value: mapped },
    { name: 'rest', value: 100 - mapped },
  ]

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <Card className="lg:col-span-1">
        <h2 className="text-lg font-semibold text-gray-100">Sentiment Input</h2>
        <div className="mt-4 space-y-4">
          <Input
            value={ticker}
            disabled={loading}
            onChange={(e) => setTicker(e.target.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 10))}
            maxLength={10}
            list="ticker-options-sentiment"
          />
          <datalist id="ticker-options-sentiment">
            {tickers.map((item) => (
              <option key={item} value={item} />
            ))}
          </datalist>
          <span className="-mt-2 block text-xs text-gray-500">Enter a valid stock symbol, for example AAPL.</span>
          <Button className="w-full" disabled={loading || !normalizedTicker} onClick={() => fetchSentiment(normalizedTicker)}>
            {loading ? 'Analyzing...' : 'Analyze Sentiment'}
          </Button>
          {loading && <Loader label="Scanning sentiment" />}
          {error && <p className="text-sm text-rose-300">{error}</p>}
        </div>
      </Card>

      <Card className="lg:col-span-2">
        <h2 className="text-lg font-semibold text-gray-100">Market Sentiment Gauge</h2>
        {result ? (
          <div className="mt-4 grid items-center gap-4 md:grid-cols-2">
            <div className="h-64">
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={chartData} dataKey="value" innerRadius={65} outerRadius={95} startAngle={180} endAngle={0}>
                    <Cell fill="#22d3ee" />
                    <Cell fill="rgba(255,255,255,0.1)" />
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-3">
              <p className="text-sm text-gray-400">Ticker</p>
              <p className="text-2xl font-semibold text-gray-100">{result.symbol}</p>
              <p className="text-sm text-gray-400">Score</p>
              <p className="text-2xl font-semibold text-gray-100">{formatNumber(score, 3)}</p>
              <p className="text-sm text-gray-400">Label</p>
              <p className="inline-flex rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm text-gray-100">
                {result.label}
              </p>
            </div>
          </div>
        ) : (
          <div className="mt-4">
            <EmptyState
              title="No sentiment loaded yet"
              description="Run an analysis to render the gauge, score, and label for the selected ticker."
            />
          </div>
        )}
      </Card>
    </div>
  )
}
