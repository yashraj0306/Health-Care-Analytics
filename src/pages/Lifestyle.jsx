import { Async, Card, Note, PageHeader, Stat, Table, pct, useApi } from '../components/ui.jsx'
import { HBar, Roc } from '../components/charts.jsx'
import { api } from '../api.js'

export default function Lifestyle() {
  const s = useApi(api.lifestyle)
  return (
    <>
      <PageHeader title="Lifestyle Analysis" subtitle="How often lifestyle topics (diet, activity, weight, smoking, sleep) are mentioned in clinical notes (notebook T14), and how well context alone predicts a weight mention." />
      <Async state={s} label="Analysing notes…">{(d) => (
        <div className="space-y-6">
          <Note tone="warn">{d.caveat}</Note>
          <div className="grid gap-6 xl:grid-cols-2">
            <Card title={`Notes mentioning each topic (of ${d.n_notes.toLocaleString()})`}><HBar data={d.counts} x="notes" y="topic" /></Card>
            <Card title="Share of notes"><Table rows={[...d.counts].reverse()} columns={[{ key: 'topic', label: 'Topic' }, { key: 'notes', label: 'Notes', right: true }, { key: 'percent', label: '% of notes', right: true }]} /></Card>
          </div>
          <Card title="Top 10 specialties by weight/obesity mentions"><div className="overflow-x-auto"><Table rows={d.by_specialty} columns={[{ key: 'specialty', label: 'Specialty' }, { key: 'total_notes', label: 'Notes', right: true }, ...d.topics.map((t) => ({ key: t, label: t, right: true }))]} /></div></Card>
          <Card title="Weight-mention text classifier (Logistic regression)">
            {!d.model.available ? <p className="text-sm text-slate-500">{d.model.reason}</p> : (<div className="space-y-4">
              <Note>The trigger words (weight, obese, BMI…) are <b>masked</b> before training — the original notebook trained on text that contained the very regex that defined the label, which is target leakage. This predicts whether a note mentions weight from its surrounding context; it is <b>not</b> an obesity predictor.</Note>
              <div className="grid grid-cols-2 gap-4 lg:grid-cols-4"><Stat label="Accuracy" value={pct(d.model.accuracy)} hint={`positive rate ${pct(d.model.positive_rate)}`} /><Stat label="ROC AUC" value={d.model.auc} /><Stat label="Mention recall" value={d.model.report.Mention['recall']} /><Stat label="Mention precision" value={d.model.report.Mention['precision']} /></div>
              <div className="grid gap-6 lg:grid-cols-2"><Roc roc={d.model.roc} auc={d.model.auc} />
                <div><p className="mb-2 text-sm font-medium">Strongest context terms</p><p className="text-sm text-slate-700">{d.model.top_context_terms.join(', ')}</p>
                  <p className="mb-1 mt-4 text-sm font-medium">Confusion matrix (rows = true)</p>
                  <table className="text-sm"><tbody>{d.model.confusion.map((r, i) => <tr key={i}><th className="pr-3 text-left font-normal text-slate-500">{i ? 'Mention' : 'No mention'}</th>{r.map((v, j) => <td key={j} className={`px-4 py-2 text-center tabular-nums ${i === j ? 'bg-brand-50 font-semibold' : 'bg-slate-50'}`}>{v}</td>)}</tr>)}</tbody></table></div></div></div>)}
          </Card>
        </div>)}</Async>
    </>
  )
}
