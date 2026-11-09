import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from 'recharts'
import { PALETTE } from './ui.jsx'

const axis = { fontSize: 11, fill: '#475569' }

export function HBar({ data, x, y, height, color = PALETTE[0], labelWidth = 170, fmt }) {
  const h = height || Math.max(220, data.length * 28 + 40)
  return (
    <ResponsiveContainer width="100%" height={h}>
      <BarChart data={data} layout="vertical" margin={{ left: 4, right: 16, top: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} stroke="#e2e8f0" />
        <XAxis type="number" tick={axis} /><YAxis type="category" dataKey={y} width={labelWidth} tick={axis} interval={0} />
        <Tooltip formatter={(v) => (fmt ? fmt(v) : v)} cursor={{ fill: '#f1f5f9' }} />
        <Bar dataKey={x} fill={color} radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

/** Scatter coloured by a categorical key. */
export function Groups({ points, groupKey, xLabel = 'Component 1', yLabel = 'Component 2', height = 440 }) {
  const groups = [...new Set(points.map((p) => p[groupKey]))]
  const colour = (g) => (g === 'Other' ? '#cbd5e1' : PALETTE[groups.filter((x) => x !== 'Other').indexOf(g) % PALETTE.length])
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ScatterChart margin={{ left: 4, right: 16, top: 8, bottom: 16 }}>
        <CartesianGrid stroke="#e2e8f0" />
        <XAxis type="number" dataKey="x" name={xLabel} tick={axis} label={{ value: xLabel, position: 'insideBottom', offset: -8, fontSize: 11 }} />
        <YAxis type="number" dataKey="y" name={yLabel} tick={axis} label={{ value: yLabel, angle: -90, position: 'insideLeft', fontSize: 11 }} />
        <ZAxis range={[28, 28]} /><Tooltip cursor={{ strokeDasharray: '3 3' }} />
        <Legend verticalAlign="bottom" wrapperStyle={{ fontSize: 11, paddingTop: 12 }} />
        {groups.map((g) => <Scatter key={g} name={String(g)} data={points.filter((p) => p[groupKey] === g)} fill={colour(g)} fillOpacity={0.65} isAnimationActive={false} />)}
      </ScatterChart>
    </ResponsiveContainer>
  )
}

export function Roc({ roc, auc }) {
  const data = [{ fpr: 0, chance: 0 }, ...roc.map((p) => ({ fpr: p.fpr, tpr: p.tpr })), { fpr: 1, chance: 1 }]
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={roc} margin={{ left: 0, right: 16, top: 8, bottom: 16 }}>
        <CartesianGrid stroke="#e2e8f0" /><XAxis type="number" dataKey="fpr" domain={[0, 1]} tick={axis} label={{ value: 'False positive rate', position: 'insideBottom', offset: -8, fontSize: 11 }} />
        <YAxis type="number" domain={[0, 1]} tick={axis} /><Tooltip />
        <Line dataKey="tpr" dot={false} stroke={PALETTE[0]} strokeWidth={2} name={`ROC (AUC ${auc})`} />
        <Line data={[{ fpr: 0, tpr: 0 }, { fpr: 1, tpr: 1 }]} dataKey="tpr" dot={false} stroke="#94a3b8" strokeDasharray="4 4" name="Chance" />
        <Legend verticalAlign="top" wrapperStyle={{ fontSize: 11 }} />
      </LineChart>
    </ResponsiveContainer>
  )
}

/** Row-normalised confusion matrix as a CSS grid heat-map. */
export function Heatmap({ labels, matrix }) {
  return (
    <div className="overflow-x-auto"><div className="inline-block min-w-full pr-28">
      <table className="border-collapse text-[10px]"><thead><tr><th className="p-1" />{labels.map((l) => (
        <th key={l} className="h-28 w-9 align-bottom"><div className="origin-bottom-left -rotate-45 whitespace-nowrap pl-3 text-left font-normal text-slate-600" style={{ width: 20 }}>{l}</div></th>))}</tr></thead>
        <tbody>{matrix.map((row, i) => (<tr key={labels[i]}><th className="whitespace-nowrap pr-2 text-right font-normal text-slate-600">{labels[i]}</th>
          {row.map((v, j) => <td key={j} title={`${labels[i]} → ${labels[j]}: ${(v * 100).toFixed(0)}%`}
            className="h-9 w-9 text-center" style={{ background: `rgba(15,118,110,${Math.min(1, v)})`, color: v > 0.5 ? '#fff' : '#334155' }}>{v >= 0.01 ? v.toFixed(2).replace(/^0/, '') : ''}</td>)}</tr>))}
        </tbody></table>
      <p className="mt-2 text-xs text-slate-500">Rows = true specialty, columns = predicted (row-normalised recall). Top 10 specialties.</p>
    </div></div>
  )
}

export { Cell }
