import { useCallback, useEffect, useRef, useState } from 'react'

import { financeApi, normalizeError } from '../services/api'

const FALLBACK_TICKERS = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META']

export function useTickers() {
  const [tickers, setTickers] = useState(FALLBACK_TICKERS)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const hasLoadedRef = useRef(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const payload = await financeApi.getTickers()
      const symbols = Array.isArray(payload?.symbols) ? payload.symbols : []
      const cleaned = symbols
        .map((symbol) => String(symbol || '').toUpperCase().replace(/[^A-Z]/g, '').slice(0, 10))
        .filter(Boolean)
      if (cleaned.length) {
        setTickers(cleaned)
      }
      hasLoadedRef.current = true
      return cleaned
    } catch (err) {
      const normalized = normalizeError(err)
      setError(normalized.message)
      return FALLBACK_TICKERS
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (!hasLoadedRef.current) {
      refresh().catch(() => {})
    }
  }, [refresh])

  return { tickers, loading, error, refresh }
}

export default useTickers
