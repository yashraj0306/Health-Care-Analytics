"""T9/T10/T12 – TF-IDF term ranking, clinical text search, term-in-context."""
import re

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .data import LABEL, TEXT
from .errors import ApiError
from .store import cached

INDEX_FILE = "search_index.joblib"


def get_index(ds):
    def build():
        path = ds.model_dir / INDEX_FILE
        if path.exists():
            idx = joblib.load(path)
            if idx["n_docs"] == len(ds.notes):
                return idx
        vec = TfidfVectorizer(stop_words="english", max_features=3000, ngram_range=(1, 2), min_df=2)
        X = vec.fit_transform(ds.notes[TEXT])
        idx = {"vectorizer": vec, "matrix": X, "n_docs": len(ds.notes)}
        ds.model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(idx, path, compress=3)
        return idx
    return cached(ds, "search_index", build)


def top_terms(ds, n=20):
    idx = get_index(ds)
    terms = np.array(idx["vectorizer"].get_feature_names_out())
    mean = np.asarray(idx["matrix"].mean(axis=0)).ravel()
    top = mean.argsort()[-n:][::-1]
    return [{"term": terms[i], "mean_tfidf": round(float(mean[i]), 5)} for i in top]


def search(ds, query, top_k=10, specialty=None):
    idx = get_index(ds)
    qv = idx["vectorizer"].transform([query])
    if qv.nnz == 0:
        return {"query": query, "results": [], "note": "None of the query terms are in the vocabulary."}
    sims = cosine_similarity(qv, idx["matrix"]).ravel()
    if specialty:
        ok = ds.notes["all_specialties"].apply(lambda s: specialty in s).to_numpy()
        sims = np.where(ok, sims, 0.0)
    order = [i for i in np.argsort(-sims)[:top_k] if sims[i] > 0]
    rows = ds.notes.iloc[order]
    return {"query": query, "results": [
        {"similarity": round(float(sims[i]), 4), "specialty": r[LABEL],
         "all_specialties": r["all_specialties"], "sample_name": str(r.get("sample_name", "")).strip(),
         "snippet": r[TEXT][:350]}
        for i, (_, r) in zip(order, rows.iterrows())]}


def term_context(ds, term, limit=10, before=100, after=150):
    term = term.strip()
    pat = re.compile(re.escape(term), re.IGNORECASE)
    mask = ds.notes[TEXT].str.contains(pat, na=False)
    total = int(mask.sum())
    out = []
    for _, r in ds.notes[mask].head(limit).iterrows():
        m = pat.search(r[TEXT])
        out.append({"specialty": r[LABEL],
                    "before": r[TEXT][max(0, m.start() - before):m.start()],
                    "match": m.group(0),
                    "after": r[TEXT][m.end():m.end() + after]})
    by_spec = (ds.notes[mask][LABEL].value_counts().head(8)
               .rename_axis("specialty").reset_index(name="notes").to_dict("records"))
    return {"term": term, "total_notes": total, "by_specialty": by_spec, "contexts": out}
