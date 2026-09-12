import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, authHeaders } from '../services/api'

type Analytics = {
  sample_count: number
  face_presence_percent: number
  blink_rate: number
  average_ear: number
  response_latency: {
    response_count: number
    average_latency_ms: number
    minimum_latency_ms: number
    maximum_latency_ms: number
    latency_variation_ms: number
  }
  gaze_distribution: {
    horizontal: {
      center: number
      left: number
      right: number
      unknown: number
    }
    vertical: {
      center: number
      up: number
      down: number
      unknown: number
    }
  }
  head_movement: {
    yaw_variation: number
    pitch_variation: number
    roll_variation: number
    movement_score: number
  }
  behavioral_deviation: {
    score: number
    level: string
    signals: string[]
  }
}

type SessionData = {
  student: {
    id: number
    name: string
    email: string
  }
  session: {
    id: number
    assessment_id: number
    assessment_title: string
    status: string
    started_at: string
    completed_at: string
  }
  results: {
    session_id: number
    trait_scores: Record<string, number>
  }
  analytics: Analytics
}


function formatMilliseconds(value: number) {
  return `${(value / 1000).toFixed(2)} s`
}

function formatDate(value: string) {
  return new Date(value).toLocaleString()
}

export function CounsellorSessionPage() {
  const { sessionId } = useParams()

  const [data, setData] =
    useState<SessionData | null>(null)

  const [error, setError] =
    useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) {
      return
    }

    async function loadSession() {
      try {
        const response =
          await api.get<SessionData>(
            `/counsellor/sessions/${sessionId}`,
            {
              headers: authHeaders(),
            },
          )

        setData(response.data)
      } catch {
        setError(
          'Unable to load assessment results.',
        )
      }
    }

    loadSession()
  }, [sessionId])

  if (error) {
    return (
      <section className="space-y-4">
        <h1 className="text-3xl font-bold">
          Assessment Results
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
    return <p>Loading assessment results...</p>
  }

  const analytics = data.analytics

  return (
    <section className="mx-auto max-w-5xl space-y-6">
      <Link className="text-sm text-indigo-700 underline" to="/">← Home</Link>
      <div>
        <Link
          className="text-sm text-indigo-700 underline"
          to={`/counsellor/students/${data.student.id}`}
        >
          ← Back to student history
        </Link>

        <p className="mt-5 text-sm font-semibold uppercase tracking-wider text-indigo-600">
          Counsellor View
        </p>

        <h1 className="mt-2 text-3xl font-bold">
          {data.student.name}
        </h1>

        <p className="mt-1 text-slate-500">
          {data.student.email}
        </p>

        <div className="mt-4 rounded-xl border bg-white p-5">
          <h2 className="text-xl font-bold">
            {data.session.assessment_title}
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Started:{' '}
            {formatDate(data.session.started_at)}
          </p>

          <p className="text-sm text-slate-500">
            Completed:{' '}
            {formatDate(data.session.completed_at)}
          </p>
        </div>
      </div>

      <div className="rounded-xl border bg-white p-5">
        <h2 className="text-xl font-bold">
          Psychometric results
        </h2>

        <p className="mt-1 text-sm text-slate-600">
          These scores summarize the student's
          self-reported answers. They are not clinical
          or diagnostic findings.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {Object.entries(
          data.results.trait_scores,
        ).map(([trait, score]) => (
          <div
            key={trait}
            className="rounded-xl border bg-white p-4"
          >
            <p className="capitalize font-semibold">
              {trait}
            </p>

            <p className="mt-1 text-2xl font-bold text-indigo-700">
              {score}%
            </p>
          </div>
        ))}
      </div>

      <div className="rounded-xl border bg-white p-5">
        <h2 className="text-xl font-bold">
          Behavioral telemetry
        </h2>

        <p className="mt-1 text-sm text-slate-600">
          These are observable signals collected
          during the assessment. They are not
          diagnoses or measurements of psychological
          state.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border bg-white p-4">
          <p className="text-sm text-slate-500">
            Face presence
          </p>

          <p className="mt-1 text-2xl font-bold text-indigo-700">
            {analytics.face_presence_percent}%
          </p>
        </div>

        <div className="rounded-xl border bg-white p-4">
          <p className="text-sm text-slate-500">
            Blink rate
          </p>

          <p className="mt-1 text-2xl font-bold text-indigo-700">
            {analytics.blink_rate}
          </p>
        </div>

        <div className="rounded-xl border bg-white p-4">
          <p className="text-sm text-slate-500">
            Average EAR
          </p>

          <p className="mt-1 text-2xl font-bold text-indigo-700">
            {analytics.average_ear}
          </p>
        </div>

        <div className="rounded-xl border bg-white p-4">
          <p className="text-sm text-slate-500">
            CV samples
          </p>

          <p className="mt-1 text-2xl font-bold text-indigo-700">
            {analytics.sample_count}
          </p>
        </div>
      </div>

      <div className="rounded-xl border bg-white p-5">
        <h2 className="text-xl font-bold">
          Response latency
        </h2>

        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-sm text-slate-500">
              Responses
            </p>

            <p className="text-lg font-semibold">
              {
                analytics.response_latency
                  .response_count
              }
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Average
            </p>

            <p className="text-lg font-semibold">
              {formatMilliseconds(
                analytics.response_latency
                  .average_latency_ms,
              )}
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Minimum
            </p>

            <p className="text-lg font-semibold">
              {formatMilliseconds(
                analytics.response_latency
                  .minimum_latency_ms,
              )}
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Maximum
            </p>

            <p className="text-lg font-semibold">
              {formatMilliseconds(
                analytics.response_latency
                  .maximum_latency_ms,
              )}
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-xl border bg-white p-5">
        <h2 className="text-xl font-bold">
          Gaze distribution
        </h2>

        <h3 className="mt-4 font-semibold">
          Horizontal
        </h3>

        <div className="mt-2 grid gap-3 sm:grid-cols-4">
          <div>
            <p className="text-sm text-slate-500">
              Center
            </p>

            <p className="text-lg font-semibold">
              {
                analytics.gaze_distribution
                  .horizontal.center
              }%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Left
            </p>

            <p className="text-lg font-semibold">
              {
                analytics.gaze_distribution
                  .horizontal.left
              }%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Right
            </p>

            <p className="text-lg font-semibold">
              {
                analytics.gaze_distribution
                  .horizontal.right
              }%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Unknown
            </p>

            <p className="text-lg font-semibold">
              {
                analytics.gaze_distribution
                  .horizontal.unknown
              }%
            </p>
          </div>
        </div>

        <h3 className="mt-5 font-semibold">
          Vertical
        </h3>

        <div className="mt-2 grid gap-3 sm:grid-cols-4">
          <div>
            <p className="text-sm text-slate-500">
              Center
            </p>

            <p className="text-lg font-semibold">
              {
                analytics.gaze_distribution
                  .vertical.center
              }%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Up
            </p>

            <p className="text-lg font-semibold">
              {
                analytics.gaze_distribution
                  .vertical.up
              }%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Down
            </p>

            <p className="text-lg font-semibold">
              {
                analytics.gaze_distribution
                  .vertical.down
              }%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Unknown
            </p>

            <p className="text-lg font-semibold">
              {
                analytics.gaze_distribution
                  .vertical.unknown
              }%
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-xl border bg-white p-5">
        <h2 className="text-xl font-bold">
          Head movement
        </h2>

        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-sm text-slate-500">
              Yaw variation
            </p>

            <p className="text-lg font-semibold">
              {analytics.head_movement.yaw_variation}
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Pitch variation
            </p>

            <p className="text-lg font-semibold">
              {
                analytics.head_movement
                  .pitch_variation
              }
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Roll variation
            </p>

            <p className="text-lg font-semibold">
              {
                analytics.head_movement
                  .roll_variation
              }
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Movement score
            </p>

            <p className="text-lg font-semibold">
              {
                analytics.head_movement
                  .movement_score
              }
            </p>
          </div>
        </div>
      </div>

      <div className="rounded-xl border bg-white p-5">
        <h2 className="text-xl font-bold">
          Behavioral deviation
        </h2>

        <div className="mt-4">
          <p className="text-sm text-slate-500">
            Observable signal level
          </p>

          <p className="mt-1 text-2xl font-bold text-indigo-700">
            {
              analytics.behavioral_deviation
                .level
            }
          </p>

          <p className="mt-1 text-sm text-slate-600">
            Score:{' '}
            {
              analytics.behavioral_deviation
                .score
            }
          </p>
        </div>

        <div className="mt-4">
          <p className="font-semibold">
            Observed signals
          </p>

          {analytics.behavioral_deviation
            .signals.length === 0 ? (
            <p className="mt-2 text-sm text-slate-500">
              No major behavioral deviations were
              observed.
            </p>
          ) : (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
              {analytics.behavioral_deviation.signals.map(
                (signal) => (
                  <li key={signal}>
                    {signal}
                  </li>
                ),
              )}
            </ul>
          )}
        </div>
      </div>
    </section>
  )
}