import { useCallback, useEffect, useRef, useState } from 'react'

import { financeApi, normalizeError } from '../services/api'

export function usePortfolio() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const controllerRef = useRef(null)

  const refresh = useCallback(async () => {
    if (controllerRef.current) {
      controllerRef.current.abort()
    }

    const controller = new AbortController()
    controllerRef.current = controller
    setLoading(true)
    setError('')

    try {
      const response = await financeApi.getPortfolio({ signal: controller.signal })
      setData(response)
      return response
    } catch (err) {
      const isCanceled =
        controller.signal.aborted ||
        err?.code === 'ERR_CANCELED' ||
        String(err?.message || '').toLowerCase() === 'canceled'

      if (isCanceled) {
        return null
      }
      const normalized = normalizeError(err)
      setError(normalized.message)
      throw normalized
    } finally {
      setLoading(false)
    }
  }, [])

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

export default usePortfolio
