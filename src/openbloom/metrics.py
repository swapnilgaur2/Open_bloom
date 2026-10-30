import pandas as pd

from src.openbloom.db import get_connection

METRICS = [
    "revenue", "gross_profit", "operating_income", "net_income",
    "operating_cash_flow", "capex", "total_assets", "total_liabilities",
    "equity", "cash",
]


def _missing(x) -> bool:
    return x is None or pd.isna(x)


def safe_divide(numerator, denominator):
    """numerator / denominator, or None if either is missing or denominator is 0."""
    if _missing(numerator) or _missing(denominator) or denominator == 0:
        return None
    return numerator / denominator


def growth_pct(current, previous):
    """Percent change vs previous period. None if previous is missing, zero or negative
    (growth from a negative base is misleading)."""
    if _missing(current) or _missing(previous) or previous <= 0:
        return None
    return (current - previous) / previous * 100


def margin_pct(numerator, revenue):
    """numerator / revenue * 100. None if revenue is missing or not positive."""
    if _missing(numerator) or _missing(revenue) or revenue <= 0:
        return None
    return numerator / revenue * 100


def ratio_pct(numerator, denominator):
    """numerator / denominator * 100, None if denominator is missing or not positive."""
    if _missing(numerator) or _missing(denominator) or denominator <= 0:
        return None
    return numerator / denominator * 100


def load_annual_table(ticker: str) -> pd.DataFrame:
    """One row per fiscal year-end, one column per metric (from the annual_metrics view)."""
    with get_connection() as conn:
        long = pd.read_sql_query(
            "SELECT a.period_end, a.metric, a.value "
            "FROM annual_metrics a JOIN companies c ON c.cik = a.cik "
            "WHERE c.ticker = ?",
            conn,
            params=(ticker,),
        )
    wide = long.pivot(index="period_end", columns="metric", values="value")
    return wide.reindex(columns=METRICS).reset_index()


def derive_liabilities(liabilities, assets, equity):
    """Reported total liabilities if present, else total assets - equity (flagged as derived).
    The derived figure also includes any non-controlling or redeemable interests."""
    if not _missing(liabilities):
        return liabilities, False
    if not _missing(assets) and not _missing(equity):
        return assets - equity, True
    return None, False


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Add growth, margins, free cash flow and ratios to a table from load_annual_table."""
    df = df.sort_values("period_end").reset_index(drop=True)
    out = df.copy()

    # Total liabilities: reported value, or assets - equity when the company does not tag it.
    pairs = [
        derive_liabilities(l, a, e)
        for l, a, e in zip(df["total_liabilities"], df["total_assets"], df["equity"])
    ]
    out["total_liabilities"] = pd.to_numeric(pd.Series([p[0] for p in pairs]), errors="coerce")
    out["total_liabilities_derived"] = [p[1] for p in pairs]

    # Growth only counts when the previous row is about one year earlier.
    gap_days = (
        pd.to_datetime(df["period_end"]) - pd.to_datetime(df["period_end"].shift(1))
    ).dt.days
    out["revenue_growth_pct"] = [
        growth_pct(cur, prev) if pd.notna(gap) and 350 <= gap <= 380 else None
        for cur, prev, gap in zip(df["revenue"], df["revenue"].shift(1), gap_days)
    ]

    out["gross_margin_pct"] = [margin_pct(n, r) for n, r in zip(df["gross_profit"], df["revenue"])]
    out["operating_margin_pct"] = [margin_pct(n, r) for n, r in zip(df["operating_income"], df["revenue"])]
    out["net_margin_pct"] = [margin_pct(n, r) for n, r in zip(df["net_income"], df["revenue"])]

    out["free_cash_flow"] = [
        None if _missing(o) or _missing(c) else o - c
        for o, c in zip(df["operating_cash_flow"], df["capex"])
    ]
    out["fcf_margin_pct"] = [margin_pct(f, r) for f, r in zip(out["free_cash_flow"], df["revenue"])]
    out["roe_pct"] = [ratio_pct(n, e) for n, e in zip(df["net_income"], df["equity"])]
    out["liabilities_to_equity"] = [
        safe_divide(l, e) for l, e in zip(out["total_liabilities"], df["equity"])
    ]
    return out


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    for ticker in ("AAPL", "JPM"):
        table = compute_metrics(load_annual_table(ticker))
        print(f"\n{ticker}")
        print(
            table[
                ["period_end", "revenue_growth_pct", "gross_margin_pct",
                 "operating_margin_pct", "net_margin_pct", "fcf_margin_pct", "roe_pct"]
            ].tail(4).round(2).to_string(index=False)
        )