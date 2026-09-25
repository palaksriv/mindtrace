import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, authHeaders } from '../services/api'

type Student = {
  id: number
  name: string
  email: string
  created_at: string
}

type AssessmentSession = {
  id: number
  assessment_id: number
  assessment_title: string
  status: string
  started_at: string
  completed_at: string | null
  response_count: number
}

type StudentHistory = {
  student: Student
  sessions: AssessmentSession[]
}
type Trend = { session_id:number; completed_at:string; trait_scores:Record<string,number>; average_latency_ms:number; sample_count:number; face_presence_percent:number }


function formatDate(value: string | null) {
  if (!value) {
    return '—'
  }

  return new Date(value).toLocaleString()
}

export function StudentHistoryPage() {
  const { studentId } = useParams()

  const [data, setData] =
    useState<StudentHistory | null>(null)

  const [error, setError] =
    useState<string | null>(null)
  const [trends, setTrends] = useState<Trend[]>([])

  useEffect(() => {
    if (!studentId) {
      return
    }

    async function loadStudent() {
      try {
        const response =
          await api.get<StudentHistory>(
            `/counsellor/students/${studentId}`,
            {
              headers: authHeaders(),
            },
          )

        setData(response.data)
      } catch {
        setError(
          'Unable to load this student.',
        )
      }
    }

    loadStudent()
  }, [studentId])

  useEffect(() => { if (!studentId) return; api.get<Trend[]>(`/counsellor/students/${studentId}/trends`, {headers:authHeaders()}).then(r=>setTrends(r.data)).catch(()=>undefined) }, [studentId])

  if (error) {
    return (
      <section className="space-y-4">
        <h1 className="text-3xl font-bold">
          Student History
        </h1>

        <p className="text-rose-700">
          {error}
        </p>

        <Link
          className="text-indigo-700 underline"
          to="/counsellor"
        >
          Back to dashboard
        </Link>
      </section>
    )
  }

  if (!data) {
    return <p>Loading student history...</p>
  }

  return (
    <section className="space-y-8">
      <Link className="text-sm text-indigo-700 underline" to="/">← Home</Link>
      <div>
        <Link
          className="text-sm text-indigo-700 underline"
          to="/counsellor"
        >
          ← Back to dashboard
        </Link>

        <h1 className="mt-4 text-3xl font-bold">
          {data.student.name}
        </h1>

        <p className="mt-1 text-slate-500">
          {data.student.email}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border bg-white p-5">
          <p className="text-sm text-slate-500">
            Total sessions
          </p>

          <p className="mt-1 text-3xl font-bold text-indigo-700">
            {data.sessions.length}
          </p>
        </div>

        <div className="rounded-xl border bg-white p-5">
          <p className="text-sm text-slate-500">
            Completed
          </p>

          <p className="mt-1 text-3xl font-bold text-indigo-700">
            {
              data.sessions.filter(
                (session) =>
                  session.status === 'completed',
              ).length
            }
          </p>
        </div>

        <div className="rounded-xl border bg-white p-5">
          <p className="text-sm text-slate-500">
            Questions answered
          </p>

          <p className="mt-1 text-3xl font-bold text-indigo-700">
            {data.sessions.reduce(
              (total, session) =>
                total + session.response_count,
              0,
            )}
          </p>
        </div>
      </div>

      {trends.length > 0 && <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between"><div><h2 className="text-xl font-bold">Personal session trends</h2><p className="mt-1 text-sm text-slate-500">Compare this student's own sessions over time. These are descriptive summaries, not clinical trends.</p></div><span className="text-sm font-medium text-indigo-700">{trends.length} completed session{trends.length===1?'':'s'}</span></div><div className="mt-6 grid gap-5 lg:grid-cols-2"><div><h3 className="font-semibold">Response pace</h3><div className="mt-3 space-y-3">{trends.map((trend,index)=><div key={trend.session_id} className="grid grid-cols-[5rem_1fr_4rem] items-center gap-3 text-sm"><span className="text-slate-500">Session {index+1}</span><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-indigo-600" style={{width:`${Math.min(100,trend.average_latency_ms/100)}%`}}/></div><span className="text-right font-semibold">{(trend.average_latency_ms/1000).toFixed(1)}s</span></div>)}</div></div><div><h3 className="font-semibold">Data coverage</h3><div className="mt-3 space-y-3">{trends.map((trend,index)=><div key={trend.session_id} className="grid grid-cols-[5rem_1fr_4rem] items-center gap-3 text-sm"><span className="text-slate-500">Session {index+1}</span><div className="h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-emerald-500" style={{width:`${trend.face_presence_percent}%`}}/></div><span className="text-right font-semibold">{trend.sample_count?`${trend.face_presence_percent}%`:'No CV'}</span></div>)}</div></div></div></div>}

      <div>
        <h2 className="text-2xl font-bold">
          Assessment history
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Select a completed assessment to view its
          psychometric and behavioral results.
        </p>
      </div>

      {data.sessions.length === 0 ? (
        <div className="rounded-xl border bg-white p-8 text-center">
          <p className="font-semibold">
            No assessment sessions yet.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {data.sessions.map((session) => (
            <article
              key={session.id}
              className="rounded-xl border bg-white p-5 shadow-sm"
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-lg font-semibold">
                    {session.assessment_title}
                  </h3>

                  <p className="mt-1 text-sm text-slate-500">
                    Started:{' '}
                    {formatDate(
                      session.started_at,
                    )}
                  </p>

                  <p className="text-sm text-slate-500">
                    Completed:{' '}
                    {formatDate(
                      session.completed_at,
                    )}
                  </p>

                  <p className="mt-2 text-sm text-slate-600">
                    Responses:{' '}
                    <span className="font-semibold">
                      {session.response_count}
                    </span>
                  </p>
                </div>

                {session.status ===
                  'completed' && (
                  <Link
                    className="rounded-md bg-indigo-700 px-4 py-2 text-center font-semibold text-white"
                    to={`/counsellor/sessions/${session.id}`}
                  >
                    View results
                  </Link>
                )}

                {session.status !==
                  'completed' && (
                  <span className="rounded-md bg-slate-100 px-4 py-2 text-center text-sm font-semibold text-slate-600">
                    In progress
                  </span>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
