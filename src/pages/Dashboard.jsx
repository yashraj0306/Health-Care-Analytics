import { Link } from 'react-router-dom'
import { Async, Card, Note, PageHeader, Stat, num, pct, useApi } from '../components/ui.jsx'
import { HBar } from '../components/charts.jsx'
import { api } from '../api.js'

export default function Dashboard() {
  const s = useApi(api.overview)
  return (
    <>
      <PageHeader title="Dashboard" subtitle="Overview of the active dataset and the specialty model. All numbers come from your data — nothing is hard-coded." />
      <Async state={s} label="Loading dataset…">{(d) => {
        const m = d.model.metrics
        return (<div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Stat label="Dataset" value={d.dataset.name} hint={`${num(d.dataset.rows)} rows`} />
            <Stat label="Unique notes" value={num(d.dataset.unique_notes)} hint={`${d.dataset.multi_listed_pct}% listed under 2+ specialties`} />
            <Stat label="Specialties" value={d.n_specialties} hint={`avg ${d.avg_words} words/note`} />
            <Stat label="Model accuracy" value={m ? pct(m.accuracy) : 'not trained'} hint={m ? `top-3 ${pct(m.top3_accuracy)} · macro F1 ${m.macro_f1}` : 'Trains on first prediction or evaluation'} />
          </div>
          {d.dataset.multi_listed_pct > 20 && <Note tone="warn">{d.dataset.multi_listed_pct}% of distinct notes appear under several specialties, so a naïve random row split leaks identical text between train and test.
            This app de-duplicates notes first — see <Link className="underline" to="/evaluation">Model Evaluation</Link> for the before/after.</Note>}
          <div className="grid gap-6 xl:grid-cols-3">
            <Card title="Top specialties by report listings" className="xl:col-span-2"><HBar data={d.top_specialties} x="reports" y="specialty" /></Card>
            <Card title="Explore">
              <ul className="space-y-2 text-sm">{[['/predict', 'Predict a specialty from text'], ['/search', 'Search clinical text'], ['/clusters', 'Cluster the notes'], ['/entities', 'Extract medical entities'], ['/visualization', 'PCA / SVD maps'], ['/lifestyle', 'Lifestyle mentions']].map(([to, l]) => (
                <li key={to}><Link to={to} className="text-brand-700 hover:underline">{l} →</Link></li>))}</ul>
            </Card>
          </div></div>)
      }}</Async>
    </>
  )
}
