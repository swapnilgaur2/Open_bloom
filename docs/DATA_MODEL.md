# Data model

Database: SQLite, `data/openbloom.db` (git-ignored, rebuilt by `universe` + `ingest`).

## Tables

**companies**: one row per filer (primary key `cik`).
`cik`, `ticker`, `name`, `sector`, `sub_industry`. Sector and sub-industry are GICS labels from the S&P 500 list; empty for companies kept from the original 41 that are not in the index.

**ingestion_runs**: one row per ingestion attempt.
`run_id`, `cik`, `started_at`, `finished_at`, `status` (`running` / `success` / `failed`), `facts_loaded`, `error`.

**concept_map**: which XBRL tags feed which metric.
`metric`, `tag`, `priority` (lower = tried first), `period_type` (`duration` or `instant`).

**facts**: raw annual facts, in USD.
`cik`, `tag`, `unit`, `period_start`, `period_end`, `value`, `accession`, `form`, `fiscal_year`, `fiscal_period`, `filed_date`, `run_id`.
Unique on (`cik`, `tag`, `unit`, `period_start`, `period_end`, `accession`), so the same filing is never stored twice, but a restated value from a later filing is kept as its own row.

**quality_issues**: data problems found during ingestion.
`cik`, `metric`, `issue_type` (currently `missing_metric`), `detail`, `detected_at`.

## View: annual_metrics

One row per company, metric and fiscal year-end.
Columns: `cik`, `metric`, `period_end`, `value`, `tag`, `accession`, `form`, `filed_date`.

Selection rule, in order:
1. Highest-priority tag (lowest `priority` number in `concept_map`).
2. Most recently filed value (so restatements win).

## What gets stored

- Forms: `10-K` and `10-K/A` only.
- Flow items (revenue, income, cash flow, capex): durations of 350 to 380 days.
- Balance-sheet items (assets, liabilities, equity, cash): point-in-time values at fiscal year-end.
- Currency: USD only. Facts reported in other units are not loaded.

## Metrics (10)

`revenue`, `gross_profit`, `operating_income`, `net_income`, `operating_cash_flow`, `capex`, `total_assets`, `total_liabilities`, `equity`, `cash`.

Tag mapping lives in `CONCEPT_MAP` in `src/openbloom/db.py`.

## Known gaps

- Banks and insurers lack operating income, capex and often a standard revenue tag.
- Gross profit is missing for most companies (many do not report it).
- Some companies do not report total liabilities directly.
- Only `us-gaap` taxonomy facts are read. Companies using other taxonomies would show as missing.