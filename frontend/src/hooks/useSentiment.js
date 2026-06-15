import { useCallback, useEffect, useRef, useState } from 'react'

import { financeApi, normalizeError } from '../services/api'

export function useSentiment(initialTicker = 'AAPL') {
  const [ticker, setTicker] = useState(initialTicker)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const latestRequestRef = useRef(0)
  const controllerRef = useRef(null)
  const timerRef = useRef(null)

  const fetchSentiment = useCallback(async (nextTicker = ticker) => {
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
          const next = nextTicker.toUpperCase()
          const response = await financeApi.getSentiment(next, { signal: controllerRef.current.signal })
          if (latestRequestRef.current === requestId) {
            setData(response)
            setTicker(next)
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
  }, [ticker])

  const refresh = fetchSentiment

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

  return { result: data, ticker, setTicker, data, loading, error, fetchSentiment, refresh }
}
