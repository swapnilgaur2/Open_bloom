import csv
import sqlite3
from pathlib import Path

DB_PATH = Path("data/openbloom.db")
COMPANIES_CSV = Path("data/companies.csv")

SCHEMA = """
CREATE TABLE IF NOT EXISTS companies (
    cik    TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    name   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    cik          TEXT NOT NULL REFERENCES companies(cik),
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    status       TEXT NOT NULL,
    facts_loaded INTEGER,
    error        TEXT
);

CREATE TABLE IF NOT EXISTS concept_map (
    metric      TEXT NOT NULL,
    tag         TEXT NOT NULL,
    priority    INTEGER NOT NULL,
    period_type TEXT NOT NULL,
    PRIMARY KEY (metric, tag)
);

CREATE TABLE IF NOT EXISTS facts (
    fact_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    cik           TEXT NOT NULL REFERENCES companies(cik),
    tag           TEXT NOT NULL,
    unit          TEXT NOT NULL,
    period_start  TEXT NOT NULL DEFAULT '',
    period_end    TEXT NOT NULL,
    value         REAL NOT NULL,
    accession     TEXT NOT NULL,
    form          TEXT NOT NULL,
    fiscal_year   INTEGER,
    fiscal_period TEXT,
    filed_date    TEXT NOT NULL,
    run_id        INTEGER NOT NULL REFERENCES ingestion_runs(run_id),
    UNIQUE (cik, tag, unit, period_start, period_end, accession)
);

CREATE TABLE IF NOT EXISTS quality_issues (
    issue_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      INTEGER REFERENCES ingestion_runs(run_id),
    cik         TEXT NOT NULL,
    metric      TEXT,
    issue_type  TEXT NOT NULL,
    detail      TEXT,
    detected_at TEXT NOT NULL
);

CREATE VIEW IF NOT EXISTS annual_metrics AS
WITH ranked AS (
    SELECT
        f.cik, c.metric, f.period_end, f.value, f.tag,
        f.accession, f.form, f.filed_date,
        ROW_NUMBER() OVER (
            PARTITION BY f.cik, c.metric, f.period_end
            ORDER BY c.priority ASC, f.filed_date DESC
        ) AS rn
    FROM facts f
    JOIN concept_map c ON c.tag = f.tag
)
SELECT cik, metric, period_end, value, tag, accession, form, filed_date
FROM ranked
WHERE rn = 1;
"""

# (metric, tag, priority, period_type). Lower priority number = tried first.
CONCEPT_MAP = [
    ("revenue", "RevenueFromContractWithCustomerExcludingAssessedTax", 1, "duration"),
    ("revenue", "Revenues", 2, "duration"),
    ("revenue", "RevenueFromContractWithCustomerIncludingAssessedTax", 3, "duration"),
    ("revenue", "SalesRevenueNet", 4, "duration"),
    ("gross_profit", "GrossProfit", 1, "duration"),
    ("operating_income", "OperatingIncomeLoss", 1, "duration"),
    ("net_income", "NetIncomeLoss", 1, "duration"),
    ("net_income", "ProfitLoss", 2, "duration"),
    ("operating_cash_flow", "NetCashProvidedByUsedInOperatingActivities", 1, "duration"),
    ("capex", "PaymentsToAcquirePropertyPlantAndEquipment", 1, "duration"),
    ("capex", "PaymentsToAcquireProductiveAssets", 2, "duration"),
    ("total_assets", "Assets", 1, "instant"),
    ("total_liabilities", "Liabilities", 1, "instant"),
    ("equity", "StockholdersEquity", 1, "instant"),
    ("equity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", 2, "instant"),
    ("cash", "CashAndCashEquivalentsAtCarryingValue", 1, "instant"),
]


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT OR REPLACE INTO concept_map (metric, tag, priority, period_type) "
            "VALUES (?, ?, ?, ?)",
            CONCEPT_MAP,
        )
        with COMPANIES_CSV.open(encoding="utf-8") as f:
            rows = [(r["cik"], r["ticker"], r["name"]) for r in csv.DictReader(f)]
        conn.executemany(
            "INSERT OR REPLACE INTO companies (cik, ticker, name) VALUES (?, ?, ?)",
            rows,
        )


if __name__ == "__main__":
    init_db()
    with get_connection() as conn:
        for table in ["companies", "concept_map", "ingestion_runs", "facts", "quality_issues"]:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {count} rows")