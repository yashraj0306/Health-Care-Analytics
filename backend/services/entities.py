"""T11 – dictionary-driven medical entity extraction with spaCy's EntityRuler.

Fixes vs. the notebook: the original cell summarised `entity_df` before it was
created (execution-order error); it kept spaCy PERSON/ORG hits (noise for medical
text) and filtered on a "DISEASE" label that en_core_web_sm never produces; and
matching was case-sensitive. Here patterns match case-insensitively and carry a
category label. If the `en_core_web_sm` model is missing, a blank English
pipeline + the same ruler is used (the dictionary logic is identical).
"""
import threading

import pandas as pd

from .data import TEXT
from .errors import ApiError
from .store import cached

LEXICON = {
    "CONDITION": ["diabetes", "hypertension", "pneumonia", "asthma", "obesity", "infection", "cancer",
                  "heart disease", "coronary artery disease", "congestive heart failure", "atrial fibrillation",
                  "hyperlipidemia", "anemia", "arthritis", "osteoarthritis", "stroke", "copd", "renal failure",
                  "hypothyroidism", "depression", "anxiety", "sepsis", "carpal tunnel syndrome", "migraine",
                  "bronchitis", "cellulitis", "gerd", "hernia", "fracture", "tumor"],
    "SYMPTOM": ["chest pain", "headache", "fever", "shortness of breath", "nausea", "vomiting", "dizziness",
                "cough", "fatigue", "abdominal pain", "back pain", "swelling", "diarrhea", "weakness", "rash"],
    "MEDICATION": ["insulin", "aspirin", "metformin", "lisinopril", "atorvastatin", "ibuprofen", "acetaminophen",
                   "warfarin", "amoxicillin", "prednisone", "morphine", "heparin", "lasix", "synthroid", "tylenol",
                   "vicodin", "percocet", "ancef", "zocor", "coumadin"],
    "PROCEDURE": ["biopsy", "mri", "magnetic resonance imaging", "ct scan", "x-ray", "ultrasound",
                  "colonoscopy", "endoscopy", "echocardiogram", "catheterization", "appendectomy",
                  "cholecystectomy", "laparoscopy", "intubation", "ekg", "arthroscopy"],
    "MEASUREMENT": ["blood pressure", "heart rate", "temperature", "oxygen saturation", "respiratory rate",
                    "body mass index", "bmi", "blood glucose"],
}

_nlp = None
_lock = threading.Lock()


def get_nlp():
    global _nlp
    with _lock:
        if _nlp is not None:
            return _nlp
        import spacy
        try:
            nlp, model = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"]), "en_core_web_sm"
            before = {"before": "ner"}
        except OSError:
            nlp, model, before = spacy.blank("en"), "blank (en_core_web_sm not installed)", {}
        ruler = nlp.add_pipe("entity_ruler", config={"phrase_matcher_attr": "LOWER", "overwrite_ents": True}, **before)
        ruler.add_patterns([{"label": lab, "pattern": t} for lab, terms in LEXICON.items() for t in terms])
        nlp.meta["_ha_model"] = model
        _nlp = nlp
        return nlp


def _extract(doc, include_general):
    lab = set(LEXICON)
    out = []
    for e in doc.ents:
        if e.label_ in lab:
            out.append({"entity": e.text.lower(), "type": e.label_, "start": e.start_char, "end": e.end_char,
                        "source": "dictionary"})
        elif include_general and e.label_ in {"PERSON", "ORG", "GPE", "DATE"}:
            out.append({"entity": e.text, "type": e.label_, "start": e.start_char, "end": e.end_char,
                        "source": "spacy_ner"})
    return out


def extract(text, include_general=False):
    nlp = get_nlp()
    return {"model": nlp.meta["_ha_model"], "entities": _extract(nlp(text[:100_000]), include_general)}


def summary(ds, n=100):
    if not 1 <= n <= 500:
        raise ApiError("n must be between 1 and 500.", 400, "invalid_parameter")
    return cached(ds, ("entities", n), lambda: _summary(ds, n))


def _summary(ds, n):
    nlp = get_nlp()
    texts = ds.notes[TEXT].head(n).str.slice(0, 10_000).tolist()
    rows = []
    for i, doc in enumerate(nlp.pipe(texts, batch_size=20)):
        rows += [{"note": i, **e} for e in _extract(doc, False)]
    if not rows:
        return {"model": nlp.meta["_ha_model"], "notes_processed": len(texts), "total_mentions": 0,
                "by_type": [], "top_entities": [], "sample": [],
                "message": "No entities found. Extend the dictionary in services/entities.py."}
    df = pd.DataFrame(rows)
    top = df.groupby(["entity", "type"]).size().reset_index(name="frequency").sort_values("frequency", ascending=False)
    return {"model": nlp.meta["_ha_model"], "notes_processed": len(texts), "total_mentions": int(len(df)),
            "notes_with_entities": int(df["note"].nunique()),
            "by_type": df["type"].value_counts().rename_axis("type").reset_index(name="mentions").to_dict("records"),
            "top_entities": top.head(30).to_dict("records"),
            "sample": df.head(30)[["note", "entity", "type"]].to_dict("records")}
