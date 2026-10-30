import streamlit as st

from src.openbloom.ui.format import isnum, money, pct, times

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


def fin_table(df, n=8) -> str:
    d = df.tail(n)
    derived = (
        [bool(x) for x in d["total_liabilities_derived"]]
        if "total_liabilities_derived" in d.columns
        else [False] * len(d)
    )
    head = "<tr><th>USD · fiscal year end</th>" + "".join(f"<th>{p}</th>" for p in d["period_end"]) + "</tr>"
    body = []
    for label, col, kind in TABLE_ROWS:
        if col is None:
            body.append(f'<tr class="sec"><td colspan="{len(d) + 1}">{label}</td></tr>')
            continue
        cells = []
        for i, v in enumerate(d[col]):
            text = money(v) if kind == "money" else pct(v) if kind == "pct" else times(v)
            if col == "total_liabilities" and derived[i] and isnum(v):
                text += "*"
            cls = ""
            if isnum(v) and kind != "x" and v < 0:
                cls = "down"
            elif isnum(v) and col == "revenue_growth_pct" and v > 0:
                cls = "up"
            cells.append(f'<td class="{cls}">{text}</td>')
        body.append(f"<tr><td>{label}</td>{''.join(cells)}</tr>")
    table = f'<table class="bb-table">{head}{"".join(body)}</table>'
    if any(derived):
        table += (
            '<div style="color:#8a8a8a;font-size:11px;margin-top:6px">'
            "* Derived: total assets minus equity (company does not report total liabilities). "
            "Includes any non-controlling or redeemable interests.</div>"
        )
    return table