import { lazy, Suspense, useEffect, useState } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'

import Sidebar from './components/layout/Sidebar'
import GlobalLoader from './components/ui/GlobalLoader'
import Topbar from './components/layout/Topbar'
import PageSkeleton from './components/ui/PageSkeleton'
import RouteErrorBoundary from './components/ui/RouteErrorBoundary'
import { toTitle } from './lib/utils'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Prediction = lazy(() => import('./pages/Prediction'))
const Forecast = lazy(() => import('./pages/Forecast'))
const Chat = lazy(() => import('./pages/Chat'))
const Portfolio = lazy(() => import('./pages/Portfolio'))
const Sentiment = lazy(() => import('./pages/Sentiment'))
const Monitoring = lazy(() => import('./pages/Monitoring'))

function RouteElement({ element }) {
  return (
    <RouteErrorBoundary>
      <Suspense fallback={<><PageSkeleton /><GlobalLoader label="Loading page..." /></>}>
        {element}
      </Suspense>
    </RouteErrorBoundary>
  )
}

function AppShell() {
  const location = useLocation()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setSidebarOpen(false)
      }
    }

    if (sidebarOpen) {
      document.body.style.overflow = 'hidden'
      window.addEventListener('keydown', handleKeyDown)
    }

    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [sidebarOpen])

  return (
    <div className="min-h-screen bg-app-gradient text-primary-text">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[110] focus:rounded-xl focus:bg-slate-950 focus:px-4 focus:py-2 focus:text-sm focus:text-white"
      >
        Skip to content
      </a>
      <div className="pointer-events-none fixed inset-0 opacity-30 animate-fade-soft">
        <div className="absolute inset-0 bg-gradient-to-br from-transparent via-cyan-500/20 to-transparent" />
        <div aria-hidden="true" className="absolute -left-16 top-20 h-72 w-72 rounded-full bg-cyan-400/25 blur-3xl animate-float-gentle" />
        <div aria-hidden="true" className="absolute right-10 top-40 h-80 w-80 rounded-full bg-emerald-400/20 blur-3xl animate-float-gentle" />
        <div aria-hidden="true" className="absolute bottom-12 left-1/2 h-64 w-64 -translate-x-1/2 rounded-full bg-blue-500/20 blur-3xl animate-float-gentle" />
      </div>

      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <main id="main-content" className="relative ml-0 min-h-screen p-4 md:ml-64 md:p-6">
        <div className="mx-auto flex min-h-[calc(100vh-2rem)] w-full max-w-[1600px] flex-col">
        <Topbar
          title={toTitle(location.pathname)}
          onOpenSidebar={() => setSidebarOpen(true)}
        />
        <div key={location.pathname} className="animate-page-in flex-1 pb-4">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/login" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<RouteElement element={<Dashboard />} />} />
            <Route path="/prediction" element={<RouteElement element={<Prediction />} />} />
            <Route path="/forecast" element={<RouteElement element={<Forecast />} />} />
            <Route path="/chat" element={<RouteElement element={<Chat />} />} />
            <Route path="/portfolio" element={<RouteElement element={<Portfolio />} />} />
            <Route path="/sentiment" element={<RouteElement element={<Sentiment />} />} />
            <Route path="/monitoring" element={<RouteElement element={<Monitoring />} />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
        </div>
      </main>
    </div>
  )
}

export default function App() {
  return <AppShell />
}
