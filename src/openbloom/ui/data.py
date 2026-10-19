import pandas as pd
import streamlit as st

from src.openbloom.db import get_connection
from src.openbloom.metrics import compute_metrics, load_annual_table


def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)


@st.cache_data(ttl=3600)
def get_companies() -> pd.DataFrame:
    return query("SELECT * FROM companies ORDER BY ticker")


@st.cache_data(ttl=3600)
def get_revenue_rank() -> pd.DataFrame:
    """Companies ranked by latest annual revenue (largest first). No prices yet, so not market cap.
    Companies whose latest revenue is more than ~15 months older than the newest filing are dropped."""
    df = query(
        "SELECT c.ticker AS ticker, a.period_end AS period_end, a.value AS revenue "
        "FROM annual_metrics a JOIN companies c ON c.cik = a.cik WHERE a.metric = 'revenue'"
    )
    if df.empty:
        return pd.DataFrame(columns=["ticker", "revenue"])
    latest = df.sort_values("period_end").groupby("ticker", as_index=False).last()
    newest = pd.to_datetime(latest["period_end"]).max()
    fresh = (newest - pd.to_datetime(latest["period_end"])).dt.days <= 450
    latest = latest[fresh]
    return latest.sort_values("revenue", ascending=False)[["ticker", "revenue"]].reset_index(drop=True)


@st.cache_data(ttl=3600)
def get_metrics(ticker: str) -> pd.DataFrame:
    df = compute_metrics(load_annual_table(ticker))
    for col in df.columns:
        if col != "period_end":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(ttl=3600)
def get_snapshot(tickers: tuple) -> pd.DataFrame:
    rows = []
    for t in tickers:
        df = get_metrics(t)
        if df.empty:
            continue
        last = df.iloc[-1]
        rows.append(
            {
                "Ticker": t,
                "FY end": last["period_end"],
                "Revenue ($B)": last["revenue"] / 1e9,
                "Growth %": last["revenue_growth_pct"],
                "Op margin %": last["operating_margin_pct"],
                "Net margin %": last["net_margin_pct"],
                "FCF margin %": last["fcf_margin_pct"],
                "ROE %": last["roe_pct"],
            }
        )
    return pd.DataFrame(rows)