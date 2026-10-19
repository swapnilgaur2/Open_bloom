import csv
import os
import re
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from src.openbloom.sec_client import get_ticker_map

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
OUTPUT = Path("data/companies.csv")

# Original 41 companies. Kept even if they ever drop out of the S&P 500.
ORIGINAL_TICKERS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA", "ORCL", "INTC", "NFLX",
    "JPM", "BAC", "GS", "V", "AXP", "BRK-B",
    "WMT", "COST", "KO", "PEP", "PG", "NKE", "MCD", "SBUX", "HD",
    "JNJ", "PFE", "UNH", "LLY", "MRK",
    "XOM", "CVX",
    "BA", "CAT", "F", "GE", "UPS",
    "VZ", "T", "DIS", "NEE",
]

# The SEC ticker file sometimes points to a successor holding company with no 10-K history.
CIK_OVERRIDES = {"XOM": ("0000034088", "Exxon Mobil Corp")}

# Companies with two share classes share one CIK (one 10-K). Keep one ticker per CIK.
PREFERRED_SHARE_CLASS = {"GOOGL", "FOXA", "NWSA"}


class _TableParser(HTMLParser):
    """Extracts the rows of the <table id="constituents"> on the Wikipedia page."""

    def __init__(self):
        super().__init__()
        self.in_target = False
        self.depth = 0
        self.rows = []
        self._row = None
        self._cell = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "table" and a.get("id") == "constituents":
            self.in_target = True
            self.depth = 1
            return
        if not self.in_target:
            return
        if tag == "table":
            self.depth += 1
        elif tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        if not self.in_target:
            return
        if tag == "table":
            self.depth -= 1
            if self.depth == 0:
                self.in_target = False
        elif tag in ("td", "th") and self._cell is not None:
            text = " ".join("".join(self._cell).split())
            self._row.append(re.sub(r"\[\w+\]", "", text))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def _fetch_sp500() -> list[dict]:
    ua = os.getenv("SEC_USER_AGENT", "OpenBloom/0.1 (personal project)")
    req = urllib.request.Request(WIKI_URL, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=30) as resp:
        page = resp.read().decode("utf-8")

    parser = _TableParser()
    parser.feed(page)
    if len(parser.rows) < 400:
        raise RuntimeError(f"Expected ~500 rows in the S&P 500 table, got {len(parser.rows)}. Page layout may have changed.")

    header = [h.lower() for h in parser.rows[0]]

    def col(prefix: str) -> int:
        for i, h in enumerate(header):
            if h.startswith(prefix):
                return i
        raise RuntimeError(f"Column '{prefix}' not found. Columns are: {parser.rows[0]}")

    i_sym, i_name, i_sec, i_sub, i_cik = col("symbol"), col("security"), col("gics sector"), col("gics sub"), col("cik")

    out = []
    for r in parser.rows[1:]:
        if len(r) <= max(i_sym, i_name, i_sec, i_sub, i_cik):
            continue
        digits = re.sub(r"\D", "", r[i_cik])
        if not digits:
            continue
        out.append(
            {
                "ticker": r[i_sym].replace(".", "-").upper(),
                "cik": digits.zfill(10),
                "name": r[i_name],
                "sector": r[i_sec],
                "sub_industry": r[i_sub],
            }
        )
    return out


def build_universe() -> None:
    sp = _fetch_sp500()

    by_cik, merged = {}, []
    for r in sp:
        if r["ticker"] in CIK_OVERRIDES:
            r["cik"], r["name"] = CIK_OVERRIDES[r["ticker"]]
        cur = by_cik.get(r["cik"])
        if cur is None:
            by_cik[r["cik"]] = r
        elif r["ticker"] in PREFERRED_SHARE_CLASS:
            merged.append(cur["ticker"])
            by_cik[r["cik"]] = r
        else:
            merged.append(r["ticker"])

    # Keep any of the original 41 that are not in the S&P 500 list (no sector).
    have = {r["ticker"] for r in by_cik.values()}
    extras, missing = [], []
    sec_map = get_ticker_map()
    by_ticker = {row["ticker"].upper(): row for row in sec_map.values()}
    for t in ORIGINAL_TICKERS:
        if t in have:
            continue
        if t in CIK_OVERRIDES:
            cik, name = CIK_OVERRIDES[t]
        elif t in by_ticker:
            cik, name = str(by_ticker[t]["cik_str"]).zfill(10), by_ticker[t]["title"]
        else:
            missing.append(t)
            continue
        if cik in by_cik:
            continue
        by_cik[cik] = {"ticker": t, "cik": cik, "name": name, "sector": "", "sub_industry": ""}
        extras.append(t)

    rows = sorted(by_cik.values(), key=lambda r: r["ticker"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["ticker", "cik", "name", "sector", "sub_industry"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {len(rows)} companies to {OUTPUT}")
    print(f"S&P 500 rows read: {len(sp)} | extra share classes merged: {merged}")
    if extras:
        print(f"Kept from original 41 (not in S&P list): {extras}")
    if missing:
        print(f"NOT FOUND: {missing}")
    sectors = {}
    for r in rows:
        sectors[r["sector"] or "(none)"] = sectors.get(r["sector"] or "(none)", 0) + 1
    for s, n in sorted(sectors.items(), key=lambda x: -x[1]):
        print(f"  {s}: {n}")


if __name__ == "__main__":
    build_universe()