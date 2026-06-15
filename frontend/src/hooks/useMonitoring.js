import { useCallback, useEffect, useRef, useState } from 'react'

import { financeApi, normalizeError } from '../services/api'

export function useMonitoring(pollMs = 30000) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const latestRequestRef = useRef(0)
  const controllerRef = useRef(null)

  const refresh = useCallback(async () => {
    if (controllerRef.current) {
      controllerRef.current.abort()
    }
    const requestId = latestRequestRef.current + 1
    latestRequestRef.current = requestId
    controllerRef.current = new AbortController()

    setLoading(true)
    setError('')
    try {
      const response = await financeApi.getMonitoring({ signal: controllerRef.current.signal })
      if (latestRequestRef.current === requestId) {
        setData(response)
      }
      return response
    } catch (err) {
      if (controllerRef.current?.signal?.aborted) {
        return null
      }
      const normalized = normalizeError(err)
      if (latestRequestRef.current === requestId) {
        setError(normalized.message)
      }
      throw normalized
    } finally {
      if (latestRequestRef.current === requestId) {
        setLoading(false)
      }
    }
  }, [])

  useEffect(() => {
    refresh().catch(() => {})
    const timer = setInterval(() => {
      refresh().catch(() => {})
    }, pollMs)
    return () => {
      clearInterval(timer)
      if (controllerRef.current) {
        controllerRef.current.abort()
      }
    }
  }, [pollMs, refresh])

  return { data, loading, error, refresh }
}
