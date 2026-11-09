import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Datasets from './pages/Datasets.jsx'
import Predict from './pages/Predict.jsx'
import Planning from './pages/Planning.jsx'
import Search from './pages/Search.jsx'
import Clusters from './pages/Clusters.jsx'
import Entities from './pages/Entities.jsx'
import Wsd from './pages/Wsd.jsx'
import Visualization from './pages/Visualization.jsx'
import Lifestyle from './pages/Lifestyle.jsx'
import Evaluation from './pages/Evaluation.jsx'
import Requirements from './pages/Requirements.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="datasets" element={<Datasets />} />
        <Route path="predict" element={<Predict />} />
        <Route path="planning" element={<Planning />} />
        <Route path="search" element={<Search />} />
        <Route path="clusters" element={<Clusters />} />
        <Route path="entities" element={<Entities />} />
        <Route path="wsd" element={<Wsd />} />
        <Route path="visualization" element={<Visualization />} />
        <Route path="lifestyle" element={<Lifestyle />} />
        <Route path="evaluation" element={<Evaluation />} />
        <Route path="requirements" element={<Requirements />} />
        <Route path="*" element={<div className="p-8 text-slate-600">Page not found.</div>} />
      </Route>
    </Routes>
  )
}
