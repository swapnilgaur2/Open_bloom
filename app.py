import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.openbloom.db import get_connection
from src.openbloom.metrics import METRICS, compute_metrics, load_annual_table

st.set_page_config(
    page_title="OpenBloom",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

AMBER, GREEN, RED, BLUE = "#FFB000", "#00D26A", "#FF4D4D", "#4FC3F7"
COLORWAY = [AMBER, BLUE, GREEN, "#E040FB", RED, "#B0BEC5"]
MONO = "IBM Plex Mono, Consolas, monospace"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');
.stApp { font-family: 'IBM Plex Mono', Consolas, monospace; background: #000; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.block-container { padding: 0.6rem 1.4rem 2rem 1.4rem; max-width: 100%; }

.topbar { display:flex; align-items:center; gap:18px; border-bottom:2px solid #FFB000;
          padding:6px 0 8px 0; margin-bottom:8px; font-family:'IBM Plex Mono',Consolas,monospace; }
.brand { background:#FFB000; color:#000; font-weight:700; padding:3px 10px; letter-spacing:2px; font-size:16px; }
.tag { color:#FFB000; font-size:12px; letter-spacing:1.5px; }
.src { margin-left:auto; color:#8a8a8a; font-size:11px; }

.strip { display:flex; align-items:baseline; gap:16px; padding:8px 12px; background:#0b0b0b;
         border:1px solid #262626; margin:6px 0 10px 0; font-family:'IBM Plex Mono',Consolas,monospace; }
.tk { color:#FFB000; font-weight:700; font-size:20px; }
.nm { color:#fff; font-size:16px; }
.fy { margin-left:auto; color:#8a8a8a; font-size:11px; }

.kpi-row { display:grid; grid-template-columns:repeat(5,1fr); gap:8px; margin-bottom:10px; }
.kpi { background:#0b0b0b; border:1px solid #262626; border-left:3px solid #FFB000; padding:8px 12px;
       font-family:'IBM Plex Mono',Consolas,monospace; }
.kpi-l { color:#8a8a8a; font-size:10px; letter-spacing:1px; text-transform:uppercase; }
.kpi-v { color:#fff; font-size:22px; font-weight:600; margin-top:2px; }
.kpi-d { font-size:11px; margin-top:2px; color:#8a8a8a; }
.up { color:#00D26A; }
.down { color:#FF4D4D; }

.bb-table { width:100%; border-collapse:collapse; font-size:12px; font-family:'IBM Plex Mono',Consolas,monospace; }
.bb-table th { background:#1a1300; color:#FFB000; text-align:right; padding:5px 10px;
               border-bottom:1px solid #FFB000; font-weight:600; }
.bb-table td { text-align:right; padding:4px 10px; border-bottom:1px solid #161616; color:#e6e6e6; }
.bb-table th:first-child, .bb-table td:first-child { text-align:left; }
.bb-table td.up { color:#00D26A; }
.bb-table td.down { color:#FF4D4D; }
.bb-table tr:hover td { background:#111; }
.bb-table tr.sec td { background:#0f0f0f; color:#FFB000; font-weight:600; letter-spacing:1px;
                      text-align:left; border-bottom:1px solid #333; padding-top:9px; }

.stTabs [data-baseweb="tab-list"] { gap:0; border-bottom:1px solid #333; }
.stTabs [data-baseweb="tab"] { background:transparent; color:#8a8a8a; letter-spacing:1.5px;
                               font-size:12px; padding:8px 18px; }
.stTabs [aria-selected="true"] { color:#000 !important; background:#FFB000 !important; }
.stTabs [data-baseweb="tab-highlight"] { background:transparent !important; }
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

LABELS = {
    "revenue": "Revenue",
    "gross_profit": "Gross profit",
    "operating_income": "Operating income",
    "net_income": "Net income",
    "operating_cash_flow": "Operating cash flow",
    "capex": "Capex",
    "free_cash_flow": "Free cash flow",
    "gross_margin_pct": "Gross margin",
    "operating_margin_pct": "Operating margin",
    "net_margin_pct": "Net margin",
    "fcf_margin_pct": "FCF margin",
}

METRIC_LABELS = {
    "revenue_growth_pct": "Revenue growth (%)",
    "gross_margin_pct": "Gross margin (%)",
    "operating_margin_pct": "Operating margin (%)",
    "net_margin_pct": "Net margin (%)",
    "fcf_margin_pct": "FCF margin (%)",
    "roe_pct": "ROE (%)",
    "liabilities_to_equity": "Liabilities / equity (x)",
}

FORMULAS = {
    "revenue_growth_pct": "(revenue - previous year revenue) / previous year revenue x 100. Only if the previous row is about 1 year earlier and positive.",
    "gross_margin_pct": "gross_profit / revenue x 100",
    "operating_margin_pct": "operating_income / revenue x 100",
    "net_margin_pct": "net_income / revenue x 100",
    "free_cash_flow": "operating_cash_flow - capex",
    "fcf_margin_pct": "free_cash_flow / revenue x 100",
    "roe_pct": "net_income / equity x 100 (distorted when equity is small, e.g. after buybacks)",
    "liabilities_to_equity": "total_liabilities / equity",
}

TABLE_ROWS = [
    ("INCOME STATEMENT", None, None),
    ("Revenue", "revenue", "money"),
    ("Gross profit", "gross_profit", "money"),
    ("Operating income", "operating_income", "money"),
    ("Net income", "net_income", "money"),
    ("CASH FLOW", None, None),
    ("Operating cash flow", "operating_cash_flow", "money"),
    ("Capex (payments)", "capex", "money"),
    ("Free cash flow", "free_cash_flow", "money"),
    ("BALANCE SHEET", None, None),
    ("Total assets", "total_assets", "money"),
    ("Total liabilities", "total_liabilities", "money"),
    ("Equity", "equity", "money"),
    ("Cash", "cash", "money"),
    ("RATIOS", None, None),
    ("Revenue growth, YoY", "revenue_growth_pct", "pct"),
    ("Gross margin", "gross_margin_pct", "pct"),
    ("Operating margin", "operating_margin_pct", "pct"),
    ("Net margin", "net_margin_pct", "pct"),
    ("FCF margin", "fcf_margin_pct", "pct"),
    ("Return on equity", "roe_pct", "pct"),
    ("Liabilities / equity", "liabilities_to_equity", "x"),
]


# ---------------- formatting helpers ----------------
def isnum(v) -> bool:
    return v is not None and pd.notna(v)


def money(v) -> str:
    if not isnum(v):
        return "—"
    a, sign = abs(v), ("-" if v < 0 else "")
    if a >= 1e12:
        return f"{sign}${a / 1e12:,.2f}T"
    if a >= 1e9:
        return f"{sign}${a / 1e9:,.1f}B"
    if a >= 1e6:
        return f"{sign}${a / 1e6:,.0f}M"
    return f"{sign}${a:,.0f}"


def pct(v, digits=1) -> str:
    return "—" if not isnum(v) else f"{v:,.{digits}f}%"


def times(v) -> str:
    return "—" if not isnum(v) else f"{v:,.2f}x"


def pp_change(cur, prev):
    if isnum(cur) and isnum(prev):
        d = cur - prev
        return f"{d:+.1f} pp YoY", d
    return None, None


def pct_change(cur, prev):
    if isnum(cur) and isnum(prev) and prev != 0:
        d = (cur - prev) / abs(prev) * 100
        return f"{d:+.1f}% YoY", d
    return None, None


def kpi(label, value, delta=(None, None)) -> str:
    text, val = delta
    if text is None:
        d = '<div class="kpi-d">&nbsp;</div>'
    else:
        cls = "up" if val >= 0 else "down"
        arrow = "▲" if val >= 0 else "▼"
        d = f'<div class="kpi-d {cls}">{arrow} {text}</div>'
    return f'<div class="kpi"><div class="kpi-l">{label}</div><div class="kpi-v">{value}</div>{d}</div>'


def show_kpis(cards) -> None:
    st.markdown(f'<div class="kpi-row">{"".join(cards)}</div>', unsafe_allow_html=True)


# ---------------- data access ----------------
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


# ---------------- chart helpers ----------------
def xlabels(df):
    """Compact x-axis labels: YYYY-MM of the fiscal year end."""
    return df["period_end"].str[:7]


def style(fig, title, height=360):
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=AMBER), x=0, y=0.97, yanchor="top"),
        height=height,
        paper_bgcolor="#000",
        plot_bgcolor="#000",
        font=dict(family=MONO, color="#c8c8c8", size=11),
        margin=dict(l=10, r=10, t=60, b=80),
        colorway=COLORWAY,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.16,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=10),
        ),
        hoverlabel=dict(bgcolor="#111", font=dict(family=MONO)),
    )
    fig.update_xaxes(gridcolor="#161616", linecolor="#333", automargin=True)
    fig.update_yaxes(gridcolor="#161616", linecolor="#333", zeroline=True, zerolinecolor="#333", automargin=True)
    return fig


def bar_chart(df, cols, title):
    cols = [c for c in cols if df[c].notna().any()]
    if not cols:
        return None
    fig = go.Figure()
    for c in cols:
        fig.add_trace(go.Bar(x=xlabels(df), y=df[c] / 1e9, name=LABELS[c]))
    fig.update_layout(barmode="group")
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="USD billions")
    return style(fig, title)


def line_chart(df, cols, title):
    cols = [c for c in cols if df[c].notna().any()]
    if not cols:
        return None
    fig = go.Figure()
    for c in cols:
        fig.add_trace(go.Scatter(x=xlabels(df), y=df[c], name=LABELS[c], mode="lines+markers"))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="% of revenue")
    return style(fig, title)


def growth_chart(df, title):
    if not df["revenue_growth_pct"].notna().any():
        return None
    colors = [GREEN if (isnum(v) and v >= 0) else RED for v in df["revenue_growth_pct"]]
    fig = go.Figure(go.Bar(x=xlabels(df), y=df["revenue_growth_pct"], marker_color=colors, name="Revenue growth"))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text="% YoY")
    fig.update_layout(showlegend=False)
    return style(fig, title, height=320)


def show_chart(fig, title, key):
    if fig is None:
        st.caption(f"{title}: not available for this company")
    else:
        st.plotly_chart(fig, key=key)


def fin_table(df, n=8) -> str:
    d = df.tail(n)
    head = "<tr><th>USD · fiscal year end</th>" + "".join(f"<th>{p}</th>" for p in d["period_end"]) + "</tr>"
    body = []
    for label, col, kind in TABLE_ROWS:
        if col is None:
            body.append(f'<tr class="sec"><td colspan="{len(d) + 1}">{label}</td></tr>')
            continue
        cells = []
        for v in d[col]:
            text = money(v) if kind == "money" else pct(v) if kind == "pct" else times(v)
            cls = ""
            if isnum(v) and kind != "x" and v < 0:
                cls = "down"
            elif isnum(v) and col == "revenue_growth_pct" and v > 0:
                cls = "up"
            cells.append(f'<td class="{cls}">{text}</td>')
        body.append(f"<tr><td>{label}</td>{''.join(cells)}</tr>")
    return f'<table class="bb-table">{head}{"".join(body)}</table>'


def signed_color(v):
    if not isnum(v):
        return ""
    return f"color:{GREEN}" if v > 0 else f"color:{RED}" if v < 0 else ""


# ---------------- page ----------------
companies = get_companies()
tickers = list(companies["ticker"])

st.markdown(
    '<div class="topbar"><span class="brand">OPENBLOOM</span>'
    '<span class="tag">FINANCIAL INTELLIGENCE</span>'
    '<span class="src">SOURCE: SEC EDGAR · ANNUAL 10-K · USD</span></div>',
    unsafe_allow_html=True,
)

names = dict(zip(companies["ticker"], companies["name"]))
sel_col, _ = st.columns([2, 3])
ticker = sel_col.selectbox(
    "SECURITY",
    tickers,
    index=tickers.index("AAPL") if "AAPL" in tickers else 0,
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

tab_snap, tab_fin, tab_cmp, tab_q, tab_src = st.tabs(
    ["SNAPSHOT", "FINANCIALS", "COMPARE", "QUALITY", "SOURCE"]
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

# ---------------- COMPARE ----------------
with tab_cmp:
    cc1, cc2 = st.columns([3, 2])
    picked = cc1.multiselect(
        "COMPANIES", tickers, default=[t for t in ["AAPL", "MSFT", "NVDA"] if t in tickers]
    )
    metric = cc2.selectbox("METRIC", list(METRIC_LABELS.keys()), format_func=lambda k: METRIC_LABELS[k])

    fig = go.Figure()
    for t in picked:
        d = get_metrics(t).dropna(subset=[metric])
        if d.empty:
            continue
        fig.add_trace(go.Scatter(x=d["period_end"].str[:4].astype(int), y=d[metric],
                                 mode="lines+markers", name=t))
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(title_text=METRIC_LABELS[metric])
    st.plotly_chart(style(fig, f"{METRIC_LABELS[metric].upper()} BY FISCAL YEAR", height=400), key="cmp")
    st.caption("X-axis = calendar year in which the fiscal year ends (Apple: September, Nvidia: January).")

    st.markdown("##### SCREENER · latest fiscal year, all companies")
    snap = get_snapshot(tuple(tickers))
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
    st.caption("Red 0 = no data. Banks do not report operating income or capex; many companies do not report gross profit.")

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