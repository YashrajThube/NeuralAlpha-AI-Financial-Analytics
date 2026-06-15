import { useMemo, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'

import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'
import Loader from '../components/ui/Loader'
import { useAuth } from '../hooks/useAuth'

export default function Login() {
  const { isAuthenticated, login, register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from || '/dashboard'
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ email: 'admin@neuralalpha.ai', password: 'NeuralAlpha123!', role: 'user' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const title = useMemo(() => (mode === 'login' ? 'Welcome back' : 'Create your account'), [mode])

  if (isAuthenticated) {
    return <Navigate to={from} replace />
  }

  const submit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      if (mode === 'login') {
        await login({ email: form.email, password: form.password })
      } else {
        await register({ email: form.email, password: form.password, role: form.role })
      }
      navigate(from, { replace: true })
    } catch (err) {
      setError(err.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-app-gradient px-4 text-primary-text">
      <div className="absolute inset-0 bg-black/20" />
      <Card className="relative z-10 w-full max-w-md">
        <div className="mb-6">
          <p className="text-xs uppercase tracking-[0.3em] text-cyan-200">NeuralAlpha</p>
          <h1 className="mt-2 text-3xl font-semibold text-gray-100">{title}</h1>
          <p className="mt-2 text-sm text-gray-400">
            {mode === 'login'
              ? 'Authenticate to access your financial intelligence workspace.'
              : 'Create a secure account to start using the platform.'}
          </p>
        </div>

        <form className="space-y-4" onSubmit={submit}>
          <label className="block">
            <span className="mb-2 block text-sm text-gray-400">Email</span>
            <Input
              type="email"
              value={form.email}
              onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
              placeholder="you@company.com"
            />
          </label>

          <label className="block">
            <span className="mb-2 block text-sm text-gray-400">Password</span>
            <Input
              type="password"
              value={form.password}
              onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
              placeholder="••••••••"
            />
          </label>

          {mode === 'register' && (
            <label className="block">
              <span className="mb-2 block text-sm text-gray-400">Role</span>
              <select
                value={form.role}
                onChange={(e) => setForm((prev) => ({ ...prev, role: e.target.value }))}
                className="w-full rounded-xl border border-white/20 bg-white/10 px-3 py-2 text-sm text-gray-100 focus:outline-none"
              >
                <option className="bg-slate-900" value="user">User</option>
                <option className="bg-slate-900" value="admin">Admin</option>
              </select>
            </label>
          )}

          {error && <p className="text-sm text-rose-300">{error}</p>}
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? <Loader label={mode === 'login' ? 'Signing in' : 'Creating account'} /> : mode === 'login' ? 'Sign In' : 'Create Account'}
          </Button>
        </form>

        <button
          type="button"
          onClick={() => setMode((prev) => (prev === 'login' ? 'register' : 'login'))}
          className="mt-4 text-sm text-cyan-200 transition hover:text-cyan-100"
        >
          {mode === 'login' ? 'Need an account? Register' : 'Already have an account? Sign in'}
        </button>
      </Card>
    </div>
  )
}
