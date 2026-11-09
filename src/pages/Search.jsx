import { useState } from 'react'
import { Async, Card, ErrorBox, Note, PageHeader, Spinner, useApi } from '../components/ui.jsx'
import { HBar } from '../components/charts.jsx'
import { api } from '../api.js'

export default function Search() {
  const [q, setQ] = useState('')
  const [spec, setSpec] = useState('')
  const [res, setRes] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const [term, setTerm] = useState('')
  const [ctx, setCtx] = useState(null)
  const [cerr, setCerr] = useState(null)
  const terms = useApi(api.terms)
  const specs = useApi(api.specialties)

  const run = async (e) => {
    e.preventDefault(); setErr(null)
    if (!q.trim()) return setErr(new Error('Enter a search query.'))
    setBusy(true)
    try { setRes(await api.search(q, 10, spec)) } catch (x) { setErr(x) } finally { setBusy(false) }
  }
  const runCtx = async (e) => {
    e.preventDefault(); setCerr(null)
    if (term.trim().length < 2) return setCerr(new Error('Enter at least 2 characters.'))
    try { setCtx(await api.context(term)) } catch (x) { setCerr(x) }
  }
  return (
    <>
      <PageHeader title="Clinical Text Search" subtitle="TF-IDF cosine-similarity retrieval over unique notes, plus term-in-context lookup (notebook T9, T10, T12)." />
      <div className="space-y-6">
        <Card title="Search reports">
          <form onSubmit={run} className="flex flex-wrap gap-2">
            <input className="input flex-1 min-w-[14rem]" placeholder="e.g. knee replacement, chest pain, diabetic foot ulcer" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Query" />
            <select className="input !w-56" value={spec} onChange={(e) => setSpec(e.target.value)} aria-label="Filter by specialty">
              <option value="">All specialties</option>{specs.data?.specialties.map((s) => <option key={s}>{s}</option>)}</select>
            <button className="btn" disabled={busy}>{busy ? 'Searching…' : 'Search'}</button></form>
          {err && <div className="mt-3"><ErrorBox error={err} /></div>}
          {res && <div className="mt-4 space-y-3">
            {res.note && <Note>{res.note}</Note>}
            {!res.results.length && !res.note && <p className="text-sm text-slate-500">No matching reports.</p>}
            {res.results.map((r, i) => (
              <article key={i} className="rounded-lg border border-slate-200 p-3">
                <div className="flex flex-wrap items-center gap-2 text-xs"><span className="rounded bg-brand-50 px-2 py-0.5 font-medium text-brand-700">{(r.similarity * 100).toFixed(1)}% match</span>
                  <span className="font-medium text-slate-800">{r.sample_name || r.specialty}</span>
                  {r.all_specialties.map((s) => <span key={s} className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-600">{s}</span>)}</div>
                <p className="mt-2 text-sm text-slate-700">{r.snippet}…</p></article>))}</div>}
        </Card>
        <div className="grid gap-6 xl:grid-cols-2">
          <Card title="Top-ranked terms (mean TF-IDF)"><Async state={terms}>{(d) => <HBar data={d.terms} x="mean_tfidf" y="term" labelWidth={120} />}</Async></Card>
          <Card title="Investigate a term in context">
            <form onSubmit={runCtx} className="flex gap-2"><input className="input" placeholder="e.g. discharge, cold, depression" value={term} onChange={(e) => setTerm(e.target.value)} aria-label="Term" /><button className="btn">Find</button></form>
            {cerr && <div className="mt-3"><ErrorBox error={cerr} /></div>}
            {ctx && <div className="mt-3 space-y-2"><p className="text-sm text-slate-600"><b>{ctx.total_notes}</b> notes contain “{ctx.term}”. Most in: {ctx.by_specialty.map((s) => `${s.specialty} (${s.notes})`).join(', ') || '—'}</p>
              <div className="max-h-80 space-y-2 overflow-auto">{ctx.contexts.map((c, i) => <p key={i} className="rounded border border-slate-200 p-2 text-xs"><span className="mb-1 block font-semibold text-slate-500">{c.specialty}</span>…{c.before}<mark className="bg-yellow-200">{c.match}</mark>{c.after}…</p>)}</div></div>}
          </Card>
        </div>
      </div>
    </>
  )
}
