import math

import pandas as pd

from src.openbloom.models.cash_conversion import cash_conversion
from src.openbloom.models.restatements import find_restatements


def _cc(rows):
    return cash_conversion(pd.DataFrame(rows, columns=["period_end", "net_income", "operating_cash_flow", "total_assets"]))


def test_conversion_and_accruals_worked_example():
    d = _cc([["2023-12-31", 90, 100, 400], ["2024-12-31", 100, 120, 600]])
    r = d.iloc[1]
    assert math.isclose(r["cash_conversion"], 1.2)
    assert math.isclose(r["accruals_pct"], (100 - 120) / 500 * 100)  # -4.0%


def test_three_year_conversion():
    d = _cc([["2022-12-31", 100, 120, 500], ["2023-12-31", 110, 110, 500], ["2024-12-31", 120, 100, 500]])
    assert math.isclose(d.iloc[2]["conv_3y"], 1.0)


def test_negative_income_not_meaningful():
    d = _cc([["2024-12-31", -50, 20, 500]])
    assert math.isnan(d.iloc[0]["cash_conversion"])
    assert "net income" in d.iloc[0]["note"]


COLS = ["ticker", "cik", "metric", "tag", "period_start", "period_end", "value", "accession", "form", "filed_date"]


def _f(rows):
    return pd.DataFrame(rows, columns=COLS)


def _row(value, acc, filed):
    return ["AAA", "0000000001", "revenue", "Revenues", "2023-01-01", "2023-12-31", value, acc, "10-K", filed]


def test_restatement_detected():
    r = find_restatements(_f([_row(100, "a1", "2024-02-01"), _row(110, "a2", "2025-02-01")]))
    assert len(r) == 1
    assert math.isclose(r.iloc[0]["change_pct"], 10.0)
    assert r.iloc[0]["original_accession"] == "a1" and r.iloc[0]["latest_accession"] == "a2"


def test_same_value_repeated_is_not_a_restatement():
    assert find_restatements(_f([_row(100, "a1", "2024-02-01"), _row(100, "a2", "2025-02-01")])).empty


def test_three_filings_uses_first_and_last():
    r = find_restatements(_f([_row(100, "a1", "2024-02-01"), _row(100, "a2", "2025-02-01"), _row(120, "a3", "2026-02-01")]))
    assert len(r) == 1
    assert math.isclose(r.iloc[0]["change_pct"], 20.0)
    assert r.iloc[0]["versions"] == 2