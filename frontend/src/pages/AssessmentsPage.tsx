import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, authHeaders } from '../services/api'
import type { AssessmentSummary } from '../types/assessment'

export function AssessmentsPage() {
  const [items, setItems] = useState<AssessmentSummary[]>([])
  const [error, setError] = useState<string | null>(null)
  useEffect(() => { api.get<AssessmentSummary[]>('/assessments', { headers: authHeaders() }).then(({ data }) => setItems(data)).catch(() => setError('Please sign in as a student to view assessments.')) }, [])
  return <section className="space-y-6"><Link className="text-sm text-indigo-700 underline" to="/">← Home</Link><h1 className="text-3xl font-bold">Available assessments</h1>{error && <p className="text-rose-700">{error}</p>}{items.map((item) => <article className="rounded-xl border bg-white p-6 shadow-sm" key={item.id}><h2 className="text-xl font-semibold">{item.title}</h2><p className="mt-2 text-slate-600">{item.description}</p><p className="mt-3 text-sm text-slate-500">{item.question_count} questions · 1 = strongly disagree, 5 = strongly agree</p><Link className="mt-5 inline-block rounded-md bg-indigo-700 px-4 py-2 font-semibold text-white" to={`/assessments/${item.id}`}>Start assessment</Link></article>)}</section>
}