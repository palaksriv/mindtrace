import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, authHeaders } from '../services/api'

type StudentSummary = {
  id: number
  name: string
  email: string
  created_at: string
  assessment_count: number
  completed_assessment_count: number
  last_assessment_at: string | null
}

function formatDate(value: string | null) {
  if (!value) {
    return 'No assessments yet'
  }

  return new Date(value).toLocaleString()
}

export function CounsellorDashboardPage() {
  const [students, setStudents] = useState<StudentSummary[]>([])

  const [loading, setLoading] = useState(true)

  const [error, setError] = useState<string | null>(null)

  const [isWiping, setIsWiping] = useState(false)

  const [wipeMessage, setWipeMessage] = useState<string | null>(
    null,
  )

  async function clearTestData() {
    const confirmed = window.confirm(
      'This will permanently delete all assessment sessions, responses, and behavioural telemetry. Users, assessments, and questions will be kept. Continue?',
    )

    if (!confirmed) {
      return
    }

    setIsWiping(true)
    setWipeMessage(null)

    try {
      const response = await api.post<{
        message: string
        sessions_deleted: number
        responses_deleted: number
        telemetry_deleted: number
      }>(
        '/admin/wipe',
        {},
        {
          headers: authHeaders(),
        },
      )

      setStudents([])

      setWipeMessage(
        `${response.data.message} Sessions: ${response.data.sessions_deleted}, responses: ${response.data.responses_deleted}, telemetry: ${response.data.telemetry_deleted}.`,
      )
    } catch {
      setWipeMessage(
        'Unable to clear test data. Please make sure you are signed in as a counsellor.',
      )
    } finally {
      setIsWiping(false)
    }
  }

  useEffect(() => {
    async function loadStudents() {
      try {
        const response = await api.get<StudentSummary[]>(
          '/counsellor/students',
          {
            headers: authHeaders(),
          },
        )

        /*
         * Only students who have actually started at least
         * one assessment session belong on the counsellor
         * assessment dashboard.
         *
         * Registered accounts with zero assessments must
         * not be counted or displayed.
         */
        const assessedStudents = response.data.filter(
          (student) => student.assessment_count > 0,
        )

        setStudents(assessedStudents)
      } catch {
        setError(
          'Unable to load students. Please make sure you are signed in as a counsellor.',
        )
      } finally {
        setLoading(false)
      }
    }

    void loadStudents()
  }, [])

  if (loading) {
    return <p>Loading counsellor dashboard...</p>
  }

  if (error) {
    return (
      <section className="space-y-4">
        <h1 className="text-3xl font-bold">
          Counsellor Dashboard
        </h1>

        <p className="rounded-xl border border-rose-200 bg-rose-50 p-5 text-rose-700">
          {error}
        </p>
      </section>
    )
  }

  const totalStudents = students.length

  const completedAssessments = students.reduce(
    (total, student) =>
      total + student.completed_assessment_count,
    0,
  )

  const studentsAssessed = students.length

  return (
    <section className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wider text-indigo-600">
          MindTrace
        </p>

        <h1 className="mt-2 text-3xl font-bold">
          Counsellor Dashboard
        </h1>

        <p className="mt-2 text-slate-600">
          Review student assessment history,
          psychometric scores, and observable
          behavioral analytics.
        </p>
      </div>

      <div className="flex flex-wrap gap-3">
        <Link
          className="rounded-md border border-slate-300 px-4 py-2 font-semibold text-slate-700"
          to="/"
        >
          Home
        </Link>

        <button
          type="button"
          onClick={() => void clearTestData()}
          disabled={isWiping}
          className="rounded-md border border-rose-300 bg-rose-50 px-4 py-2 font-semibold text-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isWiping
            ? 'Clearing test data…'
            : 'Clear Test Data'}
        </button>
      </div>

      {wipeMessage && (
        <p className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-700">
          {wipeMessage}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border bg-white p-5">
          <p className="text-sm text-slate-500">
            Total students
          </p>

          <p className="mt-1 text-3xl font-bold text-indigo-700">
            {totalStudents}
          </p>
        </div>

        <div className="rounded-xl border bg-white p-5">
          <p className="text-sm text-slate-500">
            Completed assessments
          </p>

          <p className="mt-1 text-3xl font-bold text-indigo-700">
            {completedAssessments}
          </p>
        </div>

        <div className="rounded-xl border bg-white p-5">
          <p className="text-sm text-slate-500">
            Students assessed
          </p>

          <p className="mt-1 text-3xl font-bold text-indigo-700">
            {studentsAssessed}
          </p>
        </div>
      </div>

      <div>
        <div className="mb-4">
          <h2 className="text-2xl font-bold">
            Students
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Select a student to view their complete
            assessment history.
          </p>
        </div>

        {students.length === 0 ? (
          <div className="rounded-xl border bg-white p-8 text-center">
            <p className="font-semibold">
              No assessment history found.
            </p>

            <p className="mt-1 text-sm text-slate-500">
              Students will appear here after they start
              an assessment.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {students.map((student) => (
              <article
                key={student.id}
                className="rounded-xl border bg-white p-5 shadow-sm"
              >
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">
                      {student.name}
                    </h3>

                    <p className="text-sm text-slate-500">
                      {student.email}
                    </p>

                    <p className="mt-2 text-sm text-slate-600">
                      Assessments:{' '}
                      <span className="font-semibold">
                        {student.assessment_count}
                      </span>{' '}
                      · Completed:{' '}
                      <span className="font-semibold">
                        {
                          student.completed_assessment_count
                        }
                      </span>
                    </p>

                    <p className="mt-1 text-xs text-slate-400">
                      Last assessment:{' '}
                      {formatDate(
                        student.last_assessment_at,
                      )}
                    </p>
                  </div>

                  <Link
                    className="rounded-md bg-indigo-700 px-4 py-2 text-center font-semibold text-white"
                    to={`/counsellor/students/${student.id}`}
                  >
                    View history
                  </Link>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  )
}