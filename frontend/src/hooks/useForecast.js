import { useCallback, useEffect, useRef, useState } from 'react'

import { financeApi, normalizeError } from '../services/api'

export function useForecast() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const latestRequestRef = useRef(0)
  const controllerRef = useRef(null)
  const timerRef = useRef(null)

  const forecast = useCallback(async (payloadOrTicker, horizonDays = 7) => {
    const payload =
      typeof payloadOrTicker === 'object' && payloadOrTicker !== null
        ? {
            symbol: String(payloadOrTicker.symbol || 'AAPL').toUpperCase(),
            horizon_days: Number(payloadOrTicker.horizon_days || horizonDays),
          }
        : {
            symbol: String(payloadOrTicker || 'AAPL').toUpperCase(),
            horizon_days: Number(horizonDays),
          }

    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }

    if (controllerRef.current) {
      controllerRef.current.abort()
    }

    const requestId = latestRequestRef.current + 1
    latestRequestRef.current = requestId
    controllerRef.current = new AbortController()

    return new Promise((resolve, reject) => {
      timerRef.current = setTimeout(async () => {
        setLoading(true)
        setError('')
        try {
          const response = await financeApi.forecast(payload, { signal: controllerRef.current.signal })
          if (latestRequestRef.current === requestId) {
            setData(response)
            resolve(response)
          }
        } catch (err) {
          if (controllerRef.current?.signal?.aborted) {
            resolve(null)
            return
          }
          const normalized = normalizeError(err)
          if (latestRequestRef.current === requestId) {
            setError(normalized.message)
          }
          reject(normalized)
        } finally {
          if (latestRequestRef.current === requestId) {
            setLoading(false)
          }
        }
      }, 220)
    })
  }, [])

  const runForecast = forecast

  useEffect(
    () => () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
      }
      if (controllerRef.current) {
        controllerRef.current.abort()
      }
    },
    []
  )

  return { result: data, data, loading, error, forecast, runForecast }
}
