import { useState } from 'react'
import { Async, Card, Note, PageHeader, Stat, useApi } from '../components/ui.jsx'
import { Groups } from '../components/charts.jsx'
import { api } from '../api.js'

export default function Clusters() {
  const [k, setK] = useState(5)
  const s = useApi(() => api.clusters(k), [k])
  return (
    <>
      <PageHeader title="K-Means Clustering" subtitle="Unsupervised grouping of notes in TF-IDF space, compared against the known specialty labels (notebook T10).">
        <label className="flex items-center gap-2 text-sm">Clusters (k)
          <select className="input !w-20" value={k} onChange={(e) => setK(+e.target.value)}>{[2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => <option key={n}>{n}</option>)}</select></label>
      </PageHeader>
      <Async state={s} label="Clustering…">{(d) => (
        <div className="space-y-6">
          <div className="grid grid-cols-3 gap-4"><Stat label="Silhouette" value={d.silhouette} hint="−1 … 1; higher = cleaner clusters" /><Stat label="Adjusted Rand vs specialty" value={d.adjusted_rand_vs_specialty ?? '—'} hint="0 = random agreement" /><Stat label="Documents" value={d.n_documents} /></div>
          <Note>{d.note}</Note>
          <Card title="Clusters projected to 2-D (TruncatedSVD, sample of up to 1,500 notes)">
            <Groups points={d.points.map((p) => ({ ...p, group: `Cluster ${p.cluster}` }))} groupKey="group" /></Card>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{d.clusters.map((c) => (
            <Card key={c.cluster} title={`Cluster ${c.cluster} · ${c.size} notes`}>
              <p className="text-xs text-slate-500">Top terms</p><p className="mb-2 text-sm">{c.top_terms.join(', ')}</p>
              <p className="text-xs text-slate-500">Most common specialties</p>
              <ul className="text-sm">{c.top_specialties.map((s) => <li key={s.specialty} className="flex justify-between"><span>{s.specialty}</span><span className="tabular-nums text-slate-600">{(s.share * 100).toFixed(1)}%</span></li>)}</ul></Card>))}</div>
        </div>)}</Async>
    </>
  )
}
