import { useState } from 'react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Async, Card, ErrorBox, Note, PageHeader, Stat, Table, useApi } from '../components/ui.jsx'
import { HBar } from '../components/charts.jsx'
import { api } from '../api.js'

const COLORS = { CONDITION: 'bg-red-100 text-red-800', SYMPTOM: 'bg-amber-100 text-amber-800', MEDICATION: 'bg-blue-100 text-blue-800', PROCEDURE: 'bg-purple-100 text-purple-800', MEASUREMENT: 'bg-teal-100 text-teal-800' }
const DEMO = 'The patient has a history of diabetes and hypertension, takes metformin and aspirin, and presented with chest pain and fever. An MRI and biopsy were ordered. Blood pressure was elevated.'

function Highlight({ text, ents }) {
  const parts = []; let pos = 0
  ;[...ents].sort((a, b) => a.start - b.start).forEach((e, i) => {
    if (e.start < pos) return
    parts.push(text.slice(pos, e.start))
    parts.push(<mark key={i} className={`rounded px-1 ${COLORS[e.type] || 'bg-slate-200'}`} title={e.type}>{text.slice(e.start, e.end)}<sup className="ml-0.5 text-[9px]">{e.type}</sup></mark>)
    pos = e.end
  })
  parts.push(text.slice(pos)); return <p className="leading-8 text-sm">{parts}</p>
}

export default function Entities() {
  const [text, setText] = useState(DEMO)
  const [res, setRes] = useState(null)
  const [err, setErr] = useState(null)
  const [n, setN] = useState(100)
  const sum = useApi(() => api.entitySummary(n), [n])
  const go = async () => { setErr(null); if (!text.trim()) return setErr(new Error('Enter some text.')); try { setRes({ ...(await api.entities(text)), text }) } catch (e) { setErr(e) } }
  return (
    <>
      <PageHeader title="Medical Entity Extraction" subtitle="spaCy EntityRuler with a case-insensitive medical dictionary (conditions, symptoms, medications, procedures, measurements). Dictionary-based, so it only finds terms in the lexicon." />
      <div className="space-y-6">
        <Card title="Extract from text">
          <textarea className="input h-28" value={text} onChange={(e) => setText(e.target.value)} aria-label="Text" />
          <button className="btn mt-3" onClick={go}>Extract entities</button>
          {err && <div className="mt-3"><ErrorBox error={err} /></div>}
          {res && <div className="mt-4 space-y-2"><Highlight text={res.text} ents={res.entities} /><p className="text-xs text-slate-500">{res.entities.length} entities · pipeline: {res.model}</p></div>}
        </Card>
        <Card title="Dataset summary" action={<label className="flex items-center gap-2 text-sm">Notes <select className="input !w-24" value={n} onChange={(e) => setN(+e.target.value)}>{[50, 100, 250, 500].map((v) => <option key={v}>{v}</option>)}</select></label>}>
          <Async state={sum} label="Processing notes with spaCy…">{(d) => (<div className="space-y-4">
            {d.model.startsWith('blank') && <Note tone="warn">The spaCy model <code>en_core_web_sm</code> is not installed, so a blank pipeline + dictionary ruler was used. Run <code>python -m spacy download en_core_web_sm</code>.</Note>}
            <div className="grid grid-cols-3 gap-4"><Stat label="Notes processed" value={d.notes_processed} /><Stat label="Total mentions" value={d.total_mentions} /><Stat label="Notes with ≥1 entity" value={d.notes_with_entities ?? 0} /></div>
            <div className="grid gap-6 xl:grid-cols-2">
              <div><p className="mb-1 text-sm font-medium">Most frequent entities</p><HBar data={d.top_entities.slice(0, 15).map((e) => ({ ...e, label: `${e.entity} (${e.type.toLowerCase()})` }))} x="frequency" y="label" labelWidth={170} /></div>
              <div><p className="mb-1 text-sm font-medium">Mentions by type</p>
                <ResponsiveContainer width="100%" height={260}><BarChart data={d.by_type}><CartesianGrid stroke="#e2e8f0" vertical={false} /><XAxis dataKey="type" tick={{ fontSize: 11 }} /><YAxis tick={{ fontSize: 11 }} /><Tooltip /><Bar dataKey="mentions" fill="#0f766e" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div></div>
            <Table rows={d.top_entities} columns={[{ key: 'entity', label: 'Entity' }, { key: 'type', label: 'Type' }, { key: 'frequency', label: 'Frequency', right: true }]} /></div>)}</Async>
        </Card>
      </div>
    </>
  )
}
