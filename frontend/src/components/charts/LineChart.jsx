import {
  CartesianGrid,
  Line,
  LineChart as ReLineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export default function LineChart({ data, dataKey = 'value', label = 'Value' }) {
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <ReLineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
          <XAxis dataKey="name" tick={{ fill: '#9CA3AF', fontSize: 12 }} />
          <YAxis tick={{ fill: '#9CA3AF', fontSize: 12 }} />
          <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.15)' }} />
          <Line type="monotone" dataKey={dataKey} stroke="#22d3ee" strokeWidth={2.5} dot={false} name={label} />
        </ReLineChart>
      </ResponsiveContainer>
    </div>
  )
}
