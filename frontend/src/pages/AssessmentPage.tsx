import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, authHeaders } from '../services/api'
import type {
  AssessmentDetail,
  AssessmentSession,
} from '../types/assessment'
import { WebcamCapture } from '../components/WebcamCapture'


export function AssessmentPage() {
  const { assessmentId } = useParams()
  const navigate = useNavigate()

  const [assessment, setAssessment] =
    useState<AssessmentDetail | null>(null)

  const [session, setSession] =
    useState<AssessmentSession | null>(null)

  const [index, setIndex] = useState(0)

  const [answers, setAnswers] =
    useState<Record<number, number>>({})

  const [displayedAt, setDisplayedAt] =
    useState(new Date())

  const [error, setError] =
    useState<string | null>(null)

  const [webcamConsent, setWebcamConsent] =
    useState(false)

  const [cameraActive, setCameraActive] =
    useState(false)

  useEffect(() => {
    if (!assessmentId) return

    api
      .get<AssessmentDetail>(
        `/assessments/${assessmentId}`,
        {
          headers: authHeaders(),
        },
      )
      .then(({ data }) => setAssessment(data))
      .catch(() =>
        setError('This assessment is unavailable.'),
      )
  }, [assessmentId])

  async function start() {
	
    if (
      !assessment ||
      !webcamConsent ||
      !cameraActive
    ) {
      return
    }

    try {
      const { data } =
        await api.post<AssessmentSession>(
          '/sessions',
          {
            assessment_id: assessment.id,
          },
          {
            headers: authHeaders(),
          },
        )

      // Record an auditable consent entry BEFORE any telemetry is accepted.
      await api.post(
        `/sessions/${data.id}/consent`,
        { granted: true },
        { headers: authHeaders() },
      )

      setSession(data)
      setDisplayedAt(new Date())
      setError(null)
    } catch {
      setError('Unable to start the assessment.')
    }
  }

  async function next() {
    if (!assessment || !session) return

    const question =
      assessment.questions[index]

    const value = answers[question.id]

    if (!value) {
      setError(
        'Choose a response before continuing.',
      )
      return
    }

    setError(null)

    try {
      await api.post(
        `/sessions/${session.id}/responses`,
        {
          question_id: question.id,
          response: value,
          displayed_at: displayedAt.toISOString(),
          answered_at: new Date().toISOString(),
        },
        {
          headers: authHeaders(),
        },
      )

      if (
        index ===
        assessment.questions.length - 1
      ) {
        await api.post(
          `/sessions/${session.id}/complete`,
          {},
          {
            headers: authHeaders(),
          },
        )

        navigate(`/results/${session.id}`)
      } else {
        setIndex(index + 1)
        setDisplayedAt(new Date())
      }
    } catch {
      setError(
        'Unable to save your response. Please try again.',
      )
    }
  }

  if (error && !assessment) {
    return (
      <p className="text-rose-700">
        {error}
      </p>
    )
  }

  if (!assessment) {
    return <p>Loading assessment...</p>
  }

  return (
    <section className="mx-auto max-w-3xl space-y-6">
      {!session && (
        <>
          <div>
            <h1 className="text-3xl font-bold">
              {assessment.title}
            </h1>

            <p className="mt-2 text-slate-600">
              Your answers are stored with response
              timing. This is a self-reflection tool,
              not a diagnosis.
            </p>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-5">
            <h2 className="text-lg font-semibold">
              Webcam consent
            </h2>

            <p className="mt-2 text-sm text-slate-600">
              With your permission, MindTrace will use
              your webcam during the assessment to
              collect behavioral telemetry. Raw video
              is not recorded or stored by this
              application.
            </p>

            <label className="mt-4 flex cursor-pointer items-start gap-3">
              <input
                type="checkbox"
                checked={webcamConsent}
                onChange={(event) =>
                  setWebcamConsent(
                    event.target.checked,
                  )
                }
                className="mt-1 h-4 w-4"
              />

              <span className="text-sm">
                I understand and consent to webcam use
                during this assessment.
              </span>
            </label>
          </div>
        </>
      )}

      {webcamConsent && (
        <WebcamCapture
          sessionId={session?.id}
          onStatusChange={setCameraActive}
        />
      )}

      {!session ? (
        <>
          {error && (
            <p className="text-rose-700">
              {error}
            </p>
          )}

          <button
  type="button"
  className="rounded-md bg-indigo-700 px-4 py-2 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
  disabled={!webcamConsent}
  onClick={() => {
    console.log('BEGIN BUTTON CLICKED')
    void start()
  }}
>
  Begin Assessment
</button>
        </>
      ) : (
        <>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
            Camera monitoring is active for this
            assessment.
          </div>

          <p className="text-sm font-semibold text-indigo-700">
            Question {index + 1} of{' '}
            {assessment.questions.length}
          </p>

          <div className="h-2 rounded bg-slate-200">
            <div
              className="h-2 rounded bg-indigo-700"
              style={{
                width: `${
                  ((index + 1) /
                    assessment.questions.length) *
                  100
                }%`,
              }}
            />
          </div>

          <h1 className="text-2xl font-bold">
            {
              assessment.questions[index]
                .question_text
            }
          </h1>

          <div className="grid grid-cols-5 gap-2">
            {[1, 2, 3, 4, 5].map(
              (value) => (
                <button
                  className={`rounded-md border p-3 font-semibold ${
                    answers[
                      assessment.questions[index].id
                    ] === value
                      ? 'border-indigo-700 bg-indigo-700 text-white'
                      : 'border-slate-300'
                  }`}
                  key={value}
                  onClick={() =>
                    setAnswers({
                      ...answers,
                      [assessment.questions[index].id]:
                        value,
                    })
                  }
                >
                  {value}
                </button>
              ),
            )}
          </div>

          <div className="flex justify-between text-xs text-slate-500">
            <span>
              Strongly disagree
            </span>

            <span>
              Strongly agree
            </span>
          </div>

          {error && (
            <p className="text-rose-700">
              {error}
            </p>
          )}

          <div className="flex justify-between">
            <button
              className="text-indigo-700 underline disabled:text-slate-400"
              disabled={index === 0}
              onClick={() => {
                setIndex(index - 1)
                setDisplayedAt(new Date())
              }}
            >
              Back
            </button>

            <button
              className="rounded-md bg-indigo-700 px-4 py-2 font-semibold text-white"
              onClick={next}
            >
              {index ===
              assessment.questions.length - 1
                ? 'Complete'
                : 'Next'}
            </button>
          </div>
        </>
      )}
    </section>
  )
}