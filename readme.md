# OpenBloom

A limited, open-source, Bloomberg-terminal-style fundamentals dashboard built on free SEC EDGAR data.

**Principles**
- Every number traces to a source SEC filing (accession number, XBRL tag, period).
- Every calculation is deterministic, tested code. There is no LLM in v1.
- Missing or not-applicable data is shown as "—", never guessed.

> Screenshots: _add after the next release (SNAPSHOT, MODELS, QUALITY tabs)._

## What it does today

- Annual 10-K fundamentals for the S&P 500 (about 500 companies, one ticker per filer).
- Dashboard with 6 tabs: **SNAPSHOT**, **FINANCIALS**, **MODELS**, **COMPARE**, **QUALITY**, **SOURCE**.
- Universe controls: sector filter, TOP 20 / TOP 50 / ALL (ranked by latest annual revenue), searchable company dropdown.
- **DuPont ROE model**: net margin x asset turnover x equity multiplier, with a year-over-year attribution of what moved ROE.
- **QUALITY** tab: ingestion runs, a coverage matrix (company x metric), flagged missing data.
- **SOURCE** tab: the filing, tag and period behind every stored value, with a link to the SEC filing folder.

## Not in scope (yet)

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

`ingest` skips companies that already loaded; use `--refresh` to reload everything. The first full run downloads about 500 SEC files and takes a while. Raw files are cached in `data/raw/` for 24 hours (git-ignored, like the database).

## Project layout

```
app.py                         Streamlit entry point (tabs and wiring only)
src/openbloom/
  sec_client.py                SEC EDGAR client: rate limit, disk cache
  universe.py                  builds data/companies.csv
  db.py                        SQLite schema, concept map, annual_metrics view
  ingest.py                    SEC facts -> SQLite, quality flags
  metrics.py                   metric functions (growth, margins, ROE, ...)
  models/dupont.py             DuPont model (pure functions)
  ui/                          theme, formatting, charts, tables, data access, model views
tests/                         pytest suite
docs/                          architecture, data model, metrics, decisions, roadmap
```

## Data and limitations

- Source: SEC EDGAR company-facts API (free). Annual 10-K and 10-K/A filings only.
- Companies are mapped by XBRL tags. Banks, insurers and REITs report differently, so some metrics are missing for them (see the QUALITY tab and `docs/METRICS.md`).
- Restated values: the most recently filed value wins (see `docs/DECISIONS.md`).
- The S&P 500 list is today's membership, not point-in-time. Fine for current fundamentals, wrong for historical backtests.
- Metrics like ROE can be distorted (for example by large buybacks shrinking equity). Models flag where they do not apply.

## Disclaimer

Educational project. Not investment advice. Data is provided as-is from public SEC filings and may contain errors or gaps.

## Docs

[Architecture](docs/ARCHITECTURE.md) · [Data model](docs/DATA_MODEL.md) · [Metrics](docs/METRICS.md) · [Decisions](docs/DECISIONS.md) · [Roadmap](docs/ROADMAP.md)