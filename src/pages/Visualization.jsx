import { useState } from 'react'
import { Async, Card, Note, PageHeader, Stat, Table, pct, useApi } from '../components/ui.jsx'
import { Groups } from '../components/charts.jsx'
import { api } from '../api.js'

export default function Visualization() {
  const [m, setM] = useState('svd')
  const s = useApi(() => api.reduction(m), [m])
  return (
    <>
      <PageHeader title="PCA / SVD Visualisation" subtitle="Dimensionality reduction of clinical notes (notebook T13). SVD works on the sparse TF-IDF text matrix; PCA on four numeric text statistics.">
        <div className="inline-flex overflow-hidden rounded-lg border border-slate-300">{[['svd', 'TruncatedSVD (TF-IDF)'], ['pca', 'PCA (text statistics)']].map(([v, l]) => (
          <button key={v} onClick={() => setM(v)} className={`px-3 py-1.5 text-sm ${m === v ? 'bg-brand-700 text-white' : 'bg-white text-slate-700 hover:bg-slate-50'}`}>{l}</button>))}</div>
      </PageHeader>
      <Async state={s} label="Computing projection…">{(d) => (
        <div className="space-y-6">
          <div className="grid grid-cols-3 gap-4"><Stat label="Input" value={d.method.toUpperCase()} hint={d.input} /><Stat label="Explained variance (2 comps)" value={pct(d.total_explained_variance)} hint={d.explained_variance.map((v) => pct(v)).join(' + ')} /><Stat label="Points" value={d.points.length} /></div>
          <Card title="2-D projection · coloured by the 8 largest specialties"><Groups points={d.points} groupKey="group" xLabel={m === 'pca' ? 'PC 1' : 'Component 1'} yLabel={m === 'pca' ? 'PC 2' : 'Component 2'} /></Card>
          {d.loadings && <Card title="PCA loadings"><Table rows={d.loadings} columns={[{ key: 'feature', label: 'Feature' }, { key: 'pc1', label: 'PC1', right: true }, { key: 'pc2', label: 'PC2', right: true }]} /></Card>}
          <Note>{d.total_explained_variance < 0.3 ? 'Two components explain little of the variance, so overlapping clouds are expected: 2-D is a lossy view of high-dimensional text.' : 'Overlap between specialties is normal — many specialties share vocabulary.'}</Note>
        </div>)}</Async>
    </>
  )
}
