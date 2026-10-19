import html

import plotly.graph_objects as go
import streamlit as st

from src.openbloom.models.dupont import dupont
from src.openbloom.ui.charts import style
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


def render_dupont(df, financial=False) -> None:
    d = dupont(df)
    valid = d.dropna(subset=["roe_pct"])
    if valid.empty:
        st.info("DuPont is not available for this company: needs net income, revenue, total assets and positive equity.")
        return

    latest = d.iloc[-1]
    if pd_isna(latest["roe_pct"]):
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
            fig = _line(d, col, title, yt)
            if fig is None:
                st.caption(f"{title}: not available")
            else:
                st.plotly_chart(fig, key=key)

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


def pd_isna(v) -> bool:
    return not isnum(v)