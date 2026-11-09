import { useRef, useState } from 'react'
import { CheckCircle2, CircleSlash, FileWarning } from 'lucide-react'
import { Async, Card, ErrorBox, Note, PageHeader, Table, pct, useApi } from '../components/ui.jsx'
import { HBar } from '../components/charts.jsx'
import { api } from '../api.js'

export default function Requirements() {
  const s = useApi(api.requirements)
  const [target, setTarget] = useState('')
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const ref = useRef()
  const upload = async (e) => {
    const f = e.target.files[0]; e.target.value = ''
    if (!f) return
    if (!target.trim()) return setErr(new Error('Enter the target column name first (e.g. NObeyesdad).'))
    setBusy(true); setErr(null)
    try { await api.structuredTrain(f, target.trim()); await s.reload() } catch (x) { setErr(x) } finally { setBusy(false) }
  }
  return (
    <>
      <PageHeader title="Data Requirements" subtitle="What MTSamples can and cannot support. Nothing below is simulated — features that need other data stay empty until you supply it." />
      <Async state={s}>{(d) => (
        <div className="space-y-6">
          <Card title="Supported by MTSamples (free-text transcriptions)"><ul className="grid gap-1 text-sm sm:grid-cols-2">{d.supported_with_mtsamples.map((f) => <li key={f} className="flex items-center gap-2"><CheckCircle2 className="h-4 w-4 text-emerald-600" />{f}</li>)}</ul></Card>
          {d.requires_separate_data.map((r, idx) => (
            <Card key={r.feature} title={r.feature}>
              <div className="mb-2 flex items-center gap-2 text-sm font-medium">{r.status.state === 'trained' ? <><CheckCircle2 className="h-4 w-4 text-emerald-600" />Model trained on your upload</> : r.status.state === 'requires_dataset' ? <><FileWarning className="h-4 w-4 text-amber-600" />Requires a separate dataset — not provided</> : <><CircleSlash className="h-4 w-4 text-slate-500" />Not implemented — requires data you must supply</>}</div>
              <p className="text-sm"><b>Why:</b> {r.why}</p><p className="mt-1 text-sm"><b>Needed:</b> {r.needed}</p>
              {idx === 0 && <div className="mt-4 space-y-3 border-t border-slate-100 pt-4">
                <p className="text-sm text-slate-600">Upload a structured CSV and name its target column. A RandomForest with a real <code>ColumnTransformer</code> is trained, and feature importances are read from it (the corrected T15).</p>
                <div className="flex flex-wrap gap-2"><input className="input !w-64" placeholder="Target column, e.g. NObeyesdad" value={target} onChange={(e) => setTarget(e.target.value)} aria-label="Target column" />
                  <button className="btn" disabled={busy} onClick={() => ref.current.click()}>{busy ? 'Training…' : 'Upload CSV & train'}</button><input ref={ref} type="file" accept=".csv" hidden onChange={upload} /></div>
                {err && <ErrorBox error={err} />}
                {r.status.state === 'trained' && <div className="space-y-3"><p className="text-sm">Target <code>{r.status.target}</code> · {r.status.n_rows} rows · accuracy <b>{pct(r.status.accuracy)}</b> · weighted F1 <b>{r.status.weighted_f1}</b></p>
                  <HBar data={r.status.feature_importance} x="importance" y="feature" labelWidth={180} /></div>}</div>}
            </Card>))}
          <Note tone="warn">Genomic features are deliberately left unimplemented: there is no honest way to derive them from MTSamples text, and none are fabricated.</Note>
        </div>)}</Async>
    </>
  )
}
