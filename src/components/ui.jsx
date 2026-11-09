import { useCallback, useEffect, useState } from 'react'
import { AlertTriangle, Loader2, Info } from 'lucide-react'

export const PALETTE = ['#0f766e', '#2563eb', '#d97706', '#9333ea', '#dc2626', '#0891b2', '#65a30d', '#db2777', '#64748b', '#a16207']

export function useApi(fn, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const run = useCallback(() => {
    setState((s) => ({ ...s, loading: true, error: null }))
    return fn().then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => setState({ data: null, error, loading: false }))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  useEffect(() => { run() }, [run])
  return { ...state, reload: run }
}

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
      <div><h1 className="text-2xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 max-w-3xl text-sm text-slate-600">{subtitle}</p>}</div>
      <div className="flex gap-2">{children}</div>
    </div>
  )
}

export const Card = ({ title, action, children, className = '' }) => (
  <section className={`rounded-xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}>
    {(title || action) && <div className="mb-3 flex items-center justify-between gap-2">
      <h2 className="text-sm font-semibold text-slate-700">{title}</h2>{action}</div>}
    {children}
  </section>
)

export const Stat = ({ label, value, hint }) => (
  <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
    <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
    <div className="mt-1 text-2xl font-semibold text-slate-900">{value}</div>
    {hint && <div className="mt-0.5 text-xs text-slate-500">{hint}</div>}
  </div>
)

export const Spinner = ({ label = 'Loading…' }) => (
  <div className="flex items-center gap-2 p-6 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" />{label}</div>
)

export function ErrorBox({ error, onRetry }) {
  if (!error) return null
  const noData = error.code === 'no_active_dataset'
  return (
    <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="flex-1"><div className="font-medium">{error.message}</div>
        {error.details && <pre className="mt-1 overflow-auto text-xs text-red-700">{JSON.stringify(error.details, null, 1)}</pre>}
        {noData && <a className="mt-1 inline-block underline" href="/datasets">Go to Datasets →</a>}</div>
      {onRetry && <button className="btn-ghost" onClick={onRetry}>Retry</button>}
    </div>
  )
}

export const Note = ({ children, tone = 'info' }) => (
  <div className={`flex items-start gap-2 rounded-lg p-3 text-xs ${tone === 'warn' ? 'bg-amber-50 text-amber-900' : 'bg-slate-100 text-slate-700'}`}>
    <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" /><div>{children}</div>
  </div>
)

/** Renders loading / error states, then children(data). */
export function Async({ state, children, label }) {
  if (state.loading && !state.data) return <Spinner label={label} />
  if (state.error) return <ErrorBox error={state.error} onRetry={state.reload} />
  return state.data ? children(state.data) : null
}

export function Table({ columns, rows, empty = 'No data.' }) {
  if (!rows?.length) return <p className="p-3 text-sm text-slate-500">{empty}</p>
  return (
    <div className="overflow-x-auto"><table className="min-w-full divide-y divide-slate-200">
      <thead><tr>{columns.map((c) => <th key={c.key} className={`th ${c.right ? 'text-right' : ''}`}>{c.label}</th>)}</tr></thead>
      <tbody className="divide-y divide-slate-100">{rows.map((r, i) => (
        <tr key={i} className="hover:bg-slate-50">{columns.map((c) => (
          <td key={c.key} className={`td ${c.right ? 'text-right tabular-nums' : ''}`}>{c.render ? c.render(r) : r[c.key]}</td>))}</tr>))}
      </tbody></table></div>
  )
}

export const pct = (v, d = 1) => (v == null ? '—' : `${(v * 100).toFixed(d)}%`)
export const num = (v) => (v == null ? '—' : Number(v).toLocaleString())
