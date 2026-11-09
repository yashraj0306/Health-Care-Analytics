"""Dataset loading, cleaning and de-duplication.

Key finding from the notebook analysis: in MTSamples the *same transcription* is
often listed under several specialties (2,148 of 2,357 unique texts in the public
copy). If rows are split at random, the same text lands in both train and test
with a conflicting label, which is why the original T7 accuracy was only ~9.9%.
`unique_notes` collapses each distinct text into one record that keeps *all* the
specialties it was listed under, plus one "primary" label (the least frequent
specialty, i.e. the most specific one).
"""
import pandas as pd

from .errors import DataError

TEXT = "transcription"
LABEL = "medical_specialty"
UNKNOWN = "Unknown"


def read_csv_flexible(path):
    last = None
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError as exc:
            last = exc
        except (pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
            raise DataError(f"Could not parse the CSV file: {exc}") from exc
    raise DataError(f"Could not decode the CSV file: {last}")


def normalise_columns(df):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df.loc[:, [c for c in df.columns if not c.startswith("unnamed")]]


def quality_report(raw):
    """Missing/unique stats on the *raw* (pre-clean) frame — notebook cell 9."""
    raw = normalise_columns(raw)
    return [
        {
            "column": c,
            "missing": int(raw[c].isna().sum()),
            "missing_pct": round(float(raw[c].isna().mean() * 100), 2),
            "unique": int(raw[c].nunique()),
        }
        for c in raw.columns
    ]


def clean_frame(raw):
    """Return (clean_df, has_labels). Raises DataError when unusable."""
    df = normalise_columns(raw)
    if TEXT not in df.columns:
        raise DataError(
            f"Missing required column '{TEXT}'.",
            {"columns_found": df.columns.tolist(), "required": [TEXT], "optional": [LABEL]},
        )
    df[TEXT] = (
        df[TEXT].fillna("").astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    )
    df = df[df[TEXT] != ""].copy()
    has_labels = LABEL in df.columns
    if has_labels:
        df[LABEL] = df[LABEL].fillna("").astype(str).str.strip()
        df.loc[df[LABEL].isin(["", "nan", "None"]), LABEL] = UNKNOWN
        has_labels = (df[LABEL] != UNKNOWN).any()
    else:
        df[LABEL] = UNKNOWN
    df["word_count"] = df[TEXT].str.split().str.len()
    return df.reset_index(drop=True), bool(has_labels)


def unique_notes(df):
    """One row per distinct transcription (see module docstring)."""
    freq = df[LABEL].value_counts()
    d = df.assign(_freq=df[LABEL].map(freq), _order=range(len(df)))
    d = d.sort_values(["_freq", LABEL, "_order"], kind="stable")
    grouped = d.groupby(TEXT, sort=False)
    first = grouped.head(1).copy()
    specs = grouped[LABEL].agg(lambda s: sorted(set(s)))
    first["all_specialties"] = first[TEXT].map(specs)
    first = first.sort_values("_order").drop(columns=["_freq", "_order"])
    first["word_count"] = first[TEXT].str.split().str.len()
    return first.reset_index(drop=True)


def dedup_stats(df, notes):
    multi = int((notes["all_specialties"].str.len() > 1).sum())
    return {
        "rows": int(len(df)),
        "unique_notes": int(len(notes)),
        "duplicate_rows": int(len(df) - len(notes)),
        "notes_listed_under_multiple_specialties": multi,
        "multi_listed_pct": round(multi / max(len(notes), 1) * 100, 1),
    }
