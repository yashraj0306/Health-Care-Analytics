"""Structured obesity-category model (the part of T15 that needs a *structured* dataset).

MTSamples contains free text only, so it can't support BMI/age/lifestyle-feature
models. This module trains a RandomForest on a user-supplied CSV (e.g. the UCI
"Estimation of obesity levels" dataset) using a real ColumnTransformer, which is
what the notebook's T15 code assumed (a 'preprocessor' step + feature_importances_).
Nothing is shipped or fabricated: with no upload, the endpoint reports 'requires_dataset'.
"""
import json
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .data import read_csv_flexible
from .errors import ApiError, DataError

FILE, META = "structured_model.joblib", "structured_meta.json"


def status(model_dir):
    p = model_dir / META
    if not p.exists():
        return {"state": "requires_dataset"}
    return {"state": "trained", **json.loads(p.read_text())}


def train(csv_path, target, model_dir):
    df = read_csv_flexible(csv_path)
    df.columns = [str(c).strip() for c in df.columns]
    if target not in df.columns:
        raise DataError(f"Target column '{target}' not found.", {"columns_found": df.columns.tolist()})
    df = df.dropna(subset=[target])
    if len(df) < 50:
        raise DataError("At least 50 labelled rows are required.")
    y = df[target].astype(str)
    vc = y.value_counts()
    if len(vc) < 2 or vc.min() < 2:
        raise DataError("The target needs ≥2 classes with ≥2 rows each.", {"class_counts": vc.to_dict()})
    X = df.drop(columns=[target])
    num = X.select_dtypes(include="number").columns.tolist()
    cat = [c for c in X.columns if c not in num]
    pre = ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                          ("oh", OneHotEncoder(handle_unknown="ignore"))]), cat)])
    model = Pipeline([("preprocessor", pre), ("classifier", RandomForestClassifier(
        n_estimators=300, random_state=42, n_jobs=-1))])
    a, b, c, e = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    model.fit(a, c)
    p = model.predict(b)
    names = model.named_steps["preprocessor"].get_feature_names_out()
    imp = model.named_steps["classifier"].feature_importances_
    top = np.argsort(-imp)[:15]
    meta = {"trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "target": target, "n_rows": int(len(df)), "n_train": int(len(a)), "n_test": int(len(b)),
            "numeric_features": num, "categorical_features": cat, "classes": sorted(vc.index.tolist()),
            "accuracy": round(float(accuracy_score(e, p)), 4),
            "weighted_f1": round(float(f1_score(e, p, average="weighted", zero_division=0)), 4),
            "feature_importance": [{"feature": names[i], "importance": round(float(imp[i]), 4)} for i in top]}
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_dir / FILE, compress=3)
    (model_dir / META).write_text(json.dumps(meta))
    return {"state": "trained", **meta}
