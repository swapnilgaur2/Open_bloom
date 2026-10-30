import html

import streamlit as st

from src.openbloom.metrics import METRICS
from src.openbloom.ui.charts import bar_chart, compare_chart, growth_chart, line_chart, show_chart
from src.openbloom.ui.data import get_companies, get_metrics, get_revenue_rank, get_snapshot, query
from src.openbloom.ui.format import money, pct, pct_change, pp_change, signed_color
from src.openbloom.ui.labels import FORMULAS, METRIC_LABELS
from src.openbloom.ui.model_views import render_cash_conversion, render_dupont, render_restatements
from src.openbloom.ui.tables import fin_table, kpi, show_kpis
from src.openbloom.ui.theme import GREEN, apply_theme

st.set_page_config(
    page_title="OpenBloom",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)
apply_theme()

companies = get_companies()
tickers = list(companies["ticker"])
names = dict(zip(companies["ticker"], companies["name"]))

st.markdown(
    '<div class="topbar"><span class="brand">OPENBLOOM</span>'
    '<span class="tag">FINANCIAL INTELLIGENCE</span>'
    '<span class="src">SOURCE: SEC EDGAR · ANNUAL 10-K · USD</span></div>',
    unsafe_allow_html=True,
)

# ---------------- universe controls ----------------
col_sec, col_view, col_pick = st.columns([2, 2, 3])
pool = companies
if "sector" in companies.columns:
    sectors = sorted(s for s in companies["sector"].dropna().unique())
    sector = col_sec.selectbox("SECTOR", ["All sectors"] + sectors)
    if sector != "All sectors":
        pool = companies[companies["sector"] == sector]
else:
    col_sec.caption("Sector filter appears once sectors are loaded.")

view = col_view.radio("UNIVERSE", ["TOP 20", "TOP 50", "ALL"], index=2, horizontal=True)
pool_t = list(pool["ticker"])
pool_set = set(pool_t)
ranked = [t for t in get_revenue_rank()["ticker"] if t in pool_set]
view_t = ranked[:20] if view == "TOP 20" else ranked[:50] if view == "TOP 50" else pool_t
if not view_t:
    st.warning("No companies in this selection.")
    st.stop()

ticker = col_pick.selectbox(
    f"SECURITY · {len(view_t)} shown" + (" · ranked by latest revenue" if view != "ALL" else ""),
    view_t,
    index=view_t.index("AAPL") if "AAPL" in view_t else 0,
    format_func=lambda t: f"{t}  |  {names[t]}",
)
company = companies[companies["ticker"] == ticker].iloc[0]
cik = company["cik"]
df = get_metrics(ticker)

info = query(
    "SELECT MIN(period_end) AS first_p, MAX(period_end) AS last_p, MAX(filed_date) AS latest_filing "
    "FROM annual_metrics WHERE cik = ?",
    (cik,),
).iloc[0]
run = query(
    "SELECT MAX(finished_at) AS retrieved FROM ingestion_runs WHERE cik = ? AND status = 'success'",
    (cik,),
).iloc[0]

st.markdown(
    f'<div class="strip"><span class="tk">{ticker} US Equity</span>'
    f'<span class="nm">{html.escape(company["name"])}</span>'
    f'<span class="fy">COVERAGE {info["first_p"]} → {info["last_p"]} · LATEST FILING {info["latest_filing"]} '
    f'· RETRIEVED {run["retrieved"]} UTC</span></div>',
    unsafe_allow_html=True,
)

tab_snap, tab_fin, tab_mod, tab_cmp, tab_q, tab_src = st.tabs(
    ["SNAPSHOT", "FINANCIALS", "MODELS", "COMPARE", "QUALITY", "SOURCE"]
)

# ---------------- SNAPSHOT ----------------
with tab_snap:
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else None

    def pv(col):
        return prev[col] if prev is not None else None

    show_kpis(
        [
            kpi("Revenue", money(last["revenue"]), pct_change(last["revenue"], pv("revenue"))),
            kpi("Operating margin", pct(last["operating_margin_pct"]),
                pp_change(last["operating_margin_pct"], pv("operating_margin_pct"))),
            kpi("Net margin", pct(last["net_margin_pct"]),
                pp_change(last["net_margin_pct"], pv("net_margin_pct"))),
            kpi("Free cash flow", money(last["free_cash_flow"]),
                pct_change(last["free_cash_flow"], pv("free_cash_flow"))),
            kpi("Return on equity", pct(last["roe_pct"]),
                pp_change(last["roe_pct"], pv("roe_pct"))),
        ]
    )
    st.caption(f"Fiscal year ending {last['period_end']}. '—' = not reported under the tags we map, or not applicable to this business.")

    c1, c2 = st.columns(2)
    with c1:
        show_chart(bar_chart(df, ["revenue", "operating_income", "net_income"], "REVENUE · OPERATING INCOME · NET INCOME"),
                   "Income", "g1")
    with c2:
        show_chart(line_chart(df, ["gross_margin_pct", "operating_margin_pct", "net_margin_pct", "fcf_margin_pct"],
                              "MARGINS"), "Margins", "g2")
    c3, c4 = st.columns(2)
    with c3:
        show_chart(growth_chart(df, "REVENUE GROWTH, YoY"), "Growth", "g3")
    with c4:
        show_chart(bar_chart(df, ["operating_cash_flow", "capex", "free_cash_flow"], "CASH FLOW"),
                   "Cash flow", "g4")

# ---------------- FINANCIALS ----------------
with tab_fin:
    st.markdown(fin_table(df, 8), unsafe_allow_html=True)
    st.caption("Last 8 fiscal years. Values from 10-K filings; restated figures use the most recent filing.")

# ---------------- MODELS ----------------
with tab_mod:
    st.markdown("##### FINANCIAL MODELS · deterministic, tested code, every input shown")
    model = st.radio(
        "MODEL", ["DUPONT ROE", "CASH CONVERSION", "RESTATEMENTS"], horizontal=True, label_visibility="collapsed"
    )
    is_fin = ticker in {"JPM", "BAC", "GS", "BRK-B"} or company.get("sector") == "Financials"
    if model == "DUPONT ROE":
        render_dupont(df, financial=is_fin)
    elif model == "CASH CONVERSION":
        render_cash_conversion(df, financial=is_fin)
    else:
        render_restatements(ticker)

# ---------------- COMPARE ----------------
with tab_cmp:
    cc1, cc2 = st.columns([3, 2])
    picked = cc1.multiselect(
        "COMPANIES", tickers, default=[t for t in ["AAPL", "MSFT", "NVDA"] if t in tickers]
    )
    metric = cc2.selectbox("METRIC", list(METRIC_LABELS.keys()), format_func=lambda k: METRIC_LABELS[k])

    st.plotly_chart(compare_chart({t: get_metrics(t) for t in picked}, metric), key="cmp")
    st.caption("X-axis = calendar year in which the fiscal year ends (Apple: September, Nvidia: January).")

    st.markdown(f"##### SCREENER · latest fiscal year · {view} ({len(view_t)} companies)")
    snap = get_snapshot(tuple(view_t))
    snap.insert(1, "Company", snap["Ticker"].map(names))
    styled = (
        snap.style.format(
            {
                "Revenue ($B)": "{:,.1f}",
                "Growth %": "{:,.1f}",
                "Op margin %": "{:,.1f}",
                "Net margin %": "{:,.1f}",
                "FCF margin %": "{:,.1f}",
                "ROE %": "{:,.1f}",
            },
            na_rep="—",
        ).map(signed_color, subset=["Growth %", "Op margin %", "Net margin %", "FCF margin %", "ROE %"])
    )
    st.dataframe(styled, hide_index=True, height=620)

# ---------------- QUALITY ----------------
with tab_q:
    runs = query("SELECT status, COUNT(*) AS n FROM ingestion_runs GROUP BY status")
    ok_runs = int(runs.loc[runs["status"] == "success", "n"].sum())
    failed_runs = int(runs.loc[runs["status"] == "failed", "n"].sum())
    flags = int(query("SELECT COUNT(*) AS n FROM quality_issues").iloc[0]["n"])

    cov = query(
        "SELECT c.ticker AS ticker, a.metric AS metric, COUNT(*) AS n "
        "FROM annual_metrics a JOIN companies c ON c.cik = a.cik GROUP BY c.ticker, a.metric"
    )
    matrix = (
        cov.pivot(index="ticker", columns="metric", values="n")
        .reindex(index=tickers, columns=METRICS)
        .fillna(0)
        .astype(int)
    )
    coverage_pct = (matrix > 0).values.mean() * 100

    show_kpis(
        [
            kpi("Companies loaded", str(len(companies))),
            kpi("Ingestion runs OK", str(ok_runs)),
            kpi("Failed runs", str(failed_runs)),
            kpi("Missing-metric flags", str(flags)),
            kpi("Metric coverage", pct(coverage_pct)),
        ]
    )

    st.markdown("##### COVERAGE MATRIX · number of fiscal years available per company and metric")
    st.dataframe(
        matrix.style.map(
            lambda v: "background-color:#2a0d0d;color:#FF4D4D" if v == 0 else f"color:{GREEN}"
        ),
        height=560,
    )
    st.caption(
        "Red 0 = no reported data. Banks do not report operating income or capex; many companies do not report gross profit. "
        "Total liabilities is derived (assets minus equity, marked * in FINANCIALS) when not reported, "
        "so it can show red here while still being available there."
    )

    st.markdown("##### FLAGGED ISSUES")
    issues = query(
        "SELECT c.ticker, q.metric, q.issue_type, q.detail, q.detected_at "
        "FROM quality_issues q JOIN companies c ON c.cik = q.cik ORDER BY c.ticker, q.metric"
    )
    st.dataframe(issues, hide_index=True, height=300)

# ---------------- SOURCE ----------------
with tab_src:
    st.markdown("##### PROVENANCE · SEC filing, XBRL tag and period behind each stored value")
    prov_metric = st.selectbox("METRIC", METRICS)
    prov = query(
        "SELECT period_end, value, tag, form, accession, filed_date "
        "FROM annual_metrics WHERE cik = ? AND metric = ? ORDER BY period_end DESC",
        (cik, prov_metric),
    )
    if prov.empty:
        st.info("No data for this metric.")
    else:
        prov["value (USD)"] = prov["value"].map(lambda v: f"{v:,.0f}")
        prov["filing"] = prov["accession"].map(
            lambda a: f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{a.replace('-', '')}/"
        )
        st.dataframe(
            prov[["period_end", "value (USD)", "tag", "form", "accession", "filed_date", "filing"]],
            hide_index=True,
            column_config={"filing": st.column_config.LinkColumn("SEC filing folder")},
        )
        st.caption(
            "Rule: if several tags or restated values exist for one year, keep the highest-priority tag, "
            "then the most recently filed value."
        )

    st.markdown("##### CALCULATION FORMULAS")
    rows = "".join(
        f"<tr><td>{k}</td><td style='text-align:left'>{html.escape(v)}</td></tr>"
        for k, v in FORMULAS.items()
    )
    st.markdown(
        f'<table class="bb-table"><tr><th>metric</th><th style="text-align:left">formula</th></tr>{rows}</table>',
        unsafe_allow_html=True,
    )