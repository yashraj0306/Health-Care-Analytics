import io

import joblib

from tests.conftest import make_csv


def test_health(client):
    assert client.get("/api/health").json == {"status": "ok"}


def test_no_dataset_gives_409(empty_client):
    r = empty_client.get("/api/overview")
    assert r.status_code == 409 and r.json["error"]["code"] == "no_active_dataset"


def test_overview_and_dedup(client):
    j = client.get("/api/overview").json
    assert j["dataset"]["rows"] == 57 and j["dataset"]["unique_notes"] == 56
    assert j["n_specialties"] == 5


def test_train_saves_and_reloads_model(client, app):
    m = client.post("/api/train").json
    assert 0 <= m["accuracy"] <= 1 and m["n_classes"] >= 2
    files = list((app.config["MODEL_DIR"]).glob("*/specialty_model.joblib"))
    assert files, "model artefact was not saved"
    assert joblib.load(files[0]).predict(["knee arthroplasty fracture"]).shape == (1,)
    # a fresh app instance must load from disk, not retrain
    from app import create_app
    app2 = create_app({"TESTING": True, "DATA_DIR": app.config["DATA_DIR"], "UPLOAD_DIR": app.config["UPLOAD_DIR"],
                       "MODEL_DIR": app.config["MODEL_DIR"], "DB_PATH": app.config["DB_PATH"]})
    c2 = app2.test_client()
    assert c2.get("/api/evaluation").json["classification"]["trained_at"] == m["trained_at"]


def test_predict_validation_and_result(client):
    assert client.post("/api/predict", json={}).status_code == 400
    assert client.post("/api/predict", json={"text": "short"}).status_code == 400
    assert client.post("/api/predict", data="not json", content_type="text/plain").status_code == 400
    r = client.post("/api/predict", json={"text": "knee arthroplasty with femoral and tibial components fracture"})
    assert r.status_code == 200
    assert r.json["predictions"][0]["specialty"] == "Orthopedic"
    assert client.get("/api/predictions/history").json["history"]


def test_planning(client):
    j = client.get("/api/planning").json
    assert j["n_reports"] == 57
    assert sum(s["report_count"] for s in j["specialties"]) == 57


def test_search(client):
    r = client.post("/api/search", json={"query": "melanoma skin lesion"}).json
    assert r["results"] and r["results"][0]["specialty"] == "Dermatology"
    assert client.post("/api/search", json={"query": ""}).status_code == 400
    assert client.post("/api/search", json={"query": "zzzzqq"}).json["results"] == []


def test_context(client):
    j = client.get("/api/context?term=exercise").json
    assert j["total_notes"] > 0
    assert client.get("/api/context?term=x").status_code == 400


def test_clusters_and_validation(client):
    j = client.get("/api/clusters?k=3").json
    assert len(j["clusters"]) == 3 and -1 <= j["silhouette"] <= 1
    assert client.get("/api/clusters?k=1").status_code == 400
    assert client.get("/api/clusters?k=abc").status_code == 400


def test_reduction(client):
    p = client.get("/api/reduction?method=pca").json
    assert 0 < p["total_explained_variance"] <= 1 and len(p["points"]) == 56
    assert client.get("/api/reduction?method=svd").status_code == 200
    assert client.get("/api/reduction?method=tsne").status_code == 400


def test_entities(client):
    j = client.post("/api/entities", json={"text": "Patient with Diabetes on Metformin had chest pain. MRI ordered."}).json
    got = {(e["entity"], e["type"]) for e in j["entities"]}
    assert {("diabetes", "CONDITION"), ("metformin", "MEDICATION"), ("chest pain", "SYMPTOM"), ("mri", "PROCEDURE")} <= got
    assert client.get("/api/entities/summary?n=10").status_code == 200
    assert client.get("/api/entities/summary?n=0").status_code == 400


def test_wsd(client):
    f = lambda s: client.post("/api/wsd", json={"sentence": s}).json["interpretation"]
    assert f("The patient was discharged home in stable condition.").startswith("Hospital")
    assert f("The patient reports vaginal discharge.").startswith("Bodily")
    assert f("The wound has pus and wound drainage.").startswith("Wound")
    assert f("Discharge noted.") == "Ambiguous / insufficient context"
    assert client.post("/api/wsd", json={"sentence": "x", "term": "nope"}).status_code == 400


def test_lifestyle_and_evaluation(client):
    j = client.get("/api/lifestyle").json
    assert {c["topic"] for c in j["counts"]} >= {"Smoking", "Sleep"}
    e = client.get("/api/evaluation").json
    assert "classification" in e and "lifestyle_model" in e


def test_feature_importance(client):
    g = client.get("/api/feature-importance").json
    assert g["global"]
    s = client.get("/api/feature-importance?specialty=Dermatology").json
    assert s["positive"]
    assert client.get("/api/feature-importance?specialty=Nope").status_code == 404


def test_upload_validation(client):
    assert client.post("/api/datasets/upload").status_code == 400
    r = client.post("/api/datasets/upload", data={"file": (io.BytesIO(b"a,b\n1,2\n"), "x.txt")})
    assert r.status_code == 400
    r = client.post("/api/datasets/upload", data={"file": (io.BytesIO(b"a,b\n1,2\n"), "x.csv")})
    assert r.status_code == 422 and r.json["error"]["code"] == "invalid_dataset"
    r = client.post("/api/datasets/upload", data={"file": (io.BytesIO(make_csv(n_per=10).encode()), "mine.csv")})
    assert r.status_code == 201
    names = [d["name"] for d in client.get("/api/datasets").json["datasets"]]
    assert "mine" in names
    assert client.get("/api/overview").json["dataset"]["name"] == "mine"


def test_unlabelled_upload_blocks_classification(client):
    csv = make_csv(with_label=False).encode()
    assert client.post("/api/datasets/upload", data={"file": (io.BytesIO(csv), "u.csv")}).status_code == 201
    assert client.post("/api/predict", json={"text": "knee arthroplasty fracture"}).status_code == 422
    assert client.post("/api/search", json={"query": "melanoma"}).status_code == 200   # label-free features still work


def test_builtin_cannot_be_deleted_and_unknown_404(client):
    ds = client.get("/api/datasets").json["datasets"][0]
    assert client.delete(f"/api/datasets/{ds['id']}").status_code == 400
    assert client.post("/api/datasets/zzz/activate").status_code == 404
    assert client.get("/api/nope").status_code == 404


def test_requirements_never_fabricates(client):
    j = client.get("/api/requirements").json
    assert j["requires_separate_data"][0]["status"]["state"] == "requires_dataset"
    assert j["requires_separate_data"][1]["status"]["state"] == "not_implemented"


def test_structured_training_with_synthetic_table(client):
    import numpy as np
    rng = np.random.RandomState(0)
    lines = ["age,bmi,gender,level"]
    for _ in range(200):
        bmi = rng.uniform(16, 42)
        lines.append(f"{rng.randint(18, 70)},{bmi:.1f},{rng.choice(['M', 'F'])},{'obese' if bmi > 30 else 'normal'}")
    r = client.post("/api/structured/train", data={"target": "level", "file": (io.BytesIO("\n".join(lines).encode()), "s.csv")})
    assert r.status_code == 200 and r.json["feature_importance"][0]["feature"].endswith("bmi")
    assert client.get("/api/requirements").json["requires_separate_data"][0]["status"]["state"] == "trained"
    assert client.post("/api/structured/train", data={"target": "zzz", "file": (io.BytesIO(b"a,b\n" + b"1,2\n" * 60), "s.csv")}).status_code == 422
