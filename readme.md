# OpenBloom

A limited, open-source, Bloomberg-terminal-style fundamentals workbench for the S&P 500, built on free SEC EDGAR data.

**Principles**
- Every number traces to a source SEC filing (accession number, XBRL tag, period).
- Every calculation is deterministic, tested code. There is no LLM in v1.
- Missing or not-applicable data is shown as "—", never guessed.

![Snapshot](docs/img/snapshot.png)

## What it does (v1.0)

- Annual 10-K fundamentals for about 498 S&P 500 companies (those with at least one filed 10-K), 10 metrics each.
- Dashboard tabs: **SNAPSHOT**, **FINANCIALS**, **MODELS**, **COMPARE**, **QUALITY**, **SOURCE**.
- Universe controls: sector filter, TOP 20 / TOP 50 / ALL (ranked by latest annual revenue), searchable dropdown.
- **MODELS tab**
  - **DuPont ROE**: net margin x asset turnover x equity multiplier, plus a year-over-year attribution of what moved ROE.
  - **Cash conversion**: operating cash flow / net income, 3-year conversion and the accruals ratio.
  - **Restatement tracker**: reported values that changed between filings, for one company or across all, with links to the SEC filing.
- **QUALITY tab**: ingestion runs and a coverage matrix (company x metric).
- **SOURCE tab**: the filing, tag and period behind every stored value, with a link to the SEC filing folder.

![Models](docs/img/models.png)
![Restatements](docs/img/restatements.png)
![Quality](docs/img/quality.png)

## Not in v1

Quarterly data, TTM figures, stock prices, valuation multiples, news, real-time data. See `docs/ROADMAP.md`.

## Quick start (Windows, PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file in the project root. The SEC requires a descriptive User-Agent:

```
SEC_USER_AGENT="Your Name your.email@example.com"
```

Build the data, then run the app:

```powershell
python -m src.openbloom.universe     # builds data/companies.csv (S&P 500 list)
python -m src.openbloom.ingest       # downloads SEC filings into SQLite (resumable)
python -m pytest -q                  # run tests
python -m streamlit run app.py       # open the dashboard
```

`ingest` skips companies that already loaded; use `--refresh` to reload everything (needed after changing the concept map). The first full run downloads about 500 SEC files and takes a while. Raw files are cached in `data/raw/` for 24 hours (git-ignored, like the database).

Helper scripts:
- `python -m src.openbloom.gaps` lists companies still missing core metrics.
- `python -m src.openbloom.inspect_company TICKER -k keyword` shows which XBRL tags a company actually reports.

## Project layout

```
app.py                         Streamlit entry point (tabs and wiring only)
src/openbloom/
  sec_client.py                SEC EDGAR client: rate limit, disk cache
  universe.py                  builds data/companies.csv
  db.py                        SQLite schema, concept map, annual_metrics view
  ingest.py                    SEC facts -> SQLite, quality flags
  metrics.py                   metric functions (growth, margins, ROE, derived liabilities)
  models/                      dupont.py, cash_conversion.py, restatements.py (pure functions)
  ui/                          theme, formatting, charts, tables, data access, model views
  gaps.py, inspect_company.py  data-gap diagnostics
tests/                         pytest suite
docs/                          architecture, data model, metrics, decisions, roadmap
```

## Data and limitations

- Source: SEC EDGAR company-facts API (free). Annual 10-K and 10-K/A filings only, `us-gaap` tags only.
- Banks, insurers and REITs report differently, so some metrics are missing for them (see the QUALITY tab). Gross profit is missing for most companies because most do not report it.
- Total liabilities is derived as total assets minus equity when a company does not report it (marked `*`).
- Restated values: the most recently filed value wins. A restatement is not necessarily an error; many are reclassifications.
- The S&P 500 list is today's membership, not point-in-time. Fine for current fundamentals, wrong for historical backtests.
- Known remaining gaps: revenue for APA, SYF, TFC; operating cash flow for DRI and GEHC. New listings with no 10-K yet (for example HONA, VYLR) are hidden.
- Metrics like ROE can be distorted (for example by buybacks). Models flag where they do not apply.

## Disclaimer

Educational project. Not investment advice. Data comes as-is from public SEC filings and may contain errors or gaps.

## Docs

[Architecture](docs/ARCHITECTURE.md) · [Data model](docs/DATA_MODEL.md) · [Metrics](docs/METRICS.md) · [Decisions](docs/DECISIONS.md) · [Roadmap](docs/ROADMAP.md)