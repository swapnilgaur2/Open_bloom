# Roadmap

## v1.0 (done)
- SEC client with caching, schema, resumable ingestion, SQL view, tested metrics
- S&P 500 universe with sectors; sector filter and TOP 20 / TOP 50 / ALL
- Terminal-style dashboard split into UI modules
- MODELS tab: DuPont ROE, cash conversion and accruals, restatement tracker
- Derived total liabilities, extra cash and revenue tags, gap diagnostics
- README and docs

## v1.1: data fixes (one re-ingest)
- Map the continuing-operations operating cash flow tag (fixes GEHC and likely similar companies)
- Bank revenue as net interest income plus non-interest income (SYF, TFC), clearly labelled as derived
- Diagnose APA revenue (probably custom tags) and DRI operating cash flow
- Mocked-SEC tests (annual filter, restatement rule) so the suite runs without network

## v2: analysis
1. **AI Capex Race**: capex, capex / revenue and backlog (remaining performance obligations) for MSFT, AMZN, GOOGL, META, ORCL. Needs one new tag and a note on capex definitions.
2. Peer benchmarking: percentile rank within sector (sector column already stored)
3. Piotroski F-score (9 pass/fail tests), Altman Z-score (not applicable to banks)
4. AI Mention Index: fixed keyword list counted in 10-Ks, labelled "disclosure intensity". Needs a new pipeline that downloads the filing documents. Start with about 50 companies.

## v3: terminal feel and new data
- Latest filings feed (SEC submissions API), command bar ("AAPL FA"), multi-panel home
- Daily prices from a free source (check terms), valuation multiples
- FRED macro panel, DCF sensitivity table (scenario tool, not a prediction)
- Filing change detector (plain-text diff of 10-K risk factors, no LLM)
- Insider trades (Form 4) and institutional holdings (13F)

## Later / optional
- Quarterly data and TTM (complex because Q4 is not reported separately)
- Relationship graph, AI value chain map, circular-money tracker (always labelled "disclosed", never "complete")
- LLM research assistant, only if grounded in stored evidence and citation-validated
- Foreign filers (20-F, IFRS) are out of scope for the current pipeline

## Skip
Real-time or intraday data (paid, licensing limits), news sentiment, backtested stock pickers (claims that cannot be defended), multi-agent systems.