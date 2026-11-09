"""T7/T8/T15 – medical specialty classification, evaluation, feature importance.

Fixes vs. the notebook
* Evaluation uses *unique notes* so identical text never sits in both train and test.
* The notebook's original (row-level, duplicate-conflicted) protocol is re-run and
  reported next to the fixed one, so the 9.9% figure is explained, not hidden.
* T15 looked for a 'preprocessor' step and `feature_importances_`, neither of which
  exists on TF-IDF + LinearSVC. Importance now comes from the SVM coefficients.
"""
import json
from datetime import datetime, timezone

import joblib
import numpy as np
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from .data import LABEL, TEXT, UNKNOWN
from .errors import ApiError

MIN_CLASS = 5
MODEL_FILE, METRICS_FILE = "specialty_model.joblib", "specialty_metrics.json"


def build_pipeline(max_features=10000, min_df=1):
    return Pipeline([
        ("tfidf", TfidfVectorizer(max_features=max_features, stop_words="english",
                                  ngram_range=(1, 2), min_df=min_df, sublinear_tf=True)),
        ("classifier", LinearSVC()),
    ])


def _notebook_baseline(df):
    """Re-run the original T7 protocol (row-level split, duplicates kept)."""
    d = df[df[LABEL] != UNKNOWN]
    d = d[d[LABEL].isin(d[LABEL].value_counts()[lambda s: s >= 2].index)]
    X, y = d[TEXT].str.lower(), d[LABEL]
    a, b, c, e = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    m = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=10000, stop_words="english", ngram_range=(1, 2))),
        ("classifier", LinearSVC()),
    ]).fit(a, c)
    p = m.predict(b)
    train_set = set(a)
    in_train = sum(t in train_set for t in b)
    return {
        "protocol": "Original notebook: random row split, cross-listed duplicates kept",
        "n_rows": int(len(d)), "test_rows": int(len(b)),
        "accuracy": round(float(accuracy_score(e, p)), 4),
        "weighted_f1": round(float(f1_score(e, p, average="weighted", zero_division=0)), 4),
        "test_rows_whose_text_is_also_in_train": int(in_train),
    }


def train(ds):
    ds.require_labels()
    notes = ds.notes[ds.notes[LABEL] != UNKNOWN]
    keep = notes[LABEL].value_counts()
    keep = keep[keep >= MIN_CLASS].index
    dropped = int((~notes[LABEL].isin(keep)).sum())
    notes = notes[notes[LABEL].isin(keep)]
    X, y = notes[TEXT].to_numpy(object), notes[LABEL].to_numpy(object)
    idx = np.arange(len(notes))
    tr, te = train_test_split(idx, test_size=0.2, random_state=42, stratify=y)
    model = build_pipeline(min_df=2 if len(notes) > 500 else 1).fit(X[tr], y[tr])

    scores = model.decision_function(X[te])
    classes = model.classes_
    pred = classes[scores.argmax(1)] if scores.ndim > 1 else model.predict(X[te])
    truth = y[te]
    all_specs = notes["all_specialties"].to_numpy(object)[te]
    top3 = (np.mean([t in classes[np.argsort(-s)[:3]] for t, s in zip(truth, scores)])
            if scores.ndim > 1 else None)
    report = classification_report(truth, pred, output_dict=True, zero_division=0)
    per_class = [{"specialty": k, **{m: round(float(v[m]), 3) for m in ("precision", "recall", "f1-score")},
                  "support": int(v["support"])}
                 for k, v in report.items() if k in set(classes)]
    top10 = notes[LABEL].value_counts().head(10).index.tolist()
    mask = np.isin(truth, top10)
    cm = confusion_matrix(truth[mask], pred[mask], labels=top10, normalize="true")
    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sklearn_version": sklearn.__version__,
        "protocol": "Unique notes, stratified 80/20 split, random_state=42; label = least-frequent listed specialty",
        "n_notes": int(len(notes)), "n_train": int(len(tr)), "n_test": int(len(te)),
        "n_classes": int(len(classes)), "classes_dropped_notes": dropped,
        "min_class_size": MIN_CLASS,
        "accuracy": round(float(accuracy_score(truth, pred)), 4),
        "macro_f1": round(float(f1_score(truth, pred, average="macro", zero_division=0)), 4),
        "weighted_f1": round(float(f1_score(truth, pred, average="weighted", zero_division=0)), 4),
        "top3_accuracy": None if top3 is None else round(float(top3), 4),
        "any_listed_specialty_accuracy": round(float(np.mean([p in s for p, s in zip(pred, all_specs)])), 4),
        "majority_class_baseline": round(float(pd_max_share(y[te])), 4),
        "per_class": sorted(per_class, key=lambda r: -r["support"]),
        "confusion_top10": {"labels": top10, "matrix": np.round(cm, 3).tolist()},
        "notebook_baseline": _notebook_baseline(ds.df),
    }
    ds.model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, ds.model_dir / MODEL_FILE, compress=3)
    (ds.model_dir / METRICS_FILE).write_text(json.dumps(metrics))
    ds.cache.pop("model", None)
    ds.cache["metrics"] = metrics
    ds.cache["model"] = model
    return metrics


def pd_max_share(y):
    _, counts = np.unique(y, return_counts=True)
    return counts.max() / counts.sum()


def get_model(ds, auto_train=True):
    """Load the saved pipeline, retraining if absent or from another sklearn version."""
    if "model" in ds.cache:
        return ds.cache["model"]
    mp, jp = ds.model_dir / MODEL_FILE, ds.model_dir / METRICS_FILE
    if mp.exists() and jp.exists():
        metrics = json.loads(jp.read_text())
        if metrics.get("sklearn_version") == sklearn.__version__:
            ds.cache["model"] = joblib.load(mp)
            ds.cache["metrics"] = metrics
            return ds.cache["model"]
    if not auto_train:
        raise ApiError("No trained model for this dataset yet. POST /api/train first.", 409, "model_missing")
    train(ds)
    return ds.cache["model"]


def get_metrics(ds):
    get_model(ds)
    return ds.cache["metrics"]


def predict(ds, text, top_k=3):
    model = get_model(ds)
    scores = model.decision_function([text])[0]
    order = np.argsort(-scores)[:top_k]
    classes = model.classes_
    # softmax over margins -> a *relative* confidence, NOT a calibrated probability
    e = np.exp(scores - scores.max())
    rel = e / e.sum()
    return [{"specialty": str(classes[i]), "score": round(float(scores[i]), 4),
             "relative_confidence": round(float(rel[i]), 4)} for i in order]


def feature_importance(ds, specialty=None, top_n=15):
    model = get_model(ds)
    vec, clf = model.named_steps["tfidf"], model.named_steps["classifier"]
    terms = np.array(vec.get_feature_names_out())
    coef = clf.coef_
    classes = clf.classes_
    if coef.shape[0] == 1:                       # binary case
        coef = np.vstack([-coef[0], coef[0]])
    if specialty:
        if specialty not in set(classes):
            raise ApiError(f"Unknown specialty '{specialty}'.", 404, "not_found")
        row = coef[list(classes).index(specialty)]
        pos = np.argsort(-row)[:top_n]
        neg = np.argsort(row)[:top_n]
        return {"specialty": specialty,
                "positive": [{"term": terms[i], "weight": round(float(row[i]), 4)} for i in pos],
                "negative": [{"term": terms[i], "weight": round(float(row[i]), 4)} for i in neg]}
    g = np.abs(coef).mean(0)
    top = np.argsort(-g)[:top_n]
    return {"specialty": None, "global": [{"term": terms[i], "weight": round(float(g[i]), 4)} for i in top],
            "note": "Mean |coefficient| across all one-vs-rest LinearSVC classifiers."}
