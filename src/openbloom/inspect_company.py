"""Usage: python -m src.openbloom.inspect_company TICKER [TICKER ...] [-k word1,word2]
Shows what a company actually reports: taxonomies, forms, and tags (optionally filtered by keyword)."""
import sys

from src.openbloom.db import get_connection
from src.openbloom.sec_client import get_company_facts

ANNUAL = ("10-K", "10-K/A")


def main(argv) -> None:
    keywords = []
    if "-k" in argv:
        i = argv.index("-k")
        keywords = [k.lower() for k in argv[i + 1].split(",")]
        argv = argv[:i]
    with get_connection() as conn:
        for t in argv:
            row = conn.execute("SELECT cik, name FROM companies WHERE ticker = ?", (t,)).fetchone()
            if row is None:
                print(f"\n{t}: not in companies table")
                continue
            cik, name = row
            print(f"\n=== {t} | {name} | CIK {cik}")
            try:
                facts = get_company_facts(cik).get("facts", {})
            except Exception as exc:
                print(f"  could not load facts: {exc}")
                continue
            gaap = facts.get("us-gaap", {})
            forms = {
                f.get("form")
                for body in gaap.values()
                for unit in body.get("units", {}).values()
                for f in unit
            }
            print(f"  taxonomies: {list(facts.keys())} | us-gaap tags: {len(gaap)}")
            print(f"  forms seen: {sorted(x for x in forms if x)[:10]}")
            for tag, body in sorted(gaap.items()):
                if keywords and not any(k in tag.lower() for k in keywords):
                    continue
                if not keywords:
                    continue
                usd = body.get("units", {}).get("USD", [])
                annual = [f for f in usd if f.get("form") in ANNUAL]
                if annual:
                    print(f"  {tag:75} {len(annual):3} annual facts, latest {max(f['end'] for f in annual)}")


if __name__ == "__main__":
    main(sys.argv[1:])