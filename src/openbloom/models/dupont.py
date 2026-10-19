"""DuPont decomposition: ROE = net margin x asset turnover x equity multiplier.

Uses year-end balances so the identity matches the stored ROE exactly:
(NI / Revenue) x (Revenue / Assets) x (Assets / Equity) = NI / Equity.
Not meaningful when revenue, assets or equity is missing or <= 0.
"""
import math

import pandas as pd

INPUTS = ["net_income", "revenue", "total_assets", "equity"]


def _gap_days(a: str, b: str) -> int:
    return (pd.to_datetime(b) - pd.to_datetime(a)).days


def dupont(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("period_end").reset_index(drop=True)
    out = pd.DataFrame({"period_end": df["period_end"].to_numpy()})
    for c in INPUTS:
        out[c] = pd.to_numeric(df[c], errors="coerce").to_numpy()

    nm, at, em, roe, notes = [], [], [], [], []
    for ni, rev, ta, eq in out[INPUTS].itertuples(index=False):
        missing = [n for n, v in zip(INPUTS, (ni, rev, ta, eq)) if pd.isna(v)]
        if missing:
            note = "missing " + ", ".join(missing)
        elif rev <= 0:
            note = "revenue <= 0"
        elif ta <= 0:
            note = "total assets <= 0"
        elif eq <= 0:
            note = "equity <= 0: ROE not meaningful"
        else:
            note = ""
        if note:
            nm.append(math.nan); at.append(math.nan); em.append(math.nan); roe.append(math.nan)
        else:
            m, a, l = ni / rev, rev / ta, ta / eq
            nm.append(m * 100); at.append(a); em.append(l); roe.append(m * a * l * 100)
        notes.append(note)

    out["net_margin_pct"] = nm
    out["asset_turnover"] = at
    out["equity_multiplier"] = em
    out["roe_pct"] = roe
    out["note"] = notes

    # Year-over-year attribution in log-% (additive): ROE change = margin + turnover + leverage.
    # Only when both years are valid, net income > 0 in both, and years are ~1 year apart.
    for c in ("chg_roe", "chg_margin", "chg_turnover", "chg_leverage"):
        out[c] = math.nan
    for i in range(1, len(out)):
        p, q = out.iloc[i - 1], out.iloc[i]
        if pd.isna(p["roe_pct"]) or pd.isna(q["roe_pct"]):
            continue
        if p["net_income"] <= 0 or q["net_income"] <= 0:
            continue
        if not 350 <= _gap_days(p["period_end"], q["period_end"]) <= 380:
            continue
        out.loc[i, "chg_margin"] = 100 * math.log(q["net_margin_pct"] / p["net_margin_pct"])
        out.loc[i, "chg_turnover"] = 100 * math.log(q["asset_turnover"] / p["asset_turnover"])
        out.loc[i, "chg_leverage"] = 100 * math.log(q["equity_multiplier"] / p["equity_multiplier"])
        out.loc[i, "chg_roe"] = 100 * math.log(q["roe_pct"] / p["roe_pct"])
    return out