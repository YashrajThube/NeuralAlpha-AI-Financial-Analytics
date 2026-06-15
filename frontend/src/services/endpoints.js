export const API_ENDPOINTS = {
  auth: {
    login: '/auth/login',
    register: '/auth/register',
  },
  prediction: {
    run: '/predict',
    history: '/predict/history',
  },
  forecast: {
    run: '/forecast',
  },
  sentiment: {
    bySymbol: (symbol) => `/sentiment/${encodeURIComponent(symbol)}`,
  },
  chat: {
    send: '/chat',
  },
  monitoring: {
    metrics: '/monitoring',
  },
  market: {
    tickers: '/tickers',
  },
  portfolio: {
    overview: '/portfolio',
  },
}

export default API_ENDPOINTS
