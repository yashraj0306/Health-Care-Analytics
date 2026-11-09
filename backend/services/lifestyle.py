"""T14 + notebook cell 21 – lifestyle mentions and a text 'weight mention' classifier.

Honesty notes
* Counts are *keyword mentions in transcribed notes*, not patient-level prevalence.
* The notebook trained a model to predict a label that is *defined by a regex on the
  same text*, so the model could simply rediscover the keywords (target leakage).
  Here the trigger words are masked before training so the classifier must use
  surrounding context. It remains a text-mention classifier, NOT an obesity predictor.
"""
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             roc_auc_score, roc_curve)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .data import LABEL, TEXT
from .errors import ApiError
from .store import cached

PATTERNS = {
    "Diet and nutrition": r"\bdiet\b|\bnutrition\b|\bcalorie",
    "Physical activity": r"\bexercise\b|\bphysical activity\b|\bwalking\b",
    "Obesity and weight": r"\bobesity\b|\bobese\b|\bweight\b|\bBMI\b",
    "Smoking": r"\bsmoking\b|\btobacco\b|\bcigarette",
    "Sleep": r"\bsleep\b|\binsomnia\b|\bsleep apnea\b",
}
MASK = re.compile(r"\bobesity\b|\bobese\b|\boverweight\b|\bweight\w*\b|\bbmi\b|\bbody mass index\b", re.I)


def flags(ds):
    t = ds.notes[TEXT]
    return {k: t.str.contains(p, case=False, regex=True, na=False) for k, p in PATTERNS.items()}


def run(ds):
    return cached(ds, "lifestyle", lambda: _run(ds))


def _run(ds):
    f = flags(ds)
    n = len(ds.notes)
    counts = [{"topic": k, "notes": int(v.sum()), "percent": round(float(v.mean() * 100), 1)} for k, v in f.items()]
    counts.sort(key=lambda r: r["notes"])
    by_spec = ds.notes[[LABEL]].copy()
    for k, v in f.items():
        by_spec[k] = v.values
    agg = by_spec.groupby(LABEL)[list(PATTERNS)].sum()
    agg["total_notes"] = by_spec.groupby(LABEL).size()
    agg = agg.sort_values("Obesity and weight", ascending=False).head(10).reset_index()
    return {"n_notes": n, "counts": counts,
            "by_specialty": agg.rename(columns={LABEL: "specialty"}).to_dict("records"),
            "topics": list(PATTERNS),
            "model": _weight_model(ds, f["Obesity and weight"]),
            "caveat": "Keyword mentions only (a note may mention 'weight' as a measurement). No fabricated obesity prevalence."}


def _weight_model(ds, target):
    y = target.astype(int).to_numpy()
    if len(np.unique(y)) < 2 or np.bincount(y).min() < 10:
        return {"available": False, "reason": "Too few examples in one class."}
    X = ds.notes[TEXT].str.replace(MASK, " ", regex=True).to_numpy(object)
    a, b, c, e = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    m = Pipeline([("tfidf", TfidfVectorizer(stop_words="english", max_features=3000, ngram_range=(1, 2))),
                  ("classifier", LogisticRegression(class_weight="balanced", max_iter=1000))]).fit(a, c)
    p, prob = m.predict(b), m.predict_proba(b)[:, 1]
    rep = classification_report(e, p, target_names=["No mention", "Mention"], output_dict=True, zero_division=0)
    fpr, tpr, _ = roc_curve(e, prob)
    keep = np.unique(np.linspace(0, len(fpr) - 1, 80).astype(int))
    names = np.array(m.named_steps["tfidf"].get_feature_names_out())
    coef = m.named_steps["classifier"].coef_[0]
    return {"available": True, "trigger_words_masked": True, "n_train": int(len(a)), "n_test": int(len(b)),
            "positive_rate": round(float(y.mean()), 3),
            "accuracy": round(float(accuracy_score(e, p)), 4),
            "auc": round(float(roc_auc_score(e, prob)), 4),
            "report": {k: {m_: round(float(v[m_]), 3) for m_ in ("precision", "recall", "f1-score")}
                       for k, v in rep.items() if k in ("No mention", "Mention", "macro avg")},
            "confusion": confusion_matrix(e, p).tolist(),
            "roc": [{"fpr": round(float(fpr[i]), 4), "tpr": round(float(tpr[i]), 4)} for i in keep],
            "top_context_terms": names[np.argsort(-coef)[:12]].tolist()}
