import pandas as pd

from src.openbloom.ui.theme import GREEN, RED


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


def signed_color(v):
    if not isnum(v):
        return ""
    return f"color:{GREEN}" if v > 0 else f"color:{RED}" if v < 0 else ""