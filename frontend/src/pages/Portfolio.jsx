import { useMemo } from 'react'

import EmptyState from '../components/ui/EmptyState'
import Card from '../components/ui/Card'
import Loader from '../components/ui/Loader'
import Table from '../components/ui/Table'
import { usePortfolio } from '../hooks/usePortfolio'
import { formatCurrency, formatNumber } from '../lib/utils'

export default function Portfolio() {
  const { data, loading, error } = usePortfolio()

  const columns = useMemo(
    () => [
      { key: 'symbol', label: 'Asset' },
      { key: 'quantity', label: 'Qty', render: (value) => formatNumber(value, 2) },
      { key: 'avg_price', label: 'Avg Price', render: (value) => formatCurrency(value) },
      { key: 'market_price', label: 'Market Price', render: (value) => formatCurrency(value) },
      { key: 'market_value', label: 'Market Value', render: (value) => formatCurrency(value) },
      { key: 'pnl', label: 'PnL', render: (value) => formatCurrency(value) },
      { key: 'weight_pct', label: 'Weight', render: (value) => `${formatNumber(value, 2)}%` },
    ],
    []
  )

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-100">Portfolio</h2>
        <p className="text-sm text-gray-400">Track holdings and allocation with live database data.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card>
          <p className="text-xs uppercase tracking-wide text-gray-400">Portfolio Value</p>
          <p className="mt-2 text-3xl font-semibold text-gray-100">{formatCurrency(data?.total_market_value)}</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wide text-gray-400">Total Positions</p>
          <p className="mt-2 text-3xl font-semibold text-gray-100">{formatNumber(data?.positions || 0, 0)}</p>
        </Card>
        <Card>
          <p className="text-xs uppercase tracking-wide text-gray-400">Largest Weight</p>
          <p className="mt-2 text-3xl font-semibold text-gray-100">
            {data?.holdings?.length ? `${formatNumber(Math.max(...data.holdings.map((x) => x.weight_pct || 0)), 1)}%` : '--'}
          </p>
        </Card>
      </div>

      <Card>
        <h2 className="mb-4 text-lg font-semibold text-gray-100">Asset Allocation</h2>
        {loading ? (
          <Loader label="Loading portfolio" />
        ) : data?.holdings?.length ? (
          <Table columns={columns} rows={data.holdings} />
        ) : (
          <EmptyState
            title="No holdings available"
            description="Add positions to your portfolio to see allocation, market value, and PnL breakdowns here."
          />
        )}
        {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}
      </Card>
    </div>
  )
}
