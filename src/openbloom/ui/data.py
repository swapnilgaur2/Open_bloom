import pandas as pd
import streamlit as st

from src.openbloom.db import get_connection
from src.openbloom.metrics import compute_metrics, load_annual_table


def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    with get_connection() as conn:
        return pd.read_sql_query(sql, conn, params=params)


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    return query("SELECT ticker, cik, name FROM companies ORDER BY ticker")


@st.cache_data(ttl=600)
def get_metrics(ticker: str) -> pd.DataFrame:
    df = compute_metrics(load_annual_table(ticker))
    for col in df.columns:
        if col != "period_end":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


@st.cache_data(ttl=600)
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