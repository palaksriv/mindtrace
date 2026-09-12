import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../services/api'
import type { HealthResponse } from '../types/api'

export function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<HealthResponse>('/health')
      .then(({ data }) => setHealth(data))
      .catch(() => setError('The API is unavailable. Start the backend and try again.'))
  }, [])

  return (
    <section className="max-w-3xl space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">
          Multimodal student counselling
        </p>

        <h1 className="mt-2 text-4xl font-bold tracking-tight">
          MindTrace
        </h1>

        <p className="mt-4 text-lg leading-8 text-slate-600">
          A privacy-conscious platform that combines psychometric assessment
          with observable behavioural telemetry to support student counselling.
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="font-semibold">System status</h2>

        {health && (
          <p className="mt-2 text-emerald-700">
            Connected: {health.service} is {health.status}.
          </p>
        )}

        {error && (
          <p className="mt-2 text-rose-700">
            {error}
          </p>
        )}

        {!health && !error && (
          <p className="mt-2 text-slate-500">
            Checking API status…
          </p>
        )}
      </div>

      <div className="flex flex-wrap gap-3">
        <Link
          className="rounded-md bg-indigo-700 px-4 py-2 font-semibold text-white"
          to="/login/student"
        >
          Student login
        </Link>

        <Link
          className="rounded-md border border-indigo-700 px-4 py-2 font-semibold text-indigo-700"
          to="/login/counsellor"
        >
          Counsellor login
        </Link>
      </div>
    </section>
  )
}