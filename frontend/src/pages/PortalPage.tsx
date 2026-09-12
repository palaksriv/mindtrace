import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api, authHeaders } from '../services/api'
import type { UserRole } from '../types/auth'

export function PortalPage() {
  const { role = 'student' } =
    useParams<{ role: UserRole }>()

  const selectedRole: UserRole =
    role === 'counsellor'
      ? 'counsellor'
      : 'student'

  const [message, setMessage] = useState(
    'Confirming your access...',
  )

  useEffect(() => {
    const token = localStorage.getItem(
      'mindtrace_access_token',
    )

    api
      .get<{ message: string }>(
        `/portal/${selectedRole}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      )
      .then(({ data }) => setMessage(data.message))
      .catch(() =>
        setMessage(
          'Your session is unavailable or this account cannot access this portal.',
        ),
      )
  }, [selectedRole])

  return (
    <section className="mx-auto max-w-3xl space-y-6">
      <Link
        className="text-sm text-indigo-700 underline"
        to="/"
      >
        ← Home
      </Link>
      <div>
        <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">
          MindTrace
        </p>

        <h1 className="mt-2 text-3xl font-bold">
          {selectedRole === 'student'
            ? 'Student Portal'
            : 'Counsellor Portal'}
        </h1>

        <p className="mt-2 text-slate-600">
          {selectedRole === 'student'
            ? 'Complete your psychometric assessments and review your results.'
            : 'Review student assessment results and behavioural analytics.'}
        </p>
      </div>

      <p className="rounded-xl border border-slate-200 bg-white p-5 text-slate-700">
        {message}
      </p>

      <div className="flex flex-wrap items-center gap-4">
        {selectedRole === 'student' && (
          <Link
            className="rounded-md bg-indigo-700 px-4 py-2 font-semibold text-white"
            to="/assessments"
          >
            View assessments
          </Link>
        )}

        {selectedRole === 'counsellor' && (
          <Link
            className="rounded-md bg-indigo-700 px-4 py-2 font-semibold text-white"
            to="/counsellor"
          >
            Open counsellor dashboard
          </Link>
        )}

        <Link
          className="rounded-md border border-slate-300 px-4 py-2 font-semibold text-slate-700"
          to="/"
        >
          Return home
        </Link>
      </div>
    </section>
  )
}