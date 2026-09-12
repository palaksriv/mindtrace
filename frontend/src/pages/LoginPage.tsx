import { FormEvent, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { ACCESS_TOKEN_KEY, api } from '../services/api'
import type { TokenResponse, UserRole } from '../types/auth'

const labels: Record<UserRole, string> = {
  student: 'Student',
  counsellor: 'Counsellor',
}

function EyeIcon({ visible }: { visible: boolean }) {
  if (visible) {
    return (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="h-5 w-5"
        aria-hidden="true"
      >
        <path d="M3 3l18 18" />
        <path d="M10.58 10.58a2 2 0 0 0 2.83 2.83" />
        <path d="M9.88 4.24A9.77 9.77 0 0 1 12 4c5 0 8.5 4 10 8a17.34 17.34 0 0 1-4.05 5.94" />
        <path d="M6.61 6.61C4.62 7.88 3.3 9.8 2 12c1.5 4 5 8 10 8a9.73 9.73 0 0 0 3.16-.52" />
      </svg>
    )
  }

  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}

export function LoginPage() {
  const navigate = useNavigate()
  const { role = 'student' } = useParams<{ role: UserRole }>()
  const selectedRole: UserRole =
    role === 'counsellor' ? 'counsellor' : 'student'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      const { data } = await api.post<TokenResponse>(
        '/auth/login',
        { email, password },
      )

      localStorage.setItem(
        ACCESS_TOKEN_KEY,
        data.access_token,
      )

      const meResponse = await api.get<{
        role: UserRole
      }>('/auth/me', {
        headers: {
          Authorization: `Bearer ${data.access_token}`,
        },
      })

      navigate(`/portal/${meResponse.data.role}`)
    } catch {
      setError('Incorrect email or password. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="mx-auto max-w-md rounded-xl border border-slate-200 bg-white p-7 shadow-sm">
      <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">
        MindTrace access
      </p>

      <h1 className="mt-2 text-3xl font-bold">
        {labels[selectedRole]} login
      </h1>

      <p className="mt-2 text-slate-600">
        Use your secure account credentials to continue.
      </p>

      <form className="mt-6 space-y-4" onSubmit={submit}>
        <label className="block text-sm font-medium">
          Email

          <input
            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>

        <label className="block text-sm font-medium">
          Password

          <div className="relative mt-1">
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 pr-12"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />

            <button
              type="button"
              className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 transition-colors hover:text-slate-700"
              onClick={() => setShowPassword((current) => !current)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              title={showPassword ? 'Hide password' : 'Show password'}
            >
              <EyeIcon visible={showPassword} />
            </button>
          </div>
        </label>

        {error && (
          <p className="text-sm text-rose-700" role="alert">
            {error}
          </p>
        )}

        <button
          className="w-full rounded-md bg-indigo-700 px-4 py-2 font-semibold text-white disabled:opacity-60"
          disabled={isSubmitting}
          type="submit"
        >
          {isSubmitting ? 'Signing in…' : 'Sign in'}
        </button>
      </form>

      <p className="mt-5 text-sm text-slate-600">
        Need the other portal?{' '}
        <Link
          className="text-indigo-700 underline"
          to={
            selectedRole === 'student'
              ? '/login/counsellor'
              : '/login/student'
          }
        >
          Sign in as a{' '}
          {selectedRole === 'student' ? 'counsellor' : 'student'}.
        </Link>
      </p>
    </section>
  )
}