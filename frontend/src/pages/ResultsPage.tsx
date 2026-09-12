import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, authHeaders } from '../services/api'
import type { Results } from '../types/assessment'

type BehavioralAnalytics = {
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
    per_question: {
      question_id: number
      latency_ms: number
    }[]
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
    center_both_percent: number
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


function formatMilliseconds(value: number) {
  return `${(value / 1000).toFixed(2)} s`
}

export function ResultsPage() {
  const { sessionId } = useParams()

  const [results, setResults] =
    useState<Results | null>(null)

  const [analytics, setAnalytics] =
    useState<BehavioralAnalytics | null>(null)

  const [error, setError] =
    useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return

    async function loadResults() {
      try {
        const resultsResponse =
          await api.get<Results>(
            `/sessions/${sessionId}/results`,
            {
              headers: authHeaders(),
            },
          )

        setResults(resultsResponse.data)

        const analyticsResponse =
          await api.get<BehavioralAnalytics>(
            `/cv/analytics/${sessionId}`,
            {
              headers: authHeaders(),
            },
          )

        setAnalytics(analyticsResponse.data)
      } catch {
        setError(
          'Unable to load assessment results.',
        )
      }
    }

    loadResults()
  }, [sessionId])

  if (error) {
    return (
      <p className="text-rose-700">
        {error}
      </p>
    )
  }

  if (!results || !analytics) {
    return <p>Loading results...</p>
  }

  return (
    <section className="mx-auto max-w-4xl space-y-6">
      <Link className="text-sm text-indigo-700 underline" to="/">← Home</Link>
      <div>
        <h1 className="text-3xl font-bold">
          Assessment complete
        </h1>

        <p className="mt-2 text-slate-600">
          These scores summarize your self-reported
          answers; they are not clinical or diagnostic
          findings.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {Object.entries(
          results.trait_scores,
        ).map(([trait, score]) => (
          <div
            className="rounded-xl border bg-white p-4"
            key={trait}
          >
            <p className="capitalize font-semibold">
              {trait}
            </p>

            <p className="text-2xl text-indigo-700">
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
          These are observable signals collected during
          the assessment. They are not diagnoses or
          measurements of psychological state.
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
              {analytics.response_latency.response_count}
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
              {analytics.gaze_distribution.horizontal.center}%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Left
            </p>

            <p className="text-lg font-semibold">
              {analytics.gaze_distribution.horizontal.left}%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Right
            </p>

            <p className="text-lg font-semibold">
              {analytics.gaze_distribution.horizontal.right}%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Unknown
            </p>

            <p className="text-lg font-semibold">
              {analytics.gaze_distribution.horizontal.unknown}%
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
              {analytics.gaze_distribution.vertical.center}%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Up
            </p>

            <p className="text-lg font-semibold">
              {analytics.gaze_distribution.vertical.up}%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Down
            </p>

            <p className="text-lg font-semibold">
              {analytics.gaze_distribution.vertical.down}%
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Unknown
            </p>

            <p className="text-lg font-semibold">
              {analytics.gaze_distribution.vertical.unknown}%
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
              {analytics.head_movement.pitch_variation}
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Roll variation
            </p>

            <p className="text-lg font-semibold">
              {analytics.head_movement.roll_variation}
            </p>
          </div>

          <div>
            <p className="text-sm text-slate-500">
              Movement score
            </p>

            <p className="text-lg font-semibold">
              {analytics.head_movement.movement_score}
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
            {analytics.behavioral_deviation.level}
          </p>

          <p className="mt-1 text-sm text-slate-600">
            Score:{' '}
            {analytics.behavioral_deviation.score}
          </p>
        </div>

        <div className="mt-4">
          <p className="font-semibold">
            Observed signals
          </p>

          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-600">
            {analytics.behavioral_deviation.signals.map(
              (signal) => (
                <li key={signal}>
                  {signal}
                </li>
              ),
            )}
          </ul>
        </div>
      </div>

      <Link
        className="text-indigo-700 underline"
        to="/assessments"
      >
        Return to assessments
      </Link>
    </section>
  )
}