import math

import pandas as pd

from src.openbloom.models.dupont import dupont

COLS = ["period_end", "net_income", "revenue", "total_assets", "equity"]


def test_worked_example():
    d = dupont(pd.DataFrame([["2024-12-31", 100, 1000, 500, 250]], columns=COLS))
    r = d.iloc[0]
    assert math.isclose(r["net_margin_pct"], 10.0)
    assert math.isclose(r["asset_turnover"], 2.0)
    assert math.isclose(r["equity_multiplier"], 2.0)
    assert math.isclose(r["roe_pct"], 40.0)
    assert r["note"] == ""


def test_negative_equity_not_computed():
    d = dupont(pd.DataFrame([["2024-12-31", 100, 1000, 500, -50]], columns=COLS))
    assert math.isnan(d.iloc[0]["roe_pct"])
    assert "equity" in d.iloc[0]["note"]


def test_missing_input_flagged():
    d = dupont(pd.DataFrame([["2024-12-31", 100, None, 500, 250]], columns=COLS))
    assert math.isnan(d.iloc[0]["roe_pct"])
    assert "revenue" in d.iloc[0]["note"]


def test_attribution_adds_up():
    rows = [["2023-12-31", 100, 1000, 500, 250], ["2024-12-31", 132, 1100, 550, 250]]
    d = dupont(pd.DataFrame(rows, columns=COLS))
    r = d.iloc[1]
    assert math.isclose(r["chg_margin"] + r["chg_turnover"] + r["chg_leverage"], r["chg_roe"], rel_tol=1e-9)
    assert math.isclose(r["roe_pct"], 52.8)


def test_attribution_skipped_across_gap():
    rows = [["2021-12-31", 100, 1000, 500, 250], ["2024-12-31", 132, 1100, 550, 250]]
    d = dupont(pd.DataFrame(rows, columns=COLS))
    assert math.isnan(d.iloc[1]["chg_roe"])