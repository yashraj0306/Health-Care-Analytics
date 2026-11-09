"""All REST endpoints (prefix /api)."""
import uuid
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

from services import (classification, clustering, entities, lifestyle, planning,
                      reduction, search, structured, wsd)
from services.data import LABEL, UNKNOWN
from services.errors import ApiError

bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------- helpers
def store():
    return current_app.extensions["store"]


def active():
    return store().active()


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError("Request body must be a JSON object.", 400, "invalid_json")
    return data


def text_field(data, key, min_len=1, max_len=50_000):
    v = data.get(key)
    if not isinstance(v, str) or not v.strip():
        raise ApiError(f"'{key}' is required and must be a non-empty string.", 400, "invalid_parameter")
    v = v.strip()
    if not min_len <= len(v) <= max_len:
        raise ApiError(f"'{key}' must be between {min_len} and {max_len} characters.", 400, "invalid_parameter")
    return v


def int_param(value, name, default, lo, hi):
    if value in (None, ""):
        return default
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise ApiError(f"'{name}' must be an integer.", 400, "invalid_parameter")
    if not lo <= v <= hi:
        raise ApiError(f"'{name}' must be between {lo} and {hi}.", 400, "invalid_parameter")
    return v


# ---------------------------------------------------------------- health / overview
@bp.get("/health")
def health():
    return jsonify(status="ok")


@bp.get("/overview")
def overview():
    ds = active()
    counts = ds.df[ds.df[LABEL] != UNKNOWN][LABEL].value_counts()
    model_ready = (ds.model_dir / classification.MODEL_FILE).exists()
    out = {
        "dataset": {"id": ds.id, "name": ds.name, "has_labels": ds.has_labels, **ds.stats},
        "n_specialties": int(len(counts)),
        "top_specialties": [{"specialty": k, "reports": int(v)} for k, v in counts.head(10).items()],
        "avg_words": round(float(ds.df["word_count"].mean()), 1),
        "model": {"trained": model_ready,
                  "metrics": classification.get_metrics(ds) if model_ready else None},
    }
    return jsonify(out)


# ---------------------------------------------------------------- datasets
@bp.get("/datasets")
def list_datasets():
    return jsonify(datasets=store().list_datasets())


@bp.post("/datasets/upload")
def upload():
    f = request.files.get("file")
    if f is None or not f.filename:
        raise ApiError("Attach a CSV file in the 'file' form field.", 400, "missing_file")
    if not f.filename.lower().endswith(".csv"):
        raise ApiError("Only .csv files are accepted.", 400, "invalid_file_type")
    cfg = current_app.config
    path = Path(cfg["UPLOAD_DIR"]) / f"{uuid.uuid4().hex}.csv"
    f.save(path)
    try:
        name = (request.form.get("name") or Path(f.filename).stem)[:80]
        ds_id = store().register(path, name)
        ds = store().get(ds_id)
        if len(ds.df) > cfg["MAX_ROWS"]:
            raise ApiError(f"Too many rows (max {cfg['MAX_ROWS']}).", 422, "too_many_rows")
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return jsonify(id=ds_id, name=name, rows=ds.stats["rows"], unique_notes=ds.stats["unique_notes"],
                   has_labels=ds.has_labels, message="Dataset uploaded and activated."), 201


@bp.post("/datasets/<dataset_id>/activate")
def activate(dataset_id):
    store().activate(dataset_id)
    return jsonify(message="Dataset activated.")


@bp.delete("/datasets/<dataset_id>")
def delete(dataset_id):
    store().delete(dataset_id)
    return jsonify(message="Dataset deleted.")


# ---------------------------------------------------------------- classification
@bp.post("/train")
def train():
    ds = active()
    return jsonify(classification.train(ds))


@bp.post("/predict")
def predict():
    ds = active()
    text = text_field(body(), "text", min_len=10)
    preds = classification.predict(ds, text)
    store().log_prediction(ds.id, text, preds[0]["specialty"], preds[0]["score"])
    return jsonify(predictions=preds, low_confidence=bool(preds[0]["score"] < 0),
                   note="'score' is the SVM margin; 'relative_confidence' is a softmax of margins, not a calibrated probability.")


@bp.get("/predictions/history")
def history():
    return jsonify(history=store().prediction_history(active().id))


@bp.get("/evaluation")
def evaluation():
    ds = active()
    m = classification.get_metrics(ds)
    return jsonify(classification=m, lifestyle_model=lifestyle.run(ds)["model"],
                   clustering=_cluster_eval(ds))


def _cluster_eval(ds):
    c = clustering.run(ds, 5)
    return {"k": 5, "silhouette": c["silhouette"], "adjusted_rand_vs_specialty": c["adjusted_rand_vs_specialty"]}


@bp.get("/feature-importance")
def feature_importance():
    return jsonify(classification.feature_importance(
        active(), request.args.get("specialty") or None, int_param(request.args.get("top_n"), "top_n", 15, 3, 50)))


@bp.get("/specialties")
def specialties():
    ds = active()
    ds.require_labels()
    return jsonify(specialties=sorted(classification.get_model(ds).classes_.tolist()))


# ---------------------------------------------------------------- planning / search
@bp.get("/planning")
def planning_ep():
    return jsonify(planning.indicators(active()))


@bp.post("/search")
def search_ep():
    d = body()
    q = text_field(d, "query", max_len=1000)
    return jsonify(search.search(active(), q, int_param(d.get("top_k"), "top_k", 10, 1, 25),
                                 d.get("specialty") or None))


@bp.get("/terms")
def terms():
    return jsonify(terms=search.top_terms(active(), int_param(request.args.get("n"), "n", 20, 5, 50)))


@bp.get("/context")
def context():
    term = (request.args.get("term") or "").strip()
    if len(term) < 2 or len(term) > 80:
        raise ApiError("'term' must be 2–80 characters.", 400, "invalid_parameter")
    return jsonify(search.term_context(active(), term, int_param(request.args.get("limit"), "limit", 10, 1, 30)))


# ---------------------------------------------------------------- clustering / reduction
@bp.get("/clusters")
def clusters():
    return jsonify(clustering.run(active(), int_param(request.args.get("k"), "k", 5, 2, 12)))


@bp.get("/reduction")
def reduction_ep():
    return jsonify(reduction.run(active(), (request.args.get("method") or "svd").lower()))


# ---------------------------------------------------------------- NLP
@bp.post("/entities")
def entities_ep():
    d = body()
    return jsonify(entities.extract(text_field(d, "text", max_len=100_000), bool(d.get("include_general"))))


@bp.get("/entities/summary")
def entities_summary():
    return jsonify(entities.summary(active(), int_param(request.args.get("n"), "n", 100, 1, 500)))


@bp.get("/wsd/senses")
def wsd_senses():
    return jsonify(terms=wsd.senses())


@bp.post("/wsd")
def wsd_ep():
    d = body()
    return jsonify(wsd.disambiguate(text_field(d, "sentence", max_len=2000), str(d.get("term") or "discharge")))


# ---------------------------------------------------------------- lifestyle
@bp.get("/lifestyle")
def lifestyle_ep():
    return jsonify(lifestyle.run(active()))


# ---------------------------------------------------------------- data requirements / structured
def _sdir():
    return Path(current_app.config["MODEL_DIR"]) / "structured"


@bp.get("/requirements")
def requirements():
    return jsonify(
        primary_dataset="MTSamples (free-text medical transcriptions)",
        supported_with_mtsamples=[
            "Specialty prediction", "Planning indicators", "Clinical text search", "K-Means clustering",
            "Entity extraction", "Word-sense disambiguation", "PCA / SVD", "Lifestyle keyword analysis",
            "Model evaluation"],
        requires_separate_data=[
            {"feature": "Structured obesity-category prediction (T15 feature importance on BMI/age/lifestyle)",
             "why": "MTSamples has no numeric BMI, age, height, weight or lifestyle columns. Weight keywords in free text "
                    "are not a substitute for measured values.",
             "needed": "A tabular CSV with a categorical obesity target, e.g. the public UCI 'Estimation of obesity levels' dataset.",
             "status": structured.status(_sdir()), "endpoint": "POST /api/structured/train"},
            {"feature": "Clinical-genomic analysis (genotype/variant ↔ phenotype models)",
             "why": "No genomic variants, expression or genotype data exist in MTSamples; nothing can be derived from the text.",
             "needed": "A de-identified clinical-genomic dataset (e.g. ClinVar/TCGA/UK Biobank-style extracts you are licensed to use).",
             "status": {"state": "not_implemented"},
             "endpoint": None},
        ])


@bp.get("/structured/status")
def structured_status():
    return jsonify(structured.status(_sdir()))


@bp.post("/structured/train")
def structured_train():
    f = request.files.get("file")
    target = (request.form.get("target") or "").strip()
    if f is None or not f.filename.lower().endswith(".csv"):
        raise ApiError("Attach a .csv in the 'file' field.", 400, "missing_file")
    if not target:
        raise ApiError("'target' (name of the label column) is required.", 400, "invalid_parameter")
    tmp = Path(current_app.config["UPLOAD_DIR"]) / f"structured_{uuid.uuid4().hex}.csv"
    f.save(tmp)
    try:
        return jsonify(structured.train(tmp, target, _sdir()))
    finally:
        tmp.unlink(missing_ok=True)
