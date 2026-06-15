import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export default function ForecastChart({ values = [] }) {
  const data = values.map((value, idx) => ({ name: `T+${idx + 1}`, value: Number(value) }))
  const numericValues = data.map((item) => item.value)
  const minValue = Math.min(...numericValues)
  const maxValue = Math.max(...numericValues)
  const isFlat = Number.isFinite(minValue) && Number.isFinite(maxValue) && Math.abs(maxValue - minValue) < 0.0001
  const padding = isFlat ? Math.max(1, minValue * 0.02) : Math.max(1, (maxValue - minValue) * 0.2)
  const domainMin = Number.isFinite(minValue) ? minValue - padding : 'auto'
  const domainMax = Number.isFinite(maxValue) ? maxValue + padding : 'auto'

  return (
    <div className="h-[22rem] w-full">
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="forecastFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.6} />
              <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.05} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
          <XAxis dataKey="name" tick={{ fill: '#9CA3AF', fontSize: 12 }} />
          <YAxis tick={{ fill: '#9CA3AF', fontSize: 12 }} domain={[domainMin, domainMax]} tickFormatter={(value) => `$${Number(value).toFixed(2)}`} />
          <Tooltip
            contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.15)' }}
            formatter={(value) => [`$${Number(value).toFixed(2)}`, 'Forecast']}
          />
          <Area type="monotone" dataKey="value" stroke="#22d3ee" fill="url(#forecastFill)" strokeWidth={2.5} isAnimationActive animationDuration={700} animationEasing="ease-out" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
