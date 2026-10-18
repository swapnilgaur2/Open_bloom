import pandas as pd

from src.openbloom.metrics import compute_metrics, growth_pct, margin_pct, safe_divide


def test_growth_typical():
    assert growth_pct(110, 100) == 10


def test_growth_matches_hand_checked_apple_value():
    # FY2025 vs FY2024 revenue, checked by hand: 6.43%
    assert round(growth_pct(416161e6, 391035e6), 2) == 6.43


def test_growth_missing_or_zero_previous():
    assert growth_pct(100, None) is None
    assert growth_pct(100, 0) is None
    assert growth_pct(100, -50) is None


def test_margin_hand_checked_apple_value():
    # FY2025 operating income / revenue, checked by hand: 31.97%
    assert round(margin_pct(133050e6, 416161e6), 2) == 31.97


def test_margin_zero_or_missing_revenue():
    assert margin_pct(50, 0) is None
    assert margin_pct(50, None) is None


def test_safe_divide():
    assert safe_divide(10, 4) == 2.5
    assert safe_divide(10, 0) is None


def _table(rows):
    cols = ["period_end", "revenue", "gross_profit", "operating_income", "net_income",
            "operating_cash_flow", "capex", "total_assets", "total_liabilities",
            "equity", "cash"]
    return pd.DataFrame(rows, columns=cols)


def test_compute_metrics_basic():
    df = _table([
        ["2023-12-31", 100, 40, 20, 10, 30, 10, 500, 300, 200, 50],
        ["2024-12-31", 120, 50, 21, 12, 35, 15, 600, 350, 250, 60],
    ])
    out = compute_metrics(df)
    last = out.iloc[-1]
    assert round(last["revenue_growth_pct"], 2) == 20.0
    assert round(last["operating_margin_pct"], 2) == 17.5
    assert last["free_cash_flow"] == 20
    assert round(last["roe_pct"], 2) == 4.8


def test_growth_skipped_when_a_year_is_missing():
    df = _table([
        ["2022-12-31", 100, None, None, None, None, None, None, None, None, None],
        ["2024-12-31", 150, None, None, None, None, None, None, None, None, None],
    ])
    assert compute_metrics(df).iloc[-1]["revenue_growth_pct"] is None


def test_free_cash_flow_missing_capex():
    df = _table([["2024-12-31", 100, None, None, None, 30, None, None, None, None, None]])
    assert compute_metrics(df).iloc[0]["free_cash_flow"] is None