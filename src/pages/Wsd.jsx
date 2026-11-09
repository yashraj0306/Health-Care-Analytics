import { useState } from 'react'
import { Card, ErrorBox, Note, PageHeader, useApi } from '../components/ui.jsx'
import { api } from '../api.js'

const EX = { discharge: ['The patient was discharged home in stable condition.', 'The patient reports vaginal discharge.', 'The wound has pus and wound drainage.'],
  cold: ['She has a runny nose, cough and cold symptoms.', 'The foot was cold to touch with no pulse.'], positive: ['Urine culture was positive for E. coli.', 'He had a positive response to therapy.'], depression: ['History of major depression on an antidepressant.', 'There is a depression of the skull with a depressed fracture.'] }

export default function Wsd() {
  const senses = useApi(api.wsdSenses)
  const [term, setTerm] = useState('discharge')
  const [sentence, setSentence] = useState(EX.discharge[0])
  const [res, setRes] = useState(null)
  const [err, setErr] = useState(null)
  const go = async (s = sentence) => { setErr(null); if (!s.trim()) return setErr(new Error('Enter a sentence.')); try { setRes(await api.wsd(s, term)) } catch (e) { setErr(e) } }
  return (
    <>
      <PageHeader title="Word-Sense Disambiguation" subtitle="Context-cue matching that picks the intended meaning of ambiguous clinical words (notebook T12). Rule-based demonstration — not a trained or clinically validated model." />
      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Try a sentence">
          <label className="mb-1 block text-xs text-slate-500">Ambiguous term</label>
          <select className="input mb-3" value={term} onChange={(e) => { setTerm(e.target.value); setSentence(EX[e.target.value][0]); setRes(null) }}>{(senses.data?.terms || [{ term: 'discharge' }]).map((t) => <option key={t.term}>{t.term}</option>)}</select>
          <textarea className="input h-24" value={sentence} onChange={(e) => setSentence(e.target.value)} aria-label="Sentence" />
          <div className="mt-3 flex flex-wrap gap-2"><button className="btn" onClick={() => go()}>Disambiguate</button>
            {(EX[term] || []).map((s, i) => <button key={i} className="btn-ghost" onClick={() => { setSentence(s); go(s) }}>Example {i + 1}</button>)}</div>
          {err && <div className="mt-3"><ErrorBox error={err} /></div>}
        </Card>
        <Card title="Interpretation">
          {!res ? <p className="text-sm text-slate-500">Result appears here.</p> : <div className="space-y-3">
            <div className={`rounded-lg p-4 text-lg font-semibold ${res.interpretation.startsWith('Ambiguous') ? 'bg-amber-50 text-amber-900' : 'bg-brand-50 text-brand-900'}`}>{res.interpretation}</div>
            <p className="text-sm text-slate-600">{res.reason}</p>
            {!res.term_in_sentence && <Note tone="warn">The sentence doesn't contain “{res.term}” itself; cues were matched anyway.</Note>}
            <ul className="space-y-1 text-sm">{Object.entries(res.scores).map(([s, v]) => <li key={s} className="flex justify-between border-b border-slate-100 py-1"><span>{s}</span><span className="tabular-nums">{v} cue{v === 1 ? '' : 's'}{res.evidence[s].length ? ` — “${res.evidence[s].join('”, “')}”` : ''}</span></li>)}</ul>
            <Note>{res.disclaimer}</Note></div>}
        </Card>
      </div>
    </>
  )
}
