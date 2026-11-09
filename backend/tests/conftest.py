import io
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402

# Small SYNTHETIC corpus used ONLY to exercise the code paths in tests.
# It is never used by the application and no reported metric comes from it.
TOPICS = {
    "Cardiology": "chest pain hypertension echocardiogram ventricular ejection fraction coronary artery stent",
    "Orthopedic": "knee arthroplasty femoral tibial fracture cast orthopedic fixation screw ligament",
    "Neurology": "headache seizure mri brain cranial nerve migraine neurologic weakness stroke",
    "Dermatology": "rash skin lesion biopsy melanoma eczema topical steroid cream dermatitis",
}


def make_csv(n_per=14, with_label=True, dup=True):
    rows = []
    for spec, words in TOPICS.items():
        w = words.split()
        for i in range(n_per):
            text = f"Patient seen for {w[i % 5]} and {w[(i + 2) % 8]}. Plan: {w[(i + 3) % 8]} follow up case {i} {spec[:3]}. " \
                   f"Weight was recorded and exercise advised. Discharge home in stable condition."
            rows.append((spec, text, f"{spec} sample {i}"))
    if dup:
        rows.append(("Surgery", rows[0][1], "dup"))   # same text cross-listed under another specialty
    head = "medical_specialty,transcription,sample_name\n" if with_label else "transcription,sample_name\n"
    out = io.StringIO(head)
    out.seek(0, 2)
    for spec, text, name in rows:
        out.write((f'"{spec}",' if with_label else "") + f'"{text}","{name}"\n')
    return out.getvalue()


@pytest.fixture()
def app(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "mtsamples.csv").write_text(make_csv())
    return create_app({"TESTING": True, "DATA_DIR": tmp_path / "data", "UPLOAD_DIR": tmp_path / "up",
                       "MODEL_DIR": tmp_path / "models", "DB_PATH": tmp_path / "t.db"})


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def empty_client(tmp_path):
    a = create_app({"TESTING": True, "DATA_DIR": tmp_path / "d", "UPLOAD_DIR": tmp_path / "up",
                    "MODEL_DIR": tmp_path / "models", "DB_PATH": tmp_path / "e.db"})
    return a.test_client()
