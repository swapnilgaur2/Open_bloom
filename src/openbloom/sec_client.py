import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path("data/raw")
MIN_INTERVAL_SECONDS = 0.2  # max 5 requests/sec (SEC allows 10)
CACHE_MAX_AGE_HOURS = 24
_last_request_time = 0.0


def _normalize_cik(cik) -> str:
    cik = str(cik).strip()
    if not cik.isdigit() or len(cik) > 10:
        raise ValueError(f"Invalid CIK: {cik!r}")
    return cik.zfill(10)


def get_company_facts(cik) -> dict:
    """Return SEC company facts for a CIK, using a 24h disk cache."""
    global _last_request_time
    cik = _normalize_cik(cik)
    cache_file = CACHE_DIR / f"companyfacts_{cik}.json"

    if cache_file.exists():
        age_hours = (time.time() - cache_file.stat().st_mtime) / 3600
        if age_hours < CACHE_MAX_AGE_HOURS:
            return json.loads(cache_file.read_text(encoding="utf-8"))

    user_agent = os.getenv("SEC_USER_AGENT")
    if not user_agent:
        raise RuntimeError("SEC_USER_AGENT is missing from .env")

    wait = MIN_INTERVAL_SECONDS - (time.time() - _last_request_time)
    if wait > 0:
        time.sleep(wait)

    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    response = requests.get(url, headers={"User-Agent": user_agent}, timeout=30)
    _last_request_time = time.time()
    response.raise_for_status()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(response.text, encoding="utf-8")
    return response.json()