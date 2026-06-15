import { useCallback, useRef, useState } from 'react'

import { financeApi, normalizeError } from '../services/api'

const DEFAULT_WELCOME = {
  id: 1,
  role: 'assistant',
  text: 'Welcome to NeuralAlpha AI. Ask about market risk, trend, or prediction context.',
}

export function useChat(initialSymbol = 'AAPL') {
  const [symbol, setSymbol] = useState(initialSymbol)
  const [messages, setMessages] = useState([DEFAULT_WELCOME])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const latestRequestRef = useRef(0)
  const controllerRef = useRef(null)
  const timerRef = useRef(null)

  const sendMessage = useCallback(async (message, symbolOverride) => {
    const content = String(message || '').trim()
    if (!content) {
      return null
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

    const userMessage = { id: Date.now(), role: 'user', text: content }
    setMessages((prev) => [...prev, userMessage])
    setError('')

    return new Promise((resolve, reject) => {
      timerRef.current = setTimeout(async () => {
        setLoading(true)
        try {
          const response = await financeApi.sendChat(
            {
              message: content,
              symbol: String(symbolOverride || symbol || 'AAPL').toUpperCase(),
            },
            { signal: controllerRef.current.signal }
          )

          if (latestRequestRef.current === requestId) {
            const assistantMessage = {
              id: Date.now() + 1,
              role: 'assistant',
              text: response.reply || 'No reply generated.',
            }
            setMessages((prev) => [...prev, assistantMessage])
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
  }, [symbol])

  const resetConversation = useCallback(() => {
    if (controllerRef.current) {
      controllerRef.current.abort()
    }
    if (timerRef.current) {
      clearTimeout(timerRef.current)
    }
    setMessages([DEFAULT_WELCOME])
    setError('')
    setLoading(false)
  }, [])

  return {
    symbol,
    setSymbol,
    messages,
    loading,
    error,
    sendMessage,
    resetConversation,
  }
}

export default useChat
