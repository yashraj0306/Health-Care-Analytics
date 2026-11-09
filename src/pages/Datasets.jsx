import { useRef, useState } from 'react'
import { CheckCircle2, Trash2, Upload } from 'lucide-react'
import { Async, Card, ErrorBox, Note, PageHeader, Table, useApi } from '../components/ui.jsx'
import { api } from '../api.js'

export default function Datasets() {
  const list = useApi(api.datasets)
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState(null)
  const [msg, setMsg] = useState('')
  const fileRef = useRef()

  const act = async (fn, ok) => { setBusy(true); setErr(null); setMsg(''); try { await fn(); setMsg(ok); await list.reload() } catch (e) { setErr(e) } finally { setBusy(false) } }
  const onUpload = (e) => {
    const f = e.target.files[0]; e.target.value = ''
    if (!f) return
    if (!f.name.toLowerCase().endsWith('.csv')) return setErr(new Error('Please choose a .csv file.'))
    if (f.size > 50 * 1024 * 1024) return setErr(new Error('File is larger than the 50 MB limit.'))
    act(() => api.upload(f), `Uploaded “${f.name}” and set it active.`)
  }
  return (
    <>
      <PageHeader title="Datasets" subtitle="MTSamples is the primary dataset. Upload another CSV with a 'transcription' column (and optionally 'medical_specialty') to run the same analyses on it." />
      <div className="space-y-6">
        <Card title="Upload a CSV" action={<button className="btn" disabled={busy} onClick={() => fileRef.current.click()}><Upload className="h-4 w-4" />{busy ? 'Working…' : 'Choose file'}</button>}>
          <input ref={fileRef} type="file" accept=".csv" hidden onChange={onUpload} />
          <p className="text-sm text-slate-600">Required column: <code>transcription</code>. Optional: <code>medical_specialty</code>, <code>sample_name</code>, <code>description</code>. Max 50 MB. Without a specialty column, classification, evaluation and planning-by-specialty are disabled; search, clustering, entities, PCA/SVD and lifestyle still work.</p>
          {err && <div className="mt-3"><ErrorBox error={err} /></div>}
          {msg && <p className="mt-3 flex items-center gap-2 text-sm text-emerald-700"><CheckCircle2 className="h-4 w-4" />{msg}</p>}
        </Card>
        <Card title="Registered datasets">
          <Async state={list}>{(d) => <Table rows={d.datasets} empty="No datasets yet — upload a CSV or put mtsamples.csv in backend/data/." columns={[
            { key: 'name', label: 'Name', render: (r) => <span className="font-medium">{r.name}{r.builtin && <span className="ml-2 rounded bg-brand-50 px-1.5 py-0.5 text-xs text-brand-700">primary</span>}</span> },
            { key: 'rows', label: 'Rows', right: true }, { key: 'unique_notes', label: 'Unique notes', right: true },
            { key: 'has_labels', label: 'Labels', render: (r) => (r.has_labels ? 'yes' : 'no') },
            { key: 'model_trained', label: 'Model', render: (r) => (r.model_trained ? 'trained' : '—') },
            { key: 'is_active', label: 'Status', render: (r) => (r.is_active ? <span className="font-medium text-emerald-700">active</span> : <button className="btn-ghost" disabled={busy} onClick={() => act(() => api.activate(r.id), 'Dataset activated.')}>Activate</button>) },
            { key: 'x', label: '', render: (r) => !r.builtin && <button aria-label="Delete dataset" className="text-slate-400 hover:text-red-600" disabled={busy} onClick={() => window.confirm(`Delete “${r.name}”?`) && act(() => api.remove(r.id), 'Dataset deleted.')}><Trash2 className="h-4 w-4" /></button> },
          ]} />}</Async>
        </Card>
        <Note>Uploaded datasets are stored locally in <code>backend/uploads/</code>; models for each dataset are saved under <code>backend/models/&lt;id&gt;/</code>.</Note>
      </div>
    </>
  )
}
