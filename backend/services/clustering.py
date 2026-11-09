"""T10 – K-Means on TF-IDF vectors, compared with the known specialty labels."""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import adjusted_rand_score, silhouette_score

from .data import LABEL, UNKNOWN
from .errors import ApiError
from .search import get_index
from .store import cached


def run(ds, k=5, max_points=1500):
    if not isinstance(k, int) or not 2 <= k <= 12:
        raise ApiError("k must be an integer between 2 and 12.", 400, "invalid_parameter")
    if len(ds.notes) < k + 1:
        raise ApiError("Not enough documents for that many clusters.", 422, "too_few_documents")
    return cached(ds, ("clusters", k), lambda: _run(ds, k, max_points))


def _run(ds, k, max_points):
    idx = get_index(ds)
    X, terms = idx["matrix"], np.array(idx["vectorizer"].get_feature_names_out())
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    sil = float(silhouette_score(X, labels))
    notes = ds.notes.assign(cluster=labels)
    clusters = []
    for c in range(k):
        mask = labels == c
        top = np.asarray(X[mask].mean(axis=0)).ravel().argsort()[-10:][::-1]
        comp = notes[mask][LABEL].value_counts(normalize=True).head(3)
        clusters.append({"cluster": c, "size": int(mask.sum()), "top_terms": terms[top].tolist(),
                         "top_specialties": [{"specialty": s, "share": round(float(v), 3)} for s, v in comp.items()]})
    known = notes[LABEL] != UNKNOWN
    ari = float(adjusted_rand_score(notes[LABEL][known], labels[known])) if known.sum() > 1 else None
    coords = TruncatedSVD(n_components=2, random_state=42).fit_transform(X)
    sel = np.random.RandomState(42).permutation(len(coords))[:max_points]
    return {"k": k, "silhouette": round(sil, 4),
            "adjusted_rand_vs_specialty": None if ari is None else round(ari, 4),
            "n_documents": int(len(labels)), "clusters": clusters,
            "points": [{"x": round(float(coords[i, 0]), 4), "y": round(float(coords[i, 1]), 4),
                        "cluster": int(labels[i])} for i in sel],
            "note": "Silhouette is computed on the 3,000-term TF-IDF space; low values (<0.1) are typical for clinical text."}
