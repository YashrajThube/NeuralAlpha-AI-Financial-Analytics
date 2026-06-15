import { Menu, Search, UserCircle2 } from 'lucide-react'

import Input from '../ui/Input'

export default function Topbar({ title, onOpenSidebar = () => {} }) {
  return (
    <header className="sticky top-0 z-30 mb-6 rounded-2xl border border-white/10 bg-white/10 px-5 py-4 shadow-xl backdrop-blur-xl md:px-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            aria-label="Open sidebar"
            onClick={onOpenSidebar}
            className="rounded-lg border border-white/20 bg-white/10 p-2 text-gray-100 transition-all duration-300 hover:-translate-y-0.5 hover:bg-white/15 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/60 md:hidden"
          >
            <Menu size={18} />
          </button>
          <div>
            <h1 className="text-2xl font-semibold text-gray-100">{title}</h1>
            <p className="text-sm text-gray-400">AI-powered financial command center</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative hidden md:block">
            <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <label htmlFor="global-search" className="sr-only">
              Search ticker, metric, or report
            </label>
            <Input id="global-search" className="w-72 pl-9" placeholder="Search ticker, metric, report..." aria-label="Search ticker, metric, or report" />
          </div>
          <div className="hidden items-center gap-3 rounded-full border border-white/10 bg-white/10 px-3 py-2 text-sm text-gray-200 md:flex">
            <UserCircle2 size={18} />
            <span className="max-w-48 truncate">Public mode live</span>
          </div>
          <div className="rounded-full border border-white/20 bg-white/10 p-2 text-gray-200">
            <UserCircle2 size={24} />
          </div>
        </div>
      </div>
    </header>
  )
}
