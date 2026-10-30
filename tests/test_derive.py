import pandas as pd

from src.openbloom.metrics import METRICS, compute_metrics, derive_liabilities


def _df(**values):
    row = {m: None for m in METRICS}
    row.update(values)
    row["period_end"] = "2024-12-31"
    return pd.DataFrame([row])


def test_derive_when_missing():
    assert derive_liabilities(None, 500, 200) == (300, True)


def test_reported_value_not_overwritten():
    assert derive_liabilities(280, 500, 200) == (280, False)


def test_cannot_derive_without_inputs():
    assert derive_liabilities(None, None, 200) == (None, False)


def test_compute_metrics_uses_derived_liabilities():
    out = compute_metrics(_df(total_assets=500, equity=200))
    assert out.loc[0, "total_liabilities"] == 300
    assert bool(out.loc[0, "total_liabilities_derived"]) is True
    assert abs(out.loc[0, "liabilities_to_equity"] - 1.5) < 1e-9