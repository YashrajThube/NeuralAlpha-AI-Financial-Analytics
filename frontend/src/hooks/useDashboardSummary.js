import { useCallback, useEffect, useRef, useState } from 'react'

import { financeApi, normalizeError } from '../services/api'

export function useDashboardSummary(defaultSymbol = 'AAPL', defaultHorizonDays = 7) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const controllerRef = useRef(null)

  const refresh = useCallback(async (symbol = defaultSymbol, horizonDays = defaultHorizonDays) => {
    if (controllerRef.current) {
      controllerRef.current.abort()
    }

    controllerRef.current = new AbortController()
    setLoading(true)
    setError('')

    try {
      const [prediction, forecast] = await Promise.all([
        financeApi.predict(
          {
            symbol: String(symbol).toUpperCase(),
            model_type: 'ml',
          },
          { signal: controllerRef.current.signal }
        ),
        financeApi.forecast(
          {
            symbol: String(symbol).toUpperCase(),
            horizon_days: Number(horizonDays),
          },
          { signal: controllerRef.current.signal }
        ),
      ])

      const next = {
        symbol: String(symbol).toUpperCase(),
        prediction,
        forecast,
      }
      setData(next)
      return next
    } catch (err) {
      if (controllerRef.current?.signal?.aborted) {
        return null
      }
      const normalized = normalizeError(err)
      setError(normalized.message)
      throw normalized
    } finally {
      setLoading(false)
    }
  }, [defaultHorizonDays, defaultSymbol])

  useEffect(() => {
    refresh().catch(() => {})
    return () => {
      if (controllerRef.current) {
        controllerRef.current.abort()
      }
    }
  }, [refresh])

  return {
    data,
    loading,
    error,
    refresh,
  }
}

export default useDashboardSummary
