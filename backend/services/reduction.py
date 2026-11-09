"""T13 – PCA on numeric text statistics and TruncatedSVD on TF-IDF."""
import re

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.preprocessing import StandardScaler

from .data import LABEL, TEXT
from .errors import ApiError
from .search import get_index
from .store import cached

FEATURES = ["word_count", "character_count", "sentence_count", "unique_word_count"]


def run(ds, method):
    if method not in ("pca", "svd"):
        raise ApiError("method must be 'pca' or 'svd'.", 400, "invalid_parameter")
    return cached(ds, ("reduction", method), lambda: _pca(ds) if method == "pca" else _svd(ds))


def _groups(ds, n=8):
    top = ds.notes[LABEL].value_counts().head(n).index
    return ds.notes[LABEL].where(ds.notes[LABEL].isin(top), "Other").tolist()


def _pca(ds):
    t = ds.notes[TEXT]
    feats = pd.DataFrame({
        "word_count": t.str.split().str.len(), "character_count": t.str.len(),
        "sentence_count": t.str.count(r"[.!?]+"),
        "unique_word_count": t.apply(lambda x: len(set(re.findall(r"\b\w+\b", x.lower())))),
    }).fillna(0)
    Z = StandardScaler().fit_transform(feats)
    pca = PCA(n_components=2).fit(Z)
    C = pca.transform(Z)
    groups = _groups(ds)
    return {"method": "pca", "input": "4 numeric text statistics (standardised)",
            "explained_variance": [round(float(v), 4) for v in pca.explained_variance_ratio_],
            "total_explained_variance": round(float(pca.explained_variance_ratio_.sum()), 4),
            "loadings": [{"feature": f, "pc1": round(float(a), 3), "pc2": round(float(b), 3)}
                         for f, a, b in zip(FEATURES, pca.components_[0], pca.components_[1])],
            "points": [{"x": round(float(C[i, 0]), 3), "y": round(float(C[i, 1]), 3), "group": groups[i]}
                       for i in range(len(C))]}


def _svd(ds):
    X = get_index(ds)["matrix"]
    svd = TruncatedSVD(n_components=2, random_state=42)
    C = svd.fit_transform(X)
    groups = _groups(ds)
    return {"method": "svd", "input": "TF-IDF (3,000 uni/bi-grams)",
            "explained_variance": [round(float(v), 4) for v in svd.explained_variance_ratio_],
            "total_explained_variance": round(float(svd.explained_variance_ratio_.sum()), 4),
            "points": [{"x": round(float(C[i, 0]), 4), "y": round(float(C[i, 1]), 4), "group": groups[i]}
                       for i in range(len(C))]}
