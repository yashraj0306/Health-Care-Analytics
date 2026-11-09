import { useState } from 'react'
import { Async, Card, Note, PageHeader, Stat, Table, pct, useApi } from '../components/ui.jsx'
import { HBar, Heatmap } from '../components/charts.jsx'
import { api } from '../api.js'

export default function Evaluation() {
  const s = useApi(api.evaluation)
  const [spec, setSpec] = useState('')
  const imp = useApi(() => api.importance(spec), [spec])
  return (
    <>
      <PageHeader title="Model Evaluation" subtitle="Held-out metrics of the saved specialty model, the explanation for the notebook's low accuracy, and feature importance (fixed T15)." />
      <Async state={s} label="Evaluating (first run trains the model)…">{(d) => {
        const m = d.classification, b = m.notebook_baseline
        return (<div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            <Stat label="Accuracy" value={pct(m.accuracy)} hint={`${m.n_test} held-out notes`} /><Stat label="Top-3 accuracy" value={pct(m.top3_accuracy)} />
            <Stat label="Macro F1" value={m.macro_f1} /><Stat label="Weighted F1" value={m.weighted_f1} /><Stat label="Any listed specialty" value={pct(m.any_listed_specialty_accuracy)} hint="prediction ∈ note's specialties" />
          </div>
          <Card title="Why the notebook reported ~10% accuracy">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-lg border border-red-200 bg-red-50 p-4"><div className="text-xs font-semibold uppercase text-red-700">Original protocol</div><div className="mt-1 text-3xl font-semibold text-red-800">{pct(b.accuracy)}</div>
                <p className="mt-1 text-sm text-red-900">{b.protocol}. {b.test_rows_whose_text_is_also_in_train} of {b.test_rows} test rows have text that also appears in training, often under a <i>different</i> specialty label.</p></div>
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4"><div className="text-xs font-semibold uppercase text-emerald-700">This app</div><div className="mt-1 text-3xl font-semibold text-emerald-800">{pct(m.accuracy)}</div>
                <p className="mt-1 text-sm text-emerald-900">{m.protocol}. Majority-class baseline: {pct(m.majority_class_baseline)}.</p></div></div>
            <p className="mt-3 text-xs text-slate-500">Both numbers are computed live from the data. Labels are a modelling choice (one label per note), so “Any listed specialty” is reported as a more forgiving view; accuracy depends on that choice.</p>
          </Card>
          <div className="grid gap-6 xl:grid-cols-2">
            <Card title="Confusion matrix"><Heatmap labels={m.confusion_top10.labels} matrix={m.confusion_top10.matrix} /></Card>
            <Card title="Feature importance (LinearSVC coefficients)" action={<select className="input !w-56" value={spec} onChange={(e) => setSpec(e.target.value)} aria-label="Specialty">
              <option value="">Global (all classes)</option>{m.per_class.map((c) => <option key={c.specialty}>{c.specialty}</option>)}</select>}>
              <Async state={imp}>{(i) => i.global ? <HBar data={i.global} x="weight" y="term" labelWidth={110} /> : <HBar data={i.positive} x="weight" y="term" labelWidth={110} />}</Async>
              <p className="mt-2 text-xs text-slate-500">Terms with the largest positive weight push a note toward {spec || 'any specialty (mean |weight|)'}. Not causal.</p></Card>
          </div>
          <Card title="Per-specialty results (held-out)"><div className="max-h-96 overflow-auto"><Table rows={m.per_class} columns={[{ key: 'specialty', label: 'Specialty' }, { key: 'precision', label: 'Precision', right: true }, { key: 'recall', label: 'Recall', right: true }, { key: 'f1-score', label: 'F1', right: true }, { key: 'support', label: 'Support', right: true }]} /></div>
            <p className="mt-2 text-xs text-slate-500">Classes with only 1–3 test notes give very noisy precision/recall.</p></Card>
          <div className="grid gap-4 md:grid-cols-2">
            <Card title="Clustering quality (k=5)"><p className="text-sm">Silhouette <b>{d.clustering.silhouette}</b> · Adjusted Rand vs specialty <b>{d.clustering.adjusted_rand_vs_specialty}</b></p><p className="mt-1 text-xs text-slate-500">Values near 0 mean the K-Means groups only weakly align with specialties.</p></Card>
            <Card title="Weight-mention model">{d.lifestyle_model.available ? <p className="text-sm">Accuracy <b>{pct(d.lifestyle_model.accuracy)}</b> · AUC <b>{d.lifestyle_model.auc}</b> (trigger words masked)</p> : <p className="text-sm">{d.lifestyle_model.reason}</p>}</Card>
          </div>
          <Note>Trained {m.trained_at} · scikit-learn {m.sklearn_version} · {m.n_notes} notes, {m.n_classes} classes (≥{m.min_class_size} notes each). The saved model is the one evaluated (trained on the 80% split only).</Note>
        </div>)
      }}</Async>
    </>
  )
}
