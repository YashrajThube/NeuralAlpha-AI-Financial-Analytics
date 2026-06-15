import axios from 'axios'
import API_ENDPOINTS from './endpoints'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api/v1',
  timeout: 3000,
  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },
})

function shouldRetry(error) {
  const status = error?.response?.status
  const code = error?.code || ''
  const isNetworkError = !error?.response || code === 'ERR_NETWORK' || code === 'ECONNABORTED'
  const isServerError = typeof status === 'number' && status >= 500
  const isAbort = code === 'ERR_CANCELED'

  if (isAbort) {
    return false
  }

  if (typeof status === 'number' && status >= 400 && status < 500) {
    return false
  }

  return isNetworkError || isServerError
}

api.interceptors.request.use((config) => {
  const next = { ...config }
  const publicApiKey = import.meta.env.VITE_PUBLIC_API_KEY || ''
  next.headers = {
    ...next.headers,
    'X-Client': 'neuralalpha-dashboard',
    ...(publicApiKey ? { 'X-API-Key': publicApiKey } : {}),
  }
  return next
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const config = error.config || {}
    if (shouldRetry(error)) {
      return Promise.reject(normalizeError(error))
    }

    return Promise.reject(normalizeError(error))
  }
)

export function normalizeError(error) {
  if (error?.message && error?.status && error?.raw) {
    return error
  }

  const detail = error?.response?.data?.detail
  const envelopeError = error?.response?.data?.error
  const message =
    typeof envelopeError === 'string'
      ? envelopeError
      :
    typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((item) => item?.msg || String(item)).join('; ')
        : error?.message || 'Unexpected error occurred.'

  return {
    status: error?.response?.status || 500,
    message,
    raw: error,
  }
}

const unwrap = (promise) =>
  promise.then((res) => {
    if (res?.data?.success === false) {
      throw normalizeError({ response: { status: 400, data: res.data } })
    }
    if (res?.data && Object.prototype.hasOwnProperty.call(res.data, 'data')) {
      return res.data.data
    }
    return res.data
  })

export const financeApi = {
  getTickers: (options = {}) => unwrap(api.get(API_ENDPOINTS.market.tickers, options)),
  getSentiment: (symbol, options = {}) => unwrap(api.get(API_ENDPOINTS.sentiment.bySymbol(symbol), options)),
  getMonitoring: (options = {}) => unwrap(api.get(API_ENDPOINTS.monitoring.metrics, options)),
  getPortfolio: (options = {}) => unwrap(api.get(API_ENDPOINTS.portfolio.overview, options)),
  getPredictionHistory: (options = {}) => unwrap(api.get(API_ENDPOINTS.prediction.history, options)),
  predict: (payload, options = {}) => unwrap(api.post(API_ENDPOINTS.prediction.run, payload, options)),
  forecast: (payload, options = {}) => unwrap(api.post(API_ENDPOINTS.forecast.run, payload, options)),
  sendChat: (payload, options = {}) => unwrap(api.post(API_ENDPOINTS.chat.send, payload, options)),
}

export default api
