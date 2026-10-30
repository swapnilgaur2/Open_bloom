import html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.openbloom.models.cash_conversion import cash_conversion
from src.openbloom.models.dupont import dupont
from src.openbloom.models.restatements import find_restatements
from src.openbloom.ui.charts import bar_chart, style
from src.openbloom.ui.data import query
from src.openbloom.ui.format import isnum, money, pct, pct_change, pp_change, times
from src.openbloom.ui.tables import kpi, show_kpis


def _line(d, col, title, ytitle):
    if not d[col].notna().any():
        return None
    fig = go.Figure(go.Scatter(x=d["period_end"].str[:7], y=d[col], mode="lines+markers", name=title))
    fig.update_xaxes(type="category")
    fig.update_yaxes(title_text=ytitle)
    fig.update_layout(showlegend=False)
    return style(fig, title, height=300)


def _table(rows, d) -> str:
    head = "<tr><th>fiscal year end</th>" + "".join(f"<th>{p}</th>" for p in d["period_end"]) + "</tr>"
    body = []
    for label, col, fmt in rows:
        if col is None:
            body.append(f'<tr class="sec"><td colspan="{len(d) + 1}">{label}</td></tr>')
            continue
        cells = []
        for v in d[col]:
            if fmt == "text":
                cells.append(f"<td>{html.escape(str(v)) if v else ''}</td>")
                continue
            cls = "down" if (isnum(v) and fmt in ("money", "chg") and v < 0) else ""
            cls = "up" if (fmt == "chg" and isnum(v) and v > 0) else cls
            text = {"money": money, "pct": pct, "x": times, "chg": lambda x: "—" if not isnum(x) else f"{x:+.1f}%"}[fmt](v)
            cells.append(f'<td class="{cls}">{text}</td>')
        body.append(f"<tr><td>{label}</td>{''.join(cells)}</tr>")
    return f'<table class="bb-table">{head}{"".join(body)}</table>'


def _plot(fig, title, key):
    if fig is None:
        st.caption(f"{title}: not available")
    else:
        st.plotly_chart(fig, key=key)


# ---------------- DuPont ----------------
def render_dupont(df, financial=False) -> None:
    d = dupont(df)
    valid = d.dropna(subset=["roe_pct"])
    if valid.empty:
        st.info("DuPont is not available for this company: needs net income, revenue, total assets and positive equity.")
        return

    latest = d.iloc[-1]
    if not isnum(latest["roe_pct"]):
        st.warning(f"Latest fiscal year ({latest['period_end']}) not computable: {latest['note']}. Showing the last valid year.")
    last = valid.iloc[-1]
    prev = valid.iloc[-2] if len(valid) > 1 else None

    def pv(c):
        return prev[c] if prev is not None else None

    show_kpis(
        [
            kpi("Return on equity", pct(last["roe_pct"]), pp_change(last["roe_pct"], pv("roe_pct"))),
            kpi("Net margin", pct(last["net_margin_pct"]), pp_change(last["net_margin_pct"], pv("net_margin_pct"))),
            kpi("Asset turnover", times(last["asset_turnover"]), pct_change(last["asset_turnover"], pv("asset_turnover"))),
            kpi("Equity multiplier", times(last["equity_multiplier"]), pct_change(last["equity_multiplier"], pv("equity_multiplier"))),
            kpi("Fiscal year end", last["period_end"]),
        ]
    )
    st.caption("ROE = net margin x asset turnover x equity multiplier. Net margin = profitability, turnover = efficiency, multiplier = leverage.")
    if financial:
        st.caption("Banks and insurers run on leverage by design: a high equity multiplier and low turnover are normal. Compare within financials only.")

    c1, c2 = st.columns(2)
    for col, title, yt, key, box in [
        ("roe_pct", "RETURN ON EQUITY", "%", "dp1", c1),
        ("net_margin_pct", "NET MARGIN", "%", "dp2", c2),
        ("asset_turnover", "ASSET TURNOVER", "x (revenue / assets)", "dp3", c1),
        ("equity_multiplier", "EQUITY MULTIPLIER", "x (assets / equity)", "dp4", c2),
    ]:
        with box:
            _plot(_line(d, col, title, yt), title, key)

    tail = d.tail(8)
    st.markdown("##### INPUTS AND RATIOS · every number behind the model")
    st.markdown(
        _table(
            [
                ("INPUTS (year-end, from 10-K)", None, None),
                ("Net income", "net_income", "money"),
                ("Revenue", "revenue", "money"),
                ("Total assets", "total_assets", "money"),
                ("Equity", "equity", "money"),
                ("DUPONT", None, None),
                ("Net margin", "net_margin_pct", "pct"),
                ("Asset turnover", "asset_turnover", "x"),
                ("Equity multiplier", "equity_multiplier", "x"),
                ("ROE", "roe_pct", "pct"),
                ("Not computable because", "note", "text"),
            ],
            tail,
        ),
        unsafe_allow_html=True,
    )

    st.markdown("##### WHAT CHANGED ROE · year-over-year, log-% (adds up exactly)")
    st.markdown(
        _table(
            [
                ("Net margin effect", "chg_margin", "chg"),
                ("Asset turnover effect", "chg_turnover", "chg"),
                ("Leverage effect", "chg_leverage", "chg"),
                ("Total ROE change", "chg_roe", "chg"),
            ],
            tail,
        ),
        unsafe_allow_html=True,
    )
    st.caption(
        "Shown only when both years are valid with positive net income. "
        "A rising ROE driven by the leverage effect (often buybacks) is lower quality than one driven by margin."
    )


# ---------------- Cash conversion ----------------
def render_cash_conversion(df, financial=False) -> None:
    d = cash_conversion(df)
    valid = d.dropna(subset=["cash_conversion"])
    if valid.empty:
        st.info("Cash conversion is not available for this company: needs positive net income and operating cash flow.")
        return

    latest = d.iloc[-1]
    if not isnum(latest["cash_conversion"]):
        st.warning(f"Latest fiscal year ({latest['period_end']}) not computable: {latest['note']}. Showing the last valid year.")
    last = valid.iloc[-1]
    prev = valid.iloc[-2] if len(valid) > 1 else None

    show_kpis(
        [
            kpi("Cash conversion", times(last["cash_conversion"]),
                pct_change(last["cash_conversion"], prev["cash_conversion"] if prev is not None else None)),
            kpi("3-year conversion", times(last["conv_3y"])),
            kpi("Accruals ratio", pct(last["accruals_pct"])),
            kpi("Net income", money(last["net_income"])),
            kpi("Operating cash flow", money(last["operating_cash_flow"])),
        ]
    )
    st.caption(
        f"Fiscal year ending {last['period_end']}. Conversion = operating cash flow / net income. "
        "Above 1.0x, profit is backed by cash. Persistently below 1.0x, or a high positive accruals ratio, "
        "means earnings are not turning into cash."
    )
    if financial:
        st.caption("Banks and insurers: operating cash flow includes loan and deposit flows, so this is not comparable to other sectors.")

    c1, c2 = st.columns(2)
    with c1:
        _plot(bar_chart(d, ["net_income", "operating_cash_flow"], "NET INCOME vs OPERATING CASH FLOW"), "Net income vs OCF", "cc1")
    with c2:
        _plot(_line(d, "cash_conversion", "CASH CONVERSION", "x (OCF / net income)"), "Cash conversion", "cc2")
    c3, c4 = st.columns(2)
    with c3:
        _plot(_line(d, "conv_3y", "3-YEAR CASH CONVERSION", "x (3y OCF / 3y net income)"), "3-year conversion", "cc3")
    with c4:
        _plot(_line(d, "accruals_pct", "ACCRUALS RATIO", "% of average total assets"), "Accruals ratio", "cc4")

    tail = d.tail(8)
    st.markdown("##### INPUTS AND RATIOS · every number behind the model")
    st.markdown(
        _table(
            [
                ("INPUTS (from 10-K)", None, None),
                ("Net income", "net_income", "money"),
                ("Operating cash flow", "operating_cash_flow", "money"),
                ("Total assets (year-end)", "total_assets", "money"),
                ("CASH CONVERSION", None, None),
                ("Conversion (OCF / net income)", "cash_conversion", "x"),
                ("3-year conversion", "conv_3y", "x"),
                ("Accruals ratio (avg assets)", "accruals_pct", "pct"),
                ("Not computable because", "note", "text"),
            ],
            tail,
        ),
        unsafe_allow_html=True,
    )
    st.caption("Accruals ratio = (net income - operating cash flow) / average of this and last year's total assets. Needs two consecutive years.")


# ---------------- Restatements ----------------
_FACTS_SQL = (
    "SELECT c.ticker AS ticker, f.cik AS cik, a.metric AS metric, f.tag AS tag, "
    "f.period_start AS period_start, f.period_end AS period_end, f.value AS value, "
    "f.accession AS accession, f.form AS form, f.filed_date AS filed_date "
    "FROM facts f "
    "JOIN annual_metrics a ON a.cik = f.cik AND a.tag = f.tag AND a.period_end = f.period_end "
    "JOIN companies c ON c.cik = f.cik"
)


@st.cache_data(ttl=3600)
def load_restatements() -> pd.DataFrame:
    return find_restatements(query(_FACTS_SQL))


def _link(row) -> str:
    return f"https://www.sec.gov/Archives/edgar/data/{int(row['cik'])}/{row['latest_accession'].replace('-', '')}/"


def _restatement_display(r, with_ticker=False) -> pd.DataFrame:
    out = pd.DataFrame(
        {
            "Metric": r["metric"].to_numpy(),
            "FY end": r["period_end"].to_numpy(),
            "Original (USD)": r["original_value"].map(lambda v: f"{v:,.0f}").to_numpy(),
            "Restated (USD)": r["latest_value"].map(lambda v: f"{v:,.0f}").to_numpy(),
            "Change %": r["change_pct"].map(lambda v: "—" if not isnum(v) else f"{v:+.1f}%").to_numpy(),
            "Original filed": r["original_filed"].to_numpy(),
            "Latest filed": r["latest_filed"].to_numpy(),
            "Versions": r["versions"].to_numpy(),
            "SEC filing": r.apply(_link, axis=1).to_numpy(),
        }
    )
    if with_ticker:
        out.insert(0, "Ticker", r["ticker"].to_numpy())
    return out


def render_restatements(ticker: str) -> None:
    allr = load_restatements()
    st.caption(
        "Shows reported values that changed between filings. A later 10-K repeating the same number is not a change. "
        "A change is not necessarily an error: many are reclassifications or recasts for discontinued operations."
    )
    min_chg = st.selectbox("MIN CHANGE", [0.0, 0.5, 1.0, 5.0], index=1, format_func=lambda x: f"≥ {x}% (absolute)")
    cfg = {"SEC filing": st.column_config.LinkColumn("Latest filing")}

    def filt(r):
        r = r[r["change_pct"].abs() >= min_chg] if min_chg > 0 else r
        return r.assign(_a=r["change_pct"].abs()).sort_values("_a", ascending=False).drop(columns="_a")

    mine = filt(allr[allr["ticker"] == ticker]) if not allr.empty else allr
    st.markdown(f"##### {ticker} · values that changed between filings")
    if mine.empty:
        st.info("No stored annual value for this company changed between filings at this threshold.")
    else:
        show_kpis(
            [
                kpi("Changed values", str(len(mine))),
                kpi("Largest change", f"{mine['change_pct'].iloc[0]:+.1f}%" if isnum(mine["change_pct"].iloc[0]) else "—"),
                kpi("Metrics affected", str(mine["metric"].nunique())),
                kpi("Fiscal years affected", str(mine["period_end"].nunique())),
                kpi("Latest restating filing", str(mine["latest_filed"].max())),
            ]
        )
        st.dataframe(_restatement_display(mine), hide_index=True, column_config=cfg)

    st.markdown("##### LARGEST CHANGES · all companies")
    top = filt(allr).head(40) if not allr.empty else allr
    if top.empty:
        st.info("Nothing at this threshold.")
    else:
        st.dataframe(_restatement_display(top, with_ticker=True), hide_index=True, column_config=cfg, height=520)