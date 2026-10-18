from datetime import datetime, timezone

from src.openbloom.db import get_connection, init_db
from src.openbloom.sec_client import get_company_facts

ANNUAL_FORMS = ("10-K", "10-K/A")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _is_annual_duration(start: str, end: str) -> bool:
    days = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days
    return 350 <= days <= 380


def ingest_company(conn, cik: str) -> int:
    """Load annual facts for one company. Returns number of new facts stored."""
    run_id = conn.execute(
        "INSERT INTO ingestion_runs (cik, started_at, status) VALUES (?, ?, 'running')",
        (cik, _now()),
    ).lastrowid
    conn.commit()

    try:
        us_gaap = get_company_facts(cik).get("facts", {}).get("us-gaap", {})
        concepts = conn.execute(
            "SELECT DISTINCT tag, period_type FROM concept_map"
        ).fetchall()

        loaded = 0
        for tag, period_type in concepts:
            usd_facts = us_gaap.get(tag, {}).get("units", {}).get("USD", [])
            for f in usd_facts:
                if f.get("form") not in ANNUAL_FORMS:
                    continue
                start = f.get("start", "")
                if period_type == "duration":
                    if not start or not _is_annual_duration(start, f["end"]):
                        continue
                else:
                    start = ""
                cur = conn.execute(
                    "INSERT OR IGNORE INTO facts (cik, tag, unit, period_start, "
                    "period_end, value, accession, form, fiscal_year, fiscal_period, "
                    "filed_date, run_id) VALUES (?, ?, 'USD', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (cik, tag, start, f["end"], f["val"], f["accn"], f["form"],
                     f.get("fy"), f.get("fp"), f["filed"], run_id),
                )
                loaded += cur.rowcount

        # Quality check: metrics with no data at all for this company
        conn.execute(
            "DELETE FROM quality_issues WHERE cik = ? AND issue_type = 'missing_metric'",
            (cik,),
        )
        metrics = [r[0] for r in conn.execute("SELECT DISTINCT metric FROM concept_map")]
        for metric in metrics:
            n = conn.execute(
                "SELECT COUNT(*) FROM facts f JOIN concept_map c ON c.tag = f.tag "
                "WHERE f.cik = ? AND c.metric = ?",
                (cik, metric),
            ).fetchone()[0]
            if n == 0:
                conn.execute(
                    "INSERT INTO quality_issues (run_id, cik, metric, issue_type, "
                    "detail, detected_at) VALUES (?, ?, ?, 'missing_metric', ?, ?)",
                    (run_id, cik, metric, "No annual facts found for any mapped tag", _now()),
                )

        conn.execute(
            "UPDATE ingestion_runs SET finished_at = ?, status = 'success', "
            "facts_loaded = ? WHERE run_id = ?",
            (_now(), loaded, run_id),
        )
        conn.commit()
        return loaded

    except Exception as exc:
        conn.rollback()
        conn.execute(
            "UPDATE ingestion_runs SET finished_at = ?, status = 'failed', "
            "error = ? WHERE run_id = ?",
            (_now(), str(exc)[:500], run_id),
        )
        conn.commit()
        raise


def ingest_all() -> None:
    init_db()
    with get_connection() as conn:
        companies = conn.execute("SELECT cik, ticker FROM companies ORDER BY ticker").fetchall()
        for cik, ticker in companies:
            try:
                n = ingest_company(conn, cik)
                print(f"{ticker:6} OK      {n} new facts")
            except Exception as exc:
                print(f"{ticker:6} FAILED  {exc}")

        print("\nMissing metrics (companies with no data):")
        rows = conn.execute(
            "SELECT metric, COUNT(*) FROM quality_issues "
            "WHERE issue_type = 'missing_metric' GROUP BY metric ORDER BY 2 DESC"
        ).fetchall()
        for metric, count in rows:
            print(f"  {metric}: {count} companies")


if __name__ == "__main__":
    ingest_all()