"""SQLite-backed dataset registry + in-memory analysis cache."""
import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .data import (LABEL, TEXT, clean_frame, dedup_stats, quality_report,
                   read_csv_flexible, unique_notes)
from .errors import ApiError, DataError, NeedsLabelsError, NoDatasetError


@dataclass
class LoadedDataset:
    id: str
    name: str
    df: pd.DataFrame
    notes: pd.DataFrame
    has_labels: bool
    quality: list
    stats: dict
    model_dir: Path
    cache: dict = field(default_factory=dict)

    def require_labels(self):
        counts = self.notes[self.notes[LABEL] != "Unknown"][LABEL].value_counts()
        if not self.has_labels or (counts >= 5).sum() < 2:
            raise NeedsLabelsError()


class DatasetStore:
    def __init__(self, db_path, upload_dir, model_dir, data_dir):
        self.db_path, self.upload_dir = Path(db_path), Path(upload_dir)
        self.model_dir, self.data_dir = Path(model_dir), Path(data_dir)
        for p in (self.upload_dir, self.model_dir, self.data_dir, self.db_path.parent):
            p.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self._loaded = {}
        self._init_db()

    # ---- sqlite -------------------------------------------------------
    def _conn(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        return c

    def _init_db(self):
        with self._conn() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS datasets(
                    id TEXT PRIMARY KEY, name TEXT, path TEXT, builtin INTEGER DEFAULT 0,
                    rows INTEGER, unique_notes INTEGER, has_labels INTEGER,
                    columns TEXT, created_at TEXT, is_active INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS predictions(
                    id INTEGER PRIMARY KEY AUTOINCREMENT, dataset_id TEXT,
                    preview TEXT, top_label TEXT, top_score REAL, created_at TEXT);
                """
            )

    def list_datasets(self):
        with self._conn() as c:
            rows = c.execute("SELECT * FROM datasets ORDER BY created_at DESC").fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["columns"] = json.loads(d["columns"] or "[]")
            d["is_active"] = bool(d["is_active"])
            d["builtin"] = bool(d["builtin"])
            d["has_labels"] = bool(d["has_labels"])
            d["model_trained"] = (self.model_dir / d["id"] / "specialty_model.joblib").exists()
            out.append(d)
        return out

    def _row(self, dataset_id):
        with self._conn() as c:
            return c.execute("SELECT * FROM datasets WHERE id=?", (dataset_id,)).fetchone()

    # ---- registration ---------------------------------------------------
    def register(self, path, name, builtin=False, activate=True):
        raw = read_csv_flexible(path)
        df, has_labels = clean_frame(raw)
        if len(df) < 20:
            raise DataError("The file needs at least 20 non-empty transcriptions.")
        notes = unique_notes(df)
        ds_id = uuid.uuid4().hex[:10]
        with self.lock, self._conn() as c:
            c.execute(
                "INSERT INTO datasets(id,name,path,builtin,rows,unique_notes,has_labels,columns,created_at) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (ds_id, name, str(path), int(builtin), len(df), len(notes), int(has_labels),
                 json.dumps(list(df.columns)), datetime.now(timezone.utc).isoformat(timespec="seconds")),
            )
        if activate:
            self.activate(ds_id)
        return ds_id

    def ensure_default(self, filename):
        path = self.data_dir / filename
        if not path.exists():
            return None
        with self._conn() as c:
            row = c.execute("SELECT id FROM datasets WHERE builtin=1 AND path=?", (str(path),)).fetchone()
            any_active = c.execute("SELECT 1 FROM datasets WHERE is_active=1").fetchone()
        if row:
            if not any_active:
                self.activate(row["id"])
            return row["id"]
        return self.register(path, "MTSamples (primary)", builtin=True, activate=not any_active)

    def activate(self, dataset_id):
        if not self._row(dataset_id):
            raise ApiError("Dataset not found.", 404, "not_found")
        with self.lock, self._conn() as c:
            c.execute("UPDATE datasets SET is_active=0")
            c.execute("UPDATE datasets SET is_active=1 WHERE id=?", (dataset_id,))

    def delete(self, dataset_id):
        row = self._row(dataset_id)
        if not row:
            raise ApiError("Dataset not found.", 404, "not_found")
        if row["builtin"]:
            raise ApiError("The primary MTSamples dataset cannot be deleted.", 400, "protected")
        with self.lock, self._conn() as c:
            c.execute("DELETE FROM datasets WHERE id=?", (dataset_id,))
        self._loaded.pop(dataset_id, None)
        Path(row["path"]).unlink(missing_ok=True)
        import shutil
        shutil.rmtree(self.model_dir / dataset_id, ignore_errors=True)
        with self._conn() as c:
            if not c.execute("SELECT 1 FROM datasets WHERE is_active=1").fetchone():
                first = c.execute("SELECT id FROM datasets ORDER BY builtin DESC LIMIT 1").fetchone()
                if first:
                    c.execute("UPDATE datasets SET is_active=1 WHERE id=?", (first["id"],))

    # ---- loading --------------------------------------------------------
    def get(self, dataset_id):
        with self.lock:
            if dataset_id in self._loaded:
                return self._loaded[dataset_id]
            row = self._row(dataset_id)
            if not row:
                raise ApiError("Dataset not found.", 404, "not_found")
            raw = read_csv_flexible(row["path"])
            df, has_labels = clean_frame(raw)
            notes = unique_notes(df)
            ds = LoadedDataset(
                id=dataset_id, name=row["name"], df=df, notes=notes, has_labels=has_labels,
                quality=quality_report(raw), stats=dedup_stats(df, notes),
                model_dir=self.model_dir / dataset_id,
            )
            if len(self._loaded) >= 3:                       # keep memory bounded
                self._loaded.pop(next(iter(self._loaded)))
            self._loaded[dataset_id] = ds
            return ds

    def active(self):
        with self._conn() as c:
            row = c.execute("SELECT id FROM datasets WHERE is_active=1").fetchone()
        if not row:
            raise NoDatasetError()
        return self.get(row["id"])

    # ---- prediction history ---------------------------------------------
    def log_prediction(self, dataset_id, text, label, score):
        with self._conn() as c:
            c.execute(
                "INSERT INTO predictions(dataset_id,preview,top_label,top_score,created_at) VALUES(?,?,?,?,?)",
                (dataset_id, text[:140], label, float(score),
                 datetime.now(timezone.utc).isoformat(timespec="seconds")),
            )

    def prediction_history(self, dataset_id, limit=20):
        with self._conn() as c:
            rows = c.execute(
                "SELECT preview,top_label,top_score,created_at FROM predictions "
                "WHERE dataset_id=? ORDER BY id DESC LIMIT ?", (dataset_id, limit)).fetchall()
        return [dict(r) for r in rows]


def cached(ds, key, fn):
    """Compute-once cache stored on the dataset object."""
    if key not in ds.cache:
        ds.cache[key] = fn()
    return ds.cache[key]
