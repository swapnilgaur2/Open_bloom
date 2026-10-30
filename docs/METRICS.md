# Metrics

All ratios are computed in `src/openbloom/metrics.py` from `annual_metrics`. A value is "—" when an input is missing or the ratio is not meaningful.

## Base metrics (from filings)

Revenue, gross profit, operating income, net income, operating cash flow, capex (cash paid for property and equipment), total assets, total liabilities, equity, cash.

**Total liabilities** is the reported value when available. Otherwise it is derived as total assets minus equity and marked `*` in the FINANCIALS tab. The derived figure also includes any non-controlling or redeemable interests, so it can be slightly higher than a reported total.

## Derived metrics

| Metric | Formula | Notes |
|---|---|---|
| Free cash flow | operating cash flow - capex | Not available when capex is missing (banks) |
| Revenue growth, YoY | (revenue - previous year revenue) / previous year revenue x 100 | Only if the previous row is about one year earlier and its revenue is positive |
| Gross margin | gross profit / revenue x 100 | |
| Operating margin | operating income / revenue x 100 | |
| Net margin | net income / revenue x 100 | |
| FCF margin | free cash flow / revenue x 100 | |
| ROE | net income / equity x 100 | Uses year-end equity. Distorted when equity is small (buybacks) or negative |
| Liabilities / equity | total liabilities / equity | Uses derived liabilities when needed |

Verified by hand against Apple FY2025: revenue growth 6.43%, operating margin 31.97%.

## Models

### DuPont ROE decomposition

ROE = net margin x asset turnover x equity multiplier

- Net margin = net income / revenue (profitability)
- Asset turnover = revenue / total assets (efficiency)
- Equity multiplier = total assets / equity (leverage)

Uses **year-end** balances (not averages), so the product equals the stored ROE exactly.

Year-over-year attribution: the change in ROE is split into log-percent contributions from margin, turnover and leverage, which add up exactly to the log-percent change in ROE. Shown only when both years are valid, net income is positive in both, and the years are about one year apart.

**Does not apply when:** an input is missing, revenue <= 0, total assets <= 0, or equity <= 0.

**Interpret with care:** banks and insurers run on leverage by design, so compare them within financials only. A rising ROE driven by leverage (often buybacks) is lower quality than one driven by margin.

Tests: `tests/test_dupont.py` (worked example: net income 100, revenue 1000, assets 500, equity 250 gives margin 10%, turnover 2.0, multiplier 2.0, ROE 40%).

### Cash conversion and accruals

- Cash conversion = operating cash flow / net income, only when net income > 0.
- 3-year conversion = sum of 3 years of operating cash flow / sum of 3 years of net income (smooths timing noise). Needs three consecutive years and a positive 3-year net income total.
- Accruals ratio = (net income - operating cash flow) / average total assets x 100, using this and last year's total assets. Higher means more of the profit is not backed by cash.

**Interpret with care:** conversion above 1.0x means profit is backed by cash; persistently below 1.0x is a quality warning, not proof of a problem. Banks and insurers include loan and deposit flows in operating cash flow, so the numbers are not comparable to other sectors.

Tests: `tests/test_cash_and_restatements.py`.

### Restatement tracker

Finds reported values that changed between filings. For each company, metric, tag and period, if more than one distinct value was filed, it shows the first filed value, the latest filed value, the change in percent, the number of distinct versions and a link to the latest filing.

- A later 10-K repeating the same number is not a change.
- Only the tag the app actually uses for a metric is compared.
- A change is not necessarily an error: many are reclassifications or recasts for discontinued operations.

Tests: `tests/test_cash_and_restatements.py`.

## Planned models

See `docs/ROADMAP.md`. Rule for every model: test against a published or hand-worked example, show every input, and flag where the model does not apply (banks, losses).