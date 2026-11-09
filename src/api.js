// Thin fetch wrapper. Every backend error is shaped { error: { code, message } }.
const BASE = import.meta.env.VITE_API_URL || ''

export class ApiError extends Error {
  constructor(message, code, status, details) { super(message); this.code = code; this.status = status; this.details = details }
}

async function request(path, opts = {}) {
  let res
  try { res = await fetch(`${BASE}/api${path}`, opts) }
  catch { throw new ApiError('Cannot reach the backend. Is `python app.py` running on port 5000?', 'network', 0) }
  let data = null
  try { data = await res.json() } catch { /* non-JSON */ }
  if (!res.ok) {
    const e = data?.error
    throw new ApiError(e?.message || `Request failed (${res.status})`, e?.code || 'http_error', res.status, e?.details)
  }
  return data
}

const json = (method, body) => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
const qs = (o) => { const p = new URLSearchParams(Object.entries(o).filter(([, v]) => v !== '' && v != null)); const s = p.toString(); return s ? `?${s}` : '' }

export const api = {
  overview: () => request('/overview'),
  datasets: () => request('/datasets'),
  upload: (file, name) => { const f = new FormData(); f.append('file', file); if (name) f.append('name', name); return request('/datasets/upload', { method: 'POST', body: f }) },
  activate: (id) => request(`/datasets/${id}/activate`, { method: 'POST' }),
  remove: (id) => request(`/datasets/${id}`, { method: 'DELETE' }),
  train: () => request('/train', { method: 'POST' }),
  predict: (text) => request('/predict', json('POST', { text })),
  history: () => request('/predictions/history'),
  planning: () => request('/planning'),
  search: (query, top_k, specialty) => request('/search', json('POST', { query, top_k, specialty })),
  specialties: () => request('/specialties'),
  terms: () => request('/terms?n=20'),
  context: (term) => request(`/context${qs({ term, limit: 10 })}`),
  clusters: (k) => request(`/clusters${qs({ k })}`),
  reduction: (method) => request(`/reduction${qs({ method })}`),
  entities: (text) => request('/entities', json('POST', { text })),
  entitySummary: (n) => request(`/entities/summary${qs({ n })}`),
  wsdSenses: () => request('/wsd/senses'),
  wsd: (sentence, term) => request('/wsd', json('POST', { sentence, term })),
  lifestyle: () => request('/lifestyle'),
  evaluation: () => request('/evaluation'),
  importance: (specialty) => request(`/feature-importance${qs({ specialty })}`),
  requirements: () => request('/requirements'),
  structuredTrain: (file, target) => { const f = new FormData(); f.append('file', file); f.append('target', target); return request('/structured/train', { method: 'POST', body: f }) },
}
