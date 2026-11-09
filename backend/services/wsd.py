"""T12 – rule-based word-sense disambiguation (a transparent demo, not a trained model)."""
import re

from .errors import ApiError

INVENTORY = {
    "discharge": {
        "term": r"\bdischarg\w*",
        "senses": {
            "Hospital discharge (leaving care)": [
                r"\bdischarged? (home|to|from|in stable|today)", r"\bdischarge (summary|instructions|planning|medications?|diagnosis)",
                r"\bhospital discharge\b", r"\bpatient (was|is|will be) discharged\b", r"\bready for discharge\b"],
            "Bodily discharge (fluid)": [
                r"\b(vaginal|nasal|ear|urethral|penile|eye|ocular) discharge\b", r"\bfluid discharge\b",
                r"\bdischarge from the (ear|nose|eye)\b", r"\bpurulent discharge\b|\bmucoid discharge\b"],
            "Wound discharge (drainage)": [
                r"\bwound (discharge|drainage)\b", r"\bpus\b", r"\bdischarge from the (wound|incision|site)\b",
                r"\b(incision|surgical site) (discharge|drainage)\b"],
        },
    },
    "cold": {
        "term": r"\bcold\b",
        "senses": {
            "Common cold (viral illness)": [r"\bcold symptoms?\b", r"\brunny nose\b", r"\bcongestion\b",
                                            r"\bcough\b", r"\bupper respiratory\b", r"\bsore throat\b"],
            "Low temperature / cold extremities": [r"\bcold (to (the )?touch|extremit\w+|weather|pack|compress)\b",
                                                  r"\bcold intolerance\b", r"\bcold and clammy\b", r"\bice\b"],
        },
    },
    "positive": {
        "term": r"\bpositive\b",
        "senses": {
            "Abnormal / detected (test result)": [r"\bpositive for\b", r"\btested positive\b",
                                                  r"\bpositive (culture|result|test|biopsy|margins?)\b"],
            "Favourable / good (clinical course)": [r"\bpositive (outcome|response|prognosis|attitude)\b",
                                                    r"\bdoing well\b", r"\bimprov\w+\b"],
        },
    },
    "depression": {
        "term": r"\bdepression\b",
        "senses": {
            "Mood disorder": [r"\bmajor depression\b", r"\bantidepressant\w*\b", r"\bsuicid\w+\b",
                              r"\banxiety\b", r"\bmood\b", r"\bpsychiatr\w+\b"],
            "Anatomical depression (indentation)": [r"\b(skull|bone|tibial|sternal) depression\b", r"\bdepressed fracture\b",
                                                    r"\bdepression (of|in) the (skull|bone|cortex)\b", r"\bfracture\b"],
        },
    },
}


def senses():
    return [{"term": t, "senses": list(v["senses"])} for t, v in INVENTORY.items()]


def disambiguate(sentence, term="discharge"):
    term = term.lower()
    if term not in INVENTORY:
        raise ApiError(f"Unsupported term '{term}'. Supported: {', '.join(INVENTORY)}.", 400, "invalid_parameter")
    inv = INVENTORY[term]
    text = sentence.lower()
    term_present = bool(re.search(inv["term"], text))   # notebook examples omit the word itself, so only warn
    scores, evidence = {}, {}
    for sense, pats in inv["senses"].items():
        hits = [m.group(0) for p in pats for m in re.finditer(p, text)]
        scores[sense], evidence[sense] = len(hits), hits
    best = max(scores.values())
    winners = [s for s, v in scores.items() if v == best]
    if best == 0:
        result, reason = "Ambiguous / insufficient context", "No context cue matched any sense."
    elif len(winners) > 1:
        result, reason = "Ambiguous / insufficient context", "Two or more senses scored equally."
    else:
        result, reason = winners[0], "Highest number of matching context cues."
    return {"term": term, "term_in_sentence": term_present, "sentence": sentence, "interpretation": result, "reason": reason,
            "scores": scores, "evidence": evidence,
            "disclaimer": "Rule-based cue matching on a small hand-written inventory; not clinically validated."}
