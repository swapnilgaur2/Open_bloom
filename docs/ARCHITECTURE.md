# Architecture

## Data flow

```
SEC EDGAR company-facts API
        |   (rate-limited 5 req/s, 24h disk cache in data/raw/)
        v
   sec_client.py
        |
        v
   ingest.py  --- annual filter (10-K / 10-K/A, 350-380 day durations) --->  SQLite (data/openbloom.db)
        |                                                                      facts, companies,
        |                                                                      ingestion_runs, quality_issues
        v                                                                      concept_map
   quality_issues                                                              |
                                                                               v
                                                                  view: annual_metrics
                                                                  (one row per company, metric, year-end)
                                                                               |
                                                                               v
                                                      metrics.py  (compute_metrics)  -->  models/ (DuPont, ...)
                                                                               |
                                                                               v
                                                              ui/ (data, charts, tables, model_views)
                                                                               |
                                                                               v
                                                                  app.py (Streamlit tabs)
```

## Layers and responsibilities

| Layer | Files | Rule |
|---|---|---|
| Acquisition | `sec_client.py`, `universe.py` | Network access lives here only (plus the S&P list fetch in `universe.py`). Respect SEC rate limits and User-Agent. |
| Storage | `db.py`, `ingest.py` | SQLite. Raw facts are stored with their filing reference. Nothing is calculated here. |
| Calculation | `metrics.py`, `models/` | Pure functions on DataFrames. No Streamlit, no database calls inside model functions. Tested. |
| Presentation | `ui/`, `app.py` | Formatting and layout only. No business logic. |

## Why this shape

- **Traceability:** each stored fact keeps accession number, form, tag and filing date, so the SOURCE tab can link any number back to a filing.
- **Testability:** models are pure functions, so they can be tested against hand-worked examples without a database or UI.
- **Small edits:** the UI is split into modules so changes touch one small file.

## Adding a new model

1. Add `src/openbloom/models/<name>.py` with a pure function that takes a metrics DataFrame and returns a DataFrame, including a `note` column saying why a row was not computable.
2. Add tests in `tests/test_<name>.py` against a hand-worked example.
3. Add a render function in `ui/model_views.py` that shows every input.
4. Add the model to the MODELS tab radio in `app.py`.
5. Document the formula and applicability in `docs/METRICS.md`.