"""T8/T9 – healthcare planning indicators from report volume."""
from .data import LABEL, TEXT, UNKNOWN


def indicators(ds):
    df = ds.df
    g = df.groupby(LABEL).agg(report_count=(TEXT, "size"), average_words=("word_count", "mean"),
                              unique_reports=(TEXT, "nunique")).reset_index()
    g["share_percent"] = (g["report_count"] / len(df) * 100).round(2)
    g["average_words"] = g["average_words"].round(1)
    # Transparent workload proxy (notebook T9) — NOT a validated staffing requirement.
    g["review_priority_score"] = (g["share_percent"].rank(pct=True) * 100).round(1)
    g = g.sort_values("report_count", ascending=False).reset_index(drop=True)
    top5 = g.head(5)["report_count"].sum() / len(df) * 100
    return {
        "n_reports": int(len(df)), "n_specialties": int((g[LABEL] != UNKNOWN).sum()),
        "top5_share_percent": round(float(top5), 2),
        "specialties": g.rename(columns={LABEL: "specialty"}).to_dict("records"),
        "quality": ds.quality,
        "caveats": [
            "Counts are listing counts: a note cross-listed under several specialties is counted once per listing "
            "(compare report_count with unique_reports).",
            "review_priority_score is the percentile rank of a specialty's report share — a workload proxy, "
            "not a validated resource requirement.",
            "MTSamples is a sample of transcription examples, not real hospital volumes; do not use for actual staffing.",
        ],
    }
