import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { Activity, BarChart3, Boxes, Database, FileSearch, FlaskConical, Gauge, HeartPulse, Menu, Microscope, ScatterChart, Stethoscope, Tags, X, ShieldAlert } from 'lucide-react'

const NAV = [
  ['/', 'Dashboard', Gauge], ['/datasets', 'Datasets', Database], ['/predict', 'Specialty Prediction', Stethoscope],
  ['/planning', 'Planning Indicators', BarChart3], ['/search', 'Clinical Text Search', FileSearch],
  ['/clusters', 'K-Means Clusters', Boxes], ['/entities', 'Entity Extraction', Tags], ['/wsd', 'Word Senses', Microscope],
  ['/visualization', 'PCA / SVD', ScatterChart], ['/lifestyle', 'Lifestyle Analysis', Activity],
  ['/evaluation', 'Model Evaluation', FlaskConical], ['/requirements', 'Data Requirements', ShieldAlert],
]

export default function Layout() {
  const [open, setOpen] = useState(false)
  const nav = (
    <nav className="flex flex-col gap-0.5 p-3">
      {NAV.map(([to, label, Icon]) => (
        <NavLink key={to} to={to} end={to === '/'} onClick={() => setOpen(false)}
          className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${isActive ? 'bg-brand-700 text-white' : 'text-slate-300 hover:bg-slate-800'}`}>
          <Icon className="h-4 w-4" />{label}</NavLink>))}
    </nav>
  )
  return (
    <div className="min-h-screen lg:flex">
      <aside className="hidden w-64 shrink-0 bg-slate-900 lg:block">
        <div className="flex items-center gap-2 px-5 py-5 text-white"><HeartPulse className="h-6 w-6 text-brand-500" /><span className="font-semibold">Healthcare Analytics</span></div>{nav}
      </aside>
      <div className="flex items-center justify-between bg-slate-900 px-4 py-3 text-white lg:hidden">
        <span className="flex items-center gap-2 font-semibold"><HeartPulse className="h-5 w-5 text-brand-500" />Healthcare Analytics</span>
        <button aria-label="Toggle menu" onClick={() => setOpen(!open)}>{open ? <X /> : <Menu />}</button>
      </div>
      {open && <div className="bg-slate-900 lg:hidden">{nav}</div>}
      <main className="min-w-0 flex-1 p-4 sm:p-6 lg:p-8"><Outlet />
        <footer className="mt-10 border-t border-slate-200 pt-4 text-xs text-slate-500">
          Educational analytics on public MTSamples transcriptions. Not a clinical decision tool; not validated for patient care.</footer>
      </main>
    </div>
  )
}
