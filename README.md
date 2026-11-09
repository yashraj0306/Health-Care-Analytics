# Healthcare Analytics — full-stack app built from your T7–T15 notebook

React + Vite + Tailwind frontend · Flask backend · scikit-learn · pandas · spaCy · SQLite.
Primary dataset: **MTSamples** (4,999 rows → 2,357 distinct transcriptions, 40 specialties).

## Run it (VS Code)

Open the `healthcare-analytics` folder in VS Code, open **two terminals** (Terminal → New Terminal, then the `+` / split icon).

**One-time setup — Windows (PowerShell/cmd)**
```bat
scripts\setup_windows.bat
```
**One-time setup — macOS/Linux**
```bash
bash scripts/setup_unix.sh
```
(or manually: `cd backend && python -m venv .venv`, activate it, `pip install -r requirements.txt`, `python -m spacy download en_core_web_sm`, then `cd ../frontend && npm install`.)

**Terminal 1 — backend (http://localhost:5000)**
```bash
cd backend
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
python app.py
```
**Terminal 2 — frontend (http://localhost:5173)**
```bash
cd frontend
npm run dev
```
Open **http://localhost:5173**. Needs Python 3.10+ and Node 18+.

**Single-server mode (optional):** `cd frontend && npm run build`, then `python backend/app.py` serves the built UI at http://localhost:5000.

**Tests:** `cd backend && python -m pytest -q` (19 tests).

In VS Code, select the interpreter in `backend/.venv` (Ctrl+Shift+P → *Python: Select Interpreter*).

The first call that needs the specialty model (Predict / Evaluation) trains it (~10–15 s) and saves it to `backend/models/<dataset-id>/`; later runs load it from disk. Click **Retrain model** to rebuild.

## What the notebook was doing wrong (and what changed)

| Notebook problem | Fix in this app |
|---|---|
| **T7 accuracy ≈ 9.9%** looked like a model bug. It is a *data* issue: 2,148 of 2,357 distinct transcriptions are listed under 2–5 different specialties, and a random row split puts the same text in train and test with conflicting labels (818 of 994 test rows). | Notes are de-duplicated (one record per text, keeping all listed specialties; primary label = least-frequent listed specialty). Evaluated on held-out unique notes: **75.6 % accuracy, 92.2 % top-3** (majority baseline 9.3 %). The original protocol is re-run live and shown beside it (9.8 %). |
| `y_pred` vs `pred` mix-ups (T10), `model_df` used before assignment | One consistent training/evaluation function (`services/classification.py`). |
| T11 summarised `entity_df` before it existed; `DISEASE` label never produced; PERSON/ORG noise; case-sensitive matching | Dictionary EntityRuler (case-insensitive, 5 categories), runs in a function. Falls back to a blank spaCy pipeline if `en_core_web_sm` isn't installed. |
| T15 looked for a `preprocessor` step and `feature_importances_` on TF-IDF + LinearSVC (neither exists) | Importance from LinearSVC coefficients (global and per specialty). A real `ColumnTransformer` + RandomForest importance is available for structured data (see Data Requirements). |
| Lifestyle "weight" classifier predicted a label defined by a regex on the same text (target leakage) | Trigger words are masked before training; documented as a *mention* classifier, not an obesity predictor. |
| Search returned the same duplicated note up to 5×; `input()` prompts; Colab paths (`/content`, `google.colab`) | Search over unique notes with all listed specialties; REST/JSON inputs; relative paths. |
| T12 WSD tie-handling | Explicit "Ambiguous" on ties/no cues; four terms (discharge, cold, positive, depression). Rule-based demo only. |

## Features → endpoints → pages

| Feature (notebook) | Page | Endpoint(s) |
|---|---|---|
| Datasets / upload | Datasets | `GET /api/datasets`, `POST /api/datasets/upload`, `POST /api/datasets/<id>/activate`, `DELETE /api/datasets/<id>` |
| Specialty prediction (T7) | Specialty Prediction | `POST /api/train`, `POST /api/predict`, `GET /api/predictions/history`, `GET /api/specialties` |
| Planning indicators (T8/T9) | Planning Indicators | `GET /api/planning` |
| Clinical text search (T9/T10/T12) | Clinical Text Search | `POST /api/search`, `GET /api/terms`, `GET /api/context?term=` |
| K-Means (T10) | K-Means Clusters | `GET /api/clusters?k=` |
| Entity extraction (T11) | Entity Extraction | `POST /api/entities`, `GET /api/entities/summary?n=` |
| Word-sense disambiguation (T12) | Word Senses | `GET /api/wsd/senses`, `POST /api/wsd` |
| PCA / SVD (T13) | PCA / SVD | `GET /api/reduction?method=pca\|svd` |
| Lifestyle (T14) | Lifestyle Analysis | `GET /api/lifestyle` |
| Evaluation + feature importance (T15) | Model Evaluation | `GET /api/evaluation`, `GET /api/feature-importance?specialty=` |
| Separate-data features | Data Requirements | `GET /api/requirements`, `GET /api/structured/status`, `POST /api/structured/train` |
| Dashboard | Dashboard | `GET /api/overview` |

Errors are JSON `{ "error": { "code", "message" } }` with proper status codes (400 invalid input, 404, 409 no dataset, 413 file too large, 422 bad dataset).

## Data honesty

* All metrics are computed from the loaded data at runtime; nothing is hard-coded.
* **Needs separate data (not fabricated):**
  * *Structured obesity-category model* (BMI, age, lifestyle columns → obesity level) — MTSamples has no such columns. Upload e.g. the UCI "Estimation of obesity levels" CSV on **Data Requirements**.
  * *Clinical-genomic analysis* — no genomic data exists in MTSamples; **not implemented**.
* Planning indicators are a report-volume proxy from a *sample of transcriptions*, not real hospital volumes. Not for staffing decisions.
* The specialty model, WSD rules and entity dictionary are educational and **not clinically validated**.
* MTSamples is a public collection of transcription samples; the bundled copy comes from a public GitHub mirror. Check the licence/terms you need before redistributing.

## Project layout
```
backend/  app.py  api.py  config.py  requirements.txt
          services/ (data, store, classification, search, planning, clustering,
                     reduction, entities, wsd, lifestyle, structured)
          tests/    data/mtsamples.csv   models/ (saved joblib files, created at runtime)
frontend/ package.json  vite.config.js  tailwind.config.js  src/{pages,components,api.js}
scripts/  setup_*.{bat,sh}  download_mtsamples.py
notebook_original.ipynb
```

## Testing status
Verified: 19 backend tests (synthetic fixtures only for code paths — never for reported metrics); every endpoint against the real MTSamples file; production build; all 12 pages loaded in headless Chromium with no console errors; mobile width has no horizontal scroll.
**Not verified:** Windows/macOS runs (tested on Linux, Python 3.13, Node 22); the structured-obesity trainer on a *real* obesity dataset (only a synthetic table in tests); uploads of very large (≥ 30 MB) CSVs; browsers other than Chromium; spaCy versions other than the one installed.
