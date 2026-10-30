# Decisions

Short log of choices that shape the project. Newest at the bottom.

## 1. Annual 10-K data only
Quarterly data is harder: Q4 is not reported separately in a 10-K, so it must be derived. Annual-only keeps every number directly traceable to one filing. Quarterly and TTM are on the roadmap as a later, deliberate step.

## 2. Restatements: keep the latest filed value
If the same fiscal year appears in several filings, the most recently filed value wins (after tag priority). Restated numbers are the company's current best figure. All versions stay in `facts`, which the restatement tracker uses.

## 3. SEC company-facts API, no paid data
Free and official, and every fact carries its filing reference. Trade-off: coverage depends on XBRL tagging, so some companies and metrics are missing.

## 4. Deterministic calculations, no LLM in v1
Numbers must be reproducible and testable. A research assistant is a late, optional item, and only if grounded in stored evidence and citation-checked.

## 5. SQLite
One file, no server, enough for about 500 companies of annual data. Easy to rebuild from SEC data.

## 6. The XOM CIK trap
The SEC ticker file points XOM to a holding company with no 10-K history. The correct filer is CIK `0000034088` (Exxon Mobil Corp). `CIK_OVERRIDES` in `universe.py` fixes it. Lesson: after any universe change, check the QUALITY tab and `python -m src.openbloom.gaps` for companies with no data at all.

## 7. Universe: current S&P 500
Built at runtime from the constituents table on Wikipedia (ticker, CIK, GICS sector). Companies with several share classes share one CIK and one 10-K, so one ticker is kept per CIK (GOOGL, FOXA, NWSA preferred). The original 41 companies are kept even if they leave the index.
Trade-offs: scraping a web page can break if its layout changes (the code fails loudly if fewer than 400 rows are found), and the list is current membership, not historical.

## 8. TOP 20 / TOP 50 ranked by revenue, not market cap
There is no price data yet, so market cap is not possible. Ranking uses latest annual revenue. Companies with no revenue stored, or whose latest revenue is more than about 15 months older than the newest filing, are left out of the TOP views but remain in ALL.

## 9. DuPont uses year-end balances
So the three factors multiply to exactly the stored ROE. Average-balance versions would no longer reconcile to the ROE shown elsewhere. (The accruals ratio in the cash conversion model uses average assets, as the standard definition does, and says so.)

## 10. UI split into modules
`app.py` only wires tabs. Formatting, charts, tables, data access and model views live in `src/openbloom/ui/`. Reason: small, safe edits.

## 11. Models live in their own tab
The MODELS tab keeps raw data views (SNAPSHOT, FINANCIALS) separate from analysis, and gives each new model a clear place.

## 12. Total liabilities: derive, and say so
About 130 companies do not tag total liabilities. It is derived as total assets minus equity and marked `*`. It also includes non-controlling or redeemable interests, which is stated in the footnote. The QUALITY coverage matrix still shows these as missing, because it measures reported data only.

## 13. No relabelling to fill gaps
Gross profit is not derived from cost of revenue (misleading for airlines, utilities and similar). Pre-tax income is not used as operating income. Interest income is not used as bank revenue. A "—" is more honest than a number that means something else.

## 14. Companies with no annual data are hidden
New filers with no 10-K yet (for example HONA, VYLR in this build) have nothing to show, so the app lists only companies with at least one stored annual value. They reappear automatically after a later ingest once a 10-K exists.

## 15. Restatement tracker scope
Compares the first and last filed value for the same company, metric, tag and period, only for the tag the app uses. Repeated identical values are ignored. Changes are labelled as changes, not errors, because many are reclassifications or discontinued-operations recasts.

## 16. v1.0 ships with documented gaps
Remaining gaps (revenue for APA, SYF, TFC; operating cash flow for DRI, GEHC) are listed in the README and roadmap. GEHC reports operating cash flow under a continuing-operations tag that is not mapped yet; fixing it needs a full `--refresh` for one company, so it waits for v1.1 together with other tag fixes.