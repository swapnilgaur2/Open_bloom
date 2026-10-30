"""Find reported values that changed between filings.

Input: one row per (company, metric, tag, period, filing). Only the tag the app actually uses for a
metric should be included. A later 10-K repeating the same number is NOT a change.
A change can be a correction, but is often a reclassification or a discontinued-operations recast.
"""
import math

import pandas as pd

KEYS = ["cik", "metric", "tag", "period_start", "period_end"]
OUT_COLS = [
    "ticker", "cik", "metric", "period_end",
    "original_value", "original_filed", "original_accession",
    "latest_value", "latest_filed", "latest_accession",
    "change_pct", "versions",
]


def find_restatements(facts: pd.DataFrame) -> pd.DataFrame:
    if facts.empty:
        return pd.DataFrame(columns=OUT_COLS)
    f = facts.copy()
    f["value"] = pd.to_numeric(f["value"], errors="coerce")
    f = f.dropna(subset=["value"])
    f["period_start"] = f["period_start"].fillna("")
    f = f[f.groupby(KEYS)["value"].transform("nunique") > 1]

    rows = []
    for _, g in f.sort_values(["filed_date", "accession"]).groupby(KEYS, sort=False):
        first, last = g.iloc[0], g.iloc[-1]
        change = (last["value"] - first["value"]) / abs(first["value"]) * 100 if first["value"] != 0 else math.nan
        rows.append(
            {
                "ticker": first["ticker"], "cik": first["cik"], "metric": first["metric"],
                "period_end": first["period_end"],
                "original_value": first["value"], "original_filed": first["filed_date"],
                "original_accession": first["accession"],
                "latest_value": last["value"], "latest_filed": last["filed_date"],
                "latest_accession": last["accession"],
                "change_pct": change, "versions": int(g["value"].nunique()),
            }
        )
    return pd.DataFrame(rows, columns=OUT_COLS)