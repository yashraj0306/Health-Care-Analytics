import { useState } from 'react'
import { Async, Card, Note, PageHeader, Stat, Table, num, useApi } from '../components/ui.jsx'
import { HBar } from '../components/charts.jsx'
import { api } from '../api.js'

export default function Planning() {
  const s = useApi(api.planning)
  const [sort, setSort] = useState('report_count')
  return (
    <>
      <PageHeader title="Healthcare Planning Indicators" subtitle="Report volume, length and share by specialty, plus a transparent percentile-rank priority score (notebook T8/T9)." />
      <Async state={s}>{(d) => {
        const rows = [...d.specialties].sort((a, b) => b[sort] - a[sort])
        return (<div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
            <Stat label="Report listings" value={num(d.n_reports)} /><Stat label="Specialties" value={d.n_specialties} /><Stat label="Top-5 share" value={`${d.top5_share_percent}%`} hint="of all report listings" />
          </div>
          <div className="grid gap-6 xl:grid-cols-2">
            <Card title="Top 10 specialties by report count"><HBar data={rows.slice(0, 10)} x="report_count" y="specialty" /></Card>
            <Card title="Review priority score (top 10)"><HBar data={[...d.specialties].sort((a, b) => b.review_priority_score - a.review_priority_score || b.report_count - a.report_count).slice(0, 10)} x="review_priority_score" y="specialty" color="#2563eb" /></Card>
          </div>
          <Card title="All specialties" action={<select className="input !w-auto" value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Sort by">
            {[['report_count', 'Report count'], ['share_percent', 'Share %'], ['average_words', 'Avg words'], ['review_priority_score', 'Priority score']].map(([v, l]) => <option key={v} value={v}>Sort: {l}</option>)}</select>}>
            <div className="max-h-96 overflow-auto"><Table rows={rows} columns={[{ key: 'specialty', label: 'Specialty' }, { key: 'report_count', label: 'Listings', right: true }, { key: 'unique_reports', label: 'Unique', right: true },
              { key: 'share_percent', label: 'Share %', right: true }, { key: 'average_words', label: 'Avg words', right: true }, { key: 'review_priority_score', label: 'Priority', right: true }]} /></div>
          </Card>
          <Card title="Data quality (raw file)"><Table rows={d.quality} columns={[{ key: 'column', label: 'Column' }, { key: 'missing', label: 'Missing', right: true }, { key: 'missing_pct', label: 'Missing %', right: true }, { key: 'unique', label: 'Unique values', right: true }]} /></Card>
          <Note tone="warn"><ul className="list-disc pl-4">{d.caveats.map((c) => <li key={c}>{c}</li>)}</ul></Note></div>)
      }}</Async>
    </>
  )
}
