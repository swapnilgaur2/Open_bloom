"""Cash conversion and accruals.

cash_conversion = operating cash flow / net income  (only when net income > 0)
conv_3y         = sum of 3 years of OCF / sum of 3 years of net income (smooths timing noise)
accruals_pct    = (net income - OCF) / average total assets x 100  (Sloan accrual ratio)
Higher accruals = more of the profit is not backed by cash.
"""
import math

import pandas as pd


def _gap_ok(a: str, b: str) -> bool:
    return 350 <= (pd.to_datetime(b) - pd.to_datetime(a)).days <= 380


def cash_conversion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("period_end").reset_index(drop=True)
    out = pd.DataFrame({"period_end": df["period_end"].to_numpy()})
    for c in ("net_income", "operating_cash_flow", "total_assets"):
        out[c] = pd.to_numeric(df[c], errors="coerce").to_numpy()

    n = len(out)
    conv, acc, conv3, notes = [math.nan] * n, [math.nan] * n, [math.nan] * n, [""] * n
    ni, ocf, ta, pe = out["net_income"], out["operating_cash_flow"], out["total_assets"], out["period_end"]

    for i in range(n):
        missing = [name for name, v in (("net_income", ni[i]), ("operating_cash_flow", ocf[i])) if pd.isna(v)]
        if missing:
            notes[i] = "missing " + ", ".join(missing)
            continue
        if ni[i] <= 0:
            notes[i] = "net income <= 0: ratio not meaningful"
        else:
            conv[i] = ocf[i] / ni[i]

        if i >= 1 and _gap_ok(pe[i - 1], pe[i]) and pd.notna(ta[i]) and pd.notna(ta[i - 1]):
            avg = (ta[i] + ta[i - 1]) / 2
            if avg > 0:
                acc[i] = (ni[i] - ocf[i]) / avg * 100

        if i >= 2 and _gap_ok(pe[i - 2], pe[i - 1]) and _gap_ok(pe[i - 1], pe[i]):
            w_ni, w_ocf = ni[i - 2:i + 1], ocf[i - 2:i + 1]
            if not w_ni.isna().any() and not w_ocf.isna().any() and w_ni.sum() > 0:
                conv3[i] = w_ocf.sum() / w_ni.sum()

    out["cash_conversion"] = conv
    out["conv_3y"] = conv3
    out["accruals_pct"] = acc
    out["note"] = notes
    return out