import plotly.graph_objects as go
import streamlit as st

from src.openbloom.ui.format import isnum
from src.openbloom.ui.labels import LABELS, METRIC_LABELS
from src.openbloom.ui.theme import AMBER, COLORWAY, GREEN, MONO, RED


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


def compare_chart(series_by_ticker, metric):
    """series_by_ticker: dict of ticker -> metrics DataFrame."""
    fig = go.Figure()
    for t, d in series_by_ticker.items():
        d = d.dropna(subset=[metric])
        if d.empty:
            continue
        fig.add_trace(
            go.Scatter(x=d["period_end"].str[:4].astype(int), y=d[metric], mode="lines+markers", name=t)
        )
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(title_text=METRIC_LABELS[metric])
    return style(fig, f"{METRIC_LABELS[metric].upper()} BY FISCAL YEAR", height=400)


def show_chart(fig, title, key):
    if fig is None:
        st.caption(f"{title}: not available for this company")
    else:
        st.plotly_chart(fig, key=key)