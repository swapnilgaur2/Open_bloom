# Roadmap

Status: DONE, NEXT, LATER, SKIP.

## Done
- Environment, Git and GitHub, SEC client with caching
- Schema, ingestion (resumable), SQL view, tested metrics
- Terminal-style dashboard, UI split into modules
- S&P 500 universe with sectors, TOP 20 / TOP 50 / ALL
- DuPont ROE model in a MODELS tab
- Docs and README

## NEXT
1. **Fix metric gaps**: alternative revenue tags (financials), derive total liabilities (assets - equity), more operating income tags.
2. Cash conversion and accruals (operating cash flow / net income).
3. Piotroski F-score (9 pass/fail tests).
4. Altman Z-score (non-manufacturer variant; banks not applicable).
5. Peer benchmarking: percentile rank within sector.
6. Tests with mocked SEC responses; duplicate, unit and fiscal-year-label checks.
7. Release: screenshots, clean-setup test.

## LATER: features that make it unique
- Restatement tracker: where a reported number changed between filings.
- Filing change detector: plain-text diff of 10-K risk factors year over year (no LLM).
- Insider trades (Form 4) and institutional holdings (13F).

## LATER: terminal feel
- Command bar ("AAPL FA", "MSFT COMP"), multi-panel home, latest filings feed.
- Daily prices from a free source (check terms), valuation multiples.
- FRED macro panel and DCF sensitivity table (scenario tool, not a prediction).

## LATER: relationship and AI-space features
- Auditor, share count and buybacks; major-customer disclosures; relationship graph (always labelled "disclosed", never "complete").
- AI Mention Index (fixed keyword list, "disclosure intensity"), AI capex race, mention-to-spend gap, AI value chain map, circular-money tracker.
- Foreign filers (20-F, IFRS) are out of scope for the current pipeline.

## Optional
- Quarterly data and TTM (complex because Q4 is not reported separately).
- LLM research assistant, only if grounded in stored evidence and citation-validated.

## SKIP
Real-time or intraday data (paid, licensing limits), news sentiment, backtested stock pickers (claims that cannot be defended), multi-agent systems.