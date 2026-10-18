import csv
from pathlib import Path

from src.openbloom.sec_client import get_ticker_map

TICKERS = [
    # Tech
    "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA", "ORCL", "INTC", "NFLX",
    # Financials
    "JPM", "BAC", "GS", "V", "AXP", "BRK-B",
    # Consumer
    "WMT", "COST", "KO", "PEP", "PG", "NKE", "MCD", "SBUX", "HD",
    # Healthcare
    "JNJ", "PFE", "UNH", "LLY", "MRK",
    # Energy
    "XOM", "CVX",
    # Industrials
    "BA", "CAT", "F", "GE", "UPS",
    # Telecom, media, utilities
    "VZ", "T", "DIS", "NEE",
]

OUTPUT = Path("data/companies.csv")


def build_universe() -> None:
    sec_map = get_ticker_map()
    by_ticker = {row["ticker"].upper(): row for row in sec_map.values()}

    rows, missing = [], []
    for ticker in TICKERS:
        record = by_ticker.get(ticker)
        if record is None:
            missing.append(ticker)
            continue
        rows.append(
            {
                "ticker": ticker,
                "cik": str(record["cik_str"]).zfill(10),
                "name": record["title"],
            }
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ticker", "cik", "name"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} companies to {OUTPUT}")
    if missing:
        print(f"NOT FOUND in SEC file: {missing}")


if __name__ == "__main__":
    build_universe()