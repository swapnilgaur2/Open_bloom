from src.openbloom.db import get_connection

CORE = ["revenue", "net_income", "equity", "total_assets", "operating_cash_flow", "cash"]


def main() -> None:
    marks = ",".join("?" for _ in CORE)
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT q.metric, c.ticker, COALESCE(c.sector, '-') "
            "FROM quality_issues q JOIN companies c ON c.cik = q.cik "
            f"WHERE q.issue_type = 'missing_metric' AND q.metric IN ({marks}) "
            "ORDER BY q.metric, c.ticker",
            CORE,
        ).fetchall()
    current = None
    for metric, ticker, sector in rows:
        if metric != current:
            print(f"\n{metric}:")
            current = metric
        print(f"  {ticker:6} {sector}")


if __name__ == "__main__":
    main()