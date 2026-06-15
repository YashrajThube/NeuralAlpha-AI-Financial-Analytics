import { createContext, createElement, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { financeApi, normalizeError } from '../services/api'

const TOKEN_KEY = 'na_access_token'
const EMAIL_KEY = 'na_user_email'
const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => window.localStorage.getItem(TOKEN_KEY) || '')
  const [email, setEmail] = useState(() => window.localStorage.getItem(EMAIL_KEY) || '')

  useEffect(() => {
    if (token) {
      window.localStorage.setItem(TOKEN_KEY, token)
    } else {
      window.localStorage.removeItem(TOKEN_KEY)
    }
  }, [token])

  useEffect(() => {
    if (email) {
      window.localStorage.setItem(EMAIL_KEY, email)
    } else {
      window.localStorage.removeItem(EMAIL_KEY)
    }
  }, [email])

  useEffect(() => {
    const handleUnauthorized = () => {
      setToken('')
      setEmail('')
      window.localStorage.removeItem(TOKEN_KEY)
      window.localStorage.removeItem(EMAIL_KEY)
    }

    window.addEventListener('na:unauthorized', handleUnauthorized)
    return () => {
      window.removeEventListener('na:unauthorized', handleUnauthorized)
    }
  }, [])

  const login = useCallback(async (payload) => {
    try {
      const response = await financeApi.login(payload)
      const accessToken = response?.access_token || ''
      setToken(accessToken)
      setEmail(payload.email)
      return response
    } catch (err) {
      throw normalizeError(err)
    }
  }, [])

  const register = useCallback(async (payload) => {
    try {
      await financeApi.register(payload)
      return login(payload)
    } catch (err) {
      throw normalizeError(err)
    }
  }, [login])

  const logout = useCallback(() => {
    setToken('')
    setEmail('')
    window.localStorage.removeItem(TOKEN_KEY)
    window.localStorage.removeItem(EMAIL_KEY)
  }, [])

  const value = useMemo(
    () => ({
      token,
      email,
      isAuthenticated: Boolean(token),
      login,
      register,
      logout,
    }),
    [email, login, logout, token, register]
  )

  return createElement(AuthContext.Provider, { value }, children)
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
