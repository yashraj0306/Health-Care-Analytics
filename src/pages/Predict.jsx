import { useState } from 'react'
import { Async, Card, ErrorBox, Note, PageHeader, Table, pct, useApi } from '../components/ui.jsx'
import { api } from '../api.js'

const SAMPLE = `PREOPERATIVE DIAGNOSIS: Right knee osteoarthritis.
PROCEDURE: Total knee arthroplasty with cemented femoral and tibial components. The patella was resurfaced and the wound closed in layers.`

export default function Predict() {
  const [text, setText] = useState(SAMPLE)
  const [res, setRes] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const hist = useApi(api.history)

  const go = async () => {
    setErr(null); setRes(null)
    if (text.trim().length < 10) return setErr(new Error('Enter at least 10 characters of clinical text.'))
    setBusy(true)
    try { setRes(await api.predict(text)); hist.reload() } catch (e) { setErr(e) } finally { setBusy(false) }
  }
  const retrain = async () => { setBusy(true); setErr(null); try { await api.train(); setRes(null) } catch (e) { setErr(e) } finally { setBusy(false) } }
  return (
    <>
      <PageHeader title="Medical Specialty Prediction" subtitle="TF-IDF (1–2-grams) + LinearSVC trained on de-duplicated MTSamples notes. The first request trains and saves the model (≈10 s).">
        <button className="btn-ghost" disabled={busy} onClick={retrain}>Retrain model</button>
      </PageHeader>
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Clinical text">
          <textarea className="input h-56 font-mono text-xs" value={text} onChange={(e) => setText(e.target.value)} maxLength={50000} aria-label="Clinical text" />
          <div className="mt-3 flex items-center gap-3"><button className="btn" disabled={busy} onClick={go}>{busy ? 'Working…' : 'Predict specialty'}</button>
            <span className="text-xs text-slate-500">{text.length.toLocaleString()} / 50,000 chars</span></div>
          {err && <div className="mt-3"><ErrorBox error={err} /></div>}
        </Card>
        <Card title="Prediction">
          {!res ? <p className="text-sm text-slate-500">Results appear here.</p> : <div className="space-y-3">
            {res.predictions.map((p, i) => (
              <div key={p.specialty} className={`rounded-lg border p-3 ${i === 0 ? 'border-brand-600 bg-brand-50' : 'border-slate-200'}`}>
                <div className="flex justify-between text-sm"><span className="font-medium">{i + 1}. {p.specialty}</span><span className="tabular-nums text-slate-600">margin {p.score}</span></div>
                <div className="mt-2 h-1.5 rounded bg-slate-200"><div className="h-1.5 rounded bg-brand-600" style={{ width: pct(p.relative_confidence, 0) }} /></div>
                <div className="mt-1 text-xs text-slate-500">relative confidence {pct(p.relative_confidence)}</div></div>))}
            {res.low_confidence && <Note tone="warn">All SVM margins are negative: no specialty claims this text strongly. Short, symptom-only text often looks like a consult/ER note — try a longer transcription.</Note>}
            <Note>{res.note} MTSamples notes are often cross-listed under several specialties, so treat the top 3 as candidates.</Note></div>}
        </Card>
        <Card title="Recent predictions" className="lg:col-span-2">
          <Async state={hist}>{(h) => <Table rows={h.history} empty="No predictions yet." columns={[
            { key: 'created_at', label: 'Time' }, { key: 'top_label', label: 'Top specialty' }, { key: 'top_score', label: 'Margin', right: true }, { key: 'preview', label: 'Text' }]} />}</Async>
        </Card>
      </div>
    </>
  )
}
