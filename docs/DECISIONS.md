# Decisions

Short log of choices that shape the project. Newest at the bottom.

## 1. Annual 10-K data only
Quarterly data is harder: Q4 is not reported separately in a 10-K, so it must be derived. Annual-only keeps every number directly traceable to one filing. Quarterly and TTM are on the roadmap as a later, deliberate step.

## 2. Restatements: keep the latest filed value
If the same fiscal year appears in several filings, the most recently filed value wins (after tag priority). Restated numbers are the company's current best figure. All versions stay in `facts`, which is what the planned restatement tracker will use.

## 3. SEC company-facts API, no paid data
Free and official, and every fact carries its filing reference. Trade-off: coverage depends on XBRL tagging, so some companies and metrics are missing.

## 4. Deterministic calculations, no LLM in v1
Numbers must be reproducible and testable. A research assistant is a late, optional item, and only if grounded in stored evidence and citation-checked.

## 5. SQLite
One file, no server, enough for 500 companies of annual data. Easy to rebuild from SEC data.

## 6. The XOM CIK trap
The SEC ticker file points XOM to a holding company with no 10-K history. The correct filer is CIK `0000034088` (Exxon Mobil Corp). `CIK_OVERRIDES` in `universe.py` fixes it. Lesson: after any universe change, check the QUALITY tab for companies with no data at all.

## 7. Universe: current S&P 500
Built at runtime from the constituents table on Wikipedia (ticker, CIK, GICS sector). Companies with several share classes share one CIK and one 10-K, so one ticker is kept per CIK (GOOGL, FOXA, NWSA preferred). The original 41 companies are kept even if they leave the index.
Trade-offs: scraping a web page can break if its layout changes (the code fails loudly if fewer than 400 rows are found), and the list is current membership, not historical.

## 8. TOP 20 / TOP 50 ranked by revenue, not market cap
There is no price data yet, so market cap is not possible. Ranking uses latest annual revenue. Companies with no revenue stored, or whose latest revenue is more than about 15 months older than the newest filing, are left out of the TOP views but remain in ALL.

## 9. DuPont uses year-end balances
So the three factors multiply to exactly the stored ROE. Average-balance versions are a possible later option, but would no longer reconcile to the ROE shown elsewhere.

## 10. UI split into modules
`app.py` only wires tabs. Formatting, charts, tables, data access and model views live in `src/openbloom/ui/`. Reason: small, safe edits.

## 11. Models live in their own tab
The MODELS tab keeps raw data views (SNAPSHOT, FINANCIALS) separate from analysis, and gives each new model a clear place.