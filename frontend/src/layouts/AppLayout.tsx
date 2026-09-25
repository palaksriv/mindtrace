import { Link, Outlet } from 'react-router-dom'

export function AppLayout() {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,_#e0e7ff,_transparent_32%),linear-gradient(#f8fafc,#f8fafc)] text-slate-900">
      <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur">
        <nav className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link className="flex items-center gap-2 text-xl font-bold tracking-tight text-indigo-700" to="/">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-700 text-sm text-white">M</span>MindTrace
          </Link>
          <span className="text-sm text-slate-500"></span>
        </nav>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-12">
        <Outlet />
      </main>
    </div>
  )
}
